import time
import logging

from copy import copy
from idlelib.configdialog import font_sample_text

from PyQt6.QtCore import QThreadPool, Qt
from PyQt6.QtWidgets import QWidget, QTableWidgetItem
from matplotlib import pyplot as plt

from EVA.util.path_handler import get_path
from EVA.util.worker import Worker

logger = logging.getLogger(__name__)

from EVA.core.app import get_config, get_app


class G4blPresenter(QWidget):
    def __init__(self, view, model, parent=None):
        super().__init__(parent)
        self.view = view
        self.model = model

        self.view.sample_name_linedit.setText("Sample")
        self.view.momentum_linedit.setText(str(self.model.momentum[0]))
        self.view.momentum_spread_linedit.setText(str(self.model.momentum_spread))
        self.view.min_momentum_linedit.setText(str(self.model.min_momentum))
        self.view.max_momentum_linedit.setText(str(self.model.max_momentum))
        self.view.momentum_step_linedit.setText(str(self.model.step_momentum))
        self.view.g4bl_exe_dir_linedit.setText(str(self.model.g4bl_exe_dir))
        self.view.g4bl_out_dir_linedit.setText(str(self.model.g4bl_out_dir))
        self.view.stats_linedit.setText(str(self.model.stats))
        self.view.bin_number_linedit.setText(str(self.model.bin_resolution))
        self.view.visualisation_checkbox.hide() #disable for now.
        # set momentum scam params to only be visible if momentum scan is selected
        self.on_scan_type_changed(self.view.scan_momentum_combo.currentText())
        self.view.scan_momentum_combo.currentTextChanged.connect(self.on_scan_type_changed)

        # set momentum bite param to only be visible is momentum spread simulation is selected
        self.on_sim_type_changed(self.view.sim_type_combo.currentText())
        self.view.sim_type_combo.currentTextChanged.connect(self.on_sim_type_changed)

        # Connect layer option checkboxes, set default layer method to simple stack and hide custom place_sample sample table
        self.view.mode_group.buttonToggled.connect(self.on_mode_changed)
        self.view.stack_layer_radio.setChecked(True)

        # add an empty row to the end of the layer table after every time the contents are updated
        self.view.stack_layer_setup_table.contents_updated_s.connect(self.view.stack_layer_setup_table.append_row)
        self.view.stack_layer_setup_table.cellClicked.connect(self.append_row_in_stack_layer_table_if_last_row_clicked)
        
        # check if user added sample, verify is sample provided is in the NIST database, request density if not #TODO need to actually be able to use this density 
        self.view.stack_layer_setup_table.user_edited_cell_s.connect(self.on_user_edited_cell)

        self.view.stack_layer_setup_table.set_column_completer(0, lambda: self.model.g4bl_materials)
        self.view.stack_layer_setup_table.update_contents(self.format_model_layers(), round_to=4)

        self.view.place_sample_implantation_collapse_checkbox.checkStateChanged.connect(self.view.collapse_expand_implantation)
        self.view.stack_implantation_collapse_checkbox.checkStateChanged.connect(lambda state: self.collapse_expand_tree(self.view.stack_results_tree, state))
        self.view.place_sample_implantation_collapse_checkbox.checkStateChanged.connect(lambda state: self.collapse_expand_tree(self.view.place_sample_results_tree, state))
        self.view.run_sim_button.clicked.connect(self.start_sim)
        self.view.cancel_sim_button.clicked.connect(self.cancel_sim)
        self.view.stopping_shift_plot_origin_s.connect(self.stopping_shift_plot_origin)
        self.view.stopping_reset_plot_origin_s.connect(self.stopping_reset_plot_origin)

        self.view.depth_shift_plot_origin_s.connect(self.depth_shift_plot_origin)
        self.view.depth_reset_plot_origin_s.connect(self.depth_reset_plot_origin)

        self.view.stack_save_all_sims_button.clicked.connect(self.on_save_sim_result)
        self.view.stack_save_all_imgs_button.clicked.connect(self.on_save_all_sim_plot)
        self.view.show_plot_s.connect(self.show_plot)
        self.view.momentum_slider.valueChanged.connect(self.on_slider_moved)

        self.view.load_settings_btn.clicked.connect(self.load_settings)
        self.view.save_settings_btn.clicked.connect(self.save_settings)

        # set up simulation worker to run simulation on separate thread
        self.simulation_worker = None

        self.time_last_swapped = time.time_ns()

        self.view.window_closed_s.connect(self.close_figures)

    def close_figures(self):
        for plot_stack in self.view.plot_stacks:
            self.model.close_figure(plot_stack.widget(0).canvas.figure)
            self.model.close_figure(plot_stack.widget(1).canvas.figure)


    def on_scan_type_changed(self, scan_type: str):
        """
        Shows the min, max and momentum step part of the form if scan type is "Yes", hides if scan type is "No".
        Is called every time scan type is updated

        Args:
            scan_type: whether form should be visible or not

        """
        visibility = scan_type == "Yes"

        self.view.min_momentum_linedit.setVisible(visibility)
        self.view.min_momentum_label.setVisible(visibility)
        self.view.max_momentum_linedit.setVisible(visibility)
        self.view.max_momentum_label.setVisible(visibility)
        self.view.momentum_step_linedit.setVisible(visibility)
        self.view.momentum_step_label.setVisible(visibility)

    def on_sim_type_changed(self, sim_type: str):
        """
        Is called every time simulation type is selected to toggle the visibility of the momentum bite part of the form

        Args:
            sim_type: "Mono" or "Momentum Spread"
        """

        visibility = sim_type == "Momentum Spread"

        self.view.momentum_spread_label.setVisible(visibility)
        self.view.momentum_spread_linedit.setVisible(visibility)

    def append_row_in_stack_layer_table_if_last_row_clicked(self, row):
        if row == (self.view.stack_layer_setup_table.rowCount()-1):
            self.view.stack_layer_setup_table.append_row()

    def on_mode_changed(self, button, checked):
        if not checked:   # ignore the button that was turned off
            return

        if button is self.view.stack_layer_radio:
            self.view.placement_tabWidget.hide()
            self.view.stack_tabWidget.show()
            self.model.sim_method = "Stack"
            self.current_table = self.view.stack_results_table
            self.current_tree = self.view.stack_results_tree

        elif button is self.view.manual_placement_radio:
            self.view.stack_tabWidget.hide()
            self.view.placement_tabWidget.show()
            self.model.sim_method = "Manual Placement"
            self.current_table = self.view.placement_results_table
            self.current_tree = self.view.placement_results_tree


    def format_model_layers(self, layers: list | None = None) -> list[list[str | float]]:
        """
        Formats the layers in G4blModel to a format compatible with the BaseTable's update_contents() method.

        Returns:
            Formatted array containing the layer data in G4blModel.
        """
        if layers is None:
            layers = self.model.stack_input

        return [[layer["name"], layer["thickness"], layer.get("density", " ")] for layer in layers]

    def get_layers_from_stack_table(self) -> list[dict] | None:
        """
        Gets layers from table and restructures them to fit the format required by TrimFitModel

        Returns: Restructured layers
        """
        layers = self.view.stack_layer_setup_table.get_contents()
        structured_layers = []

        for layer in layers:
            if layer[0] == "" or layer[1] == "":
                # skip rows where sample name is blank - assume the whole row is empty
                continue

            name = layer[0]
            try:
                thickness = float(layer[1])
            except ValueError:
                raise ValueError

            layer_dict = {"name": name, "thickness": thickness}

            if layer_dict["thickness"] <= 0:
                raise ValueError

            # layer density is allowed to be empty for 'Beamline Window' and 'Air (compressed)'
            #TODO have eva check if material exists in g4bl database, if yes then skip density requirement
            try:
                if layer[2] != "":
                    layer_dict["density"] = float(layer[2])
                else:
                    layer_dict["density"] = 0.0
            except ValueError:
                raise ValueError
            
            structured_layers.append(layer_dict)
        return structured_layers

    def start_sim(self):
        try:
            # get form data from view
            form_data = self.view.get_form_data()
        except (ValueError, AttributeError) as e:
            self.view.display_error_message(message="Invalid form input!")
            return

        # check that form contains valid g4bl settings
        valid, error = self.validate_g4bl_settings(form_data)

        if not valid:
            self.view.display_error_message(message=error)
            return
        try:
            if self.model.sim_method=="Stack": 
                self.model.stack_input = self.get_layers_from_stack_table()

        except (ValueError, AttributeError, KeyError) as e:
            self.view.display_error_message(message="Invalid layers specified. All layers must have a thickness, and all undefined layers "
                                                    "must have a density specified. "
                                                    "Ensure all values are greater than 0.")
            raise e
        # check if g4bl exe and output path is valid
        g4bldir_valid = self.model.is_valid_path(form_data["g4bl_dir"])
        outputdir_valid = self.model.is_valid_path(form_data["output_dir"])

        if not g4bldir_valid or not outputdir_valid:
            self.view.display_error_message(message="Could not find g4bl.exe at specified location. "
                                     "Please ensure you have G4BL installed.")
            return

        if form_data["sim_type"] == "Momentum Spread" and form_data["stats"] < 500:
            self.view.display_error_message(message="Momentum spread simulation requires a minimum of 500 muons.")
            return
        # if everything is ok, send data to model and simulate
        try:
            self.model.min_momentum = form_data["min_momentum"]
            self.model.max_momentum = form_data["max_momentum"]
            self.model.step_momentum = form_data["step_momentum"]
            self.model.momentum_spread = form_data["momentum_spread"]
            self.model.sample_name = form_data["sample_name"]
            self.model.stats = form_data["stats"]
            self.model.bin_resolution = form_data["bin_number"]
            self.model.g4bl_exe_dir = form_data["g4bl_dir"]
            self.model.g4bl_out_dir = form_data["output_dir"]
            self.model.scan_type = form_data["scan_type"]
            self.model.sim_type = form_data["sim_type"]

            if not isinstance(form_data["momentum"], list):
                self.model.momentum = [form_data["momentum"]]

        except Exception as e:
            self.view.display_error_message(message=f"An unexpected error has occurred! \n{e}")
            logger.critical("Simulation failed! %s", e)
            raise e

        # show simulation progress widget and cancel button
        self.view.simulation_progress_widget.show()
        self.view.cancel_sim_button.show()

        # get number of simulations and update progress bar
        n_sim = len(self.model.momentum)
        self.view.simulation_progress_bar.setMaximum(n_sim)
        self.view.simulation_progress_bar.setValue(0)

        self.view.estimated_time_remaining_label.setText(f"Estimated time left: calculating...")
        self.view.simulation_progress_label.setText(f"Running simulation 1 / {n_sim}")

        # start simulation on separate thread
        self.simulation_worker = Worker(self.model.start_g4bl_simulation)
        self.simulation_worker.signals.result.connect(self.on_simulation_finished)
        self.simulation_worker.signals.progress.connect(self.progress_fn)

        get_app().threadpool.start(self.simulation_worker)

    def cancel_sim(self):
        # if user has requested the simulation to be cancelled, set this flag to True to notify the model
        self.model.cancel_sim = True
        self.view.simulation_progress_label.setText("Stopping...")
        self.view.estimated_time_remaining_label.setText(f"Estimated time remaining: -")

    def progress_fn(self, progress: dict):
        """
        Updates progress bar and progress text. Is called every time the simulation worker emits a progress signal.

        Args:
            progress: dict with keys 'current' - current simulation number, 'total' - number of simulations planned

        """
        n = progress["current"]
        total = progress["total"]

        if n == total:
            return

        time_str = self.model.estimate_time_left(n, total)
        self.view.estimated_time_remaining_label.setText(f"Estimated time remaining: {time_str}")

        self.view.simulation_progress_bar.setMaximum(total)
        self.view.simulation_progress_label.setText(f"Running simulation {n+1} / {total}")
        self.view.simulation_progress_bar.setValue(n)

    def on_simulation_finished(self, result):
        self.model.cancel_sim = False

        # hide progress bar and cancel button when done
        self.view.simulation_progress_widget.hide()
        self.view.cancel_sim_button.hide()

        if result["status"] == "cancelled":
            self.view.display_message(message="Simulation cancelled!")
            return

        self.reset_view()

        # update table and implantation tree
        self.view.setup_results_table(self.model.momentum, self.current_table)

        self.view.update_results_tree(tree=self.current_tree,
                                      momenta=self.model.momentum,
                                      layer_names=[layer["name"] for layer in self.model.stack_input],
                                      proportions=self.model.proportions_per_layer,
                                      proportions_errs=self.model.proportions_per_layer_err,
                                      counts=self.model.counts_per_layer,
                                      counts_errs=self.model.counts_per_layer_err)

        for i, momentum in enumerate(self.model.momentum):
            fig_whole, ax_whole = self.model.plot_whole(i, momentum)
            fig_comp, ax_comp = self.model.plot_components(i, momentum)

            self.view.generate_plot_tab(momentum, i, fig_whole, ax_whole, fig_comp, ax_comp)

        # Plot stopping profiles and depth profiles
        if len(self.model.momentum) > 1:
            self.view.enable_depth_profile_tab(*self.model.plot_depth_profile())

            self.view.slider_container.show()
            self.view.momentum_slider.setMinimum(0)
            self.view.momentum_slider.setMaximum(len(self.model.momentum)-1)
            self.view.momentum_slider.setSingleStep(1)

    def stopping_shift_plot_origin(self):
        pass
    def stopping_reset_plot_origin(self):
        pass
    def depth_shift_plot_origin(self):
        pass
    def depth_reset_plot_origin(self):
        pass
    def on_save_sim_result(self):
        pass
    def on_save_all_sim_results(self):
        pass

    def on_save_all_sim_plot(self):
        # check if the figure for this momentum exists
        if not self.model.figs:
            self.view.display_error_message(message="No plots available to save.")
            return

        # default filename
        default_path = self.model.get_default_g4bl_plot_save_name()
        filter_str = "Zip Archive (*.zip)"

        # get path from user
        path = self.view.get_save_file_path(default_path, filter_str)

        if path:
            self.model.save_plot(path)

    def on_user_edited_cell(self, row, col):
        # only care about material column
        if col != 0:
            return
        table = self.view.stack_layer_setup_table
        table_item = table.item(row, 0)
        if table_item is None:
            return
        # check if the sample name is in database
        sample_name = table_item.text()
        sample_name = sample_name.replace(" ", "_")
        density_item = table.item(row, 2)
        if density_item is None:
            density_item = QTableWidgetItem("")
            table.setItem(row, 2, density_item)
        if sample_name in self.model.g4bl_materials:
            if sample_name in self.model.g4bl_compounds:
                table.setItem(row, 2, QTableWidgetItem("placeholderdisabled"))
                density_item.setFlags(density_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            else:
                table.setItem(row, 2, QTableWidgetItem(""))
                # make editable again
                density_item.setFlags(density_item.flags() | Qt.ItemFlag.ItemIsEditable)
            return
        density_item.setFlags(density_item.flags() | Qt.ItemFlag.ItemIsEditable)
        # update density column WITHOUT triggering signals (otherwise it recursively calls function when it updates value)
        table.block_updates = True
        table.setItem(row, 2, QTableWidgetItem("Unknown-Density required"))
        table.block_updates = False

    def show_plot(self, index, momentumstr):
        self.view.stopping_profiles_tab_widget.setCurrentIndex(index)

    def on_slider_moved(self, val: int):
        dt = time.time_ns() - self.time_last_swapped

        if dt < 1e7:
            return # limit swapping plots to once every 10ms

        self.show_plot(val, self.model.momentum[val])
        self.time_last_swapped = time.time_ns()

    def load_settings(self):
        pass
    def save_settings(self):
        pass

    def validate_g4bl_settings(self, form_data: dict) -> tuple[bool, str]:
        """
        Checks if form data contains valid g4bl settings

        Args:
            form_data: dict containing all g4bl setting loaded from form

        Returns:
            bool indicating whether form is valid, string containing additional information
        """

        form_data["min_momentum"] = form_data["min_momentum"]
        form_data["max_momentum"] = form_data["max_momentum"]
        self.model.step_momentum = form_data["step_momentum"]
        self.model.momentum_spread = form_data["momentum_spread"]
        self.model.sample_name = form_data["sample_name"]
        self.model.stats = form_data["stats"]
        self.model.g4bl_exe_dir = form_data["g4bl_dir"]
        self.model.g4bl_out_dir = form_data["output_dir"]
        self.model.scan_type = form_data["scan_type"]
        self.model.sim_type = form_data["sim_type"]

        if (form_data["max_momentum"] <= 0 or form_data["min_momentum"] <= 0 or
                form_data["step_momentum"] <= 0 or form_data["momentum"] <= 0):
            return False, "Momentum must be greater than 0."

        if form_data["min_momentum"] >= form_data["max_momentum"]:
            return False, "Min momentum must be less than max momentum."

        if (form_data["max_momentum"] - form_data["min_momentum"]) < form_data["step_momentum"]:
            return False, "Momentum step too high."

        if form_data["stats"] <= 0:
            return False, "Stats must be greater than 0."

        if form_data["momentum_spread"] <= 0:
            return False, "Momentum spread be greater than 0."

        if ((form_data["max_momentum"] - form_data["min_momentum"]) / form_data["step_momentum"]) > 1e6:
            return False, "Too many simulations! Please increase the momentum step."

        return True, ""

    def reset_view(self):
        self.close_figures()
        self.view.reset()