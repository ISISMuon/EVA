import time
import logging

from copy import copy
from idlelib.configdialog import font_sample_text

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QWidget
from matplotlib import pyplot as plt

from EVA.util.path_handler import get_path
from EVA.util.worker import Worker

logger = logging.getLogger(__name__)

from EVA.core.app import get_config, get_app


class TrimPresenter(QWidget):
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
        self.view.srim_exe_dir_linedit.setText(str(self.model.srim_exe_dir))
        self.view.trim_out_dir_linedit.setText(str(self.model.srim_out_dir))
        self.view.stats_linedit.setText(str(self.model.stats))

        # set momentum scam params to only be visible if momentum scan is selected
        self.on_scan_type_changed(self.view.scan_momentum_combo.currentText())
        self.view.scan_momentum_combo.currentTextChanged.connect(self.on_scan_type_changed)

        # set momentum bite param to only be visible is momentum spread simulation is selected
        self.on_sim_type_changed(self.view.sim_type_combo.currentText())
        self.view.sim_type_combo.currentTextChanged.connect(self.on_sim_type_changed)

        # add an empty row to the end of the layer table after every time the contents are updated
        self.view.layer_setup_table.contents_updated_s.connect(self.view.layer_setup_table.append_row)
        self.view.layer_setup_table.cellClicked.connect(self.append_row_in_layer_table_if_last_row_clicked)

        self.view.layer_setup_table.update_contents(self.format_model_layers(), round_to=4)

        self.view.collapse_expand_implantation_checkbox.checkStateChanged.connect(self.view.collapse_expand_implantation)

        self.view.run_sim_button.clicked.connect(self.start_sim)
        self.view.cancel_sim_button.clicked.connect(self.cancel_sim)
        self.view.shift_plot_origin_s.connect(self.shift_plot_origin)
        self.view.reset_plot_origin_s.connect(self.reset_plot_origin)

        self.view.save_s.connect(self.on_save_sim_result)
        self.view.save_all_sims_button.clicked.connect(self.on_save_all_sim_results)
        self.view.show_plot_s.connect(self.show_plot)
        self.view.momentum_slider.valueChanged.connect(self.on_slider_moved)

        self.view.file_load.triggered.connect(self.load_settings)
        self.view.file_save.triggered.connect(self.save_settings)
        self.view.file_reset.triggered.connect(self.load_default_settings)


        # set up simulation worker to run simulation on separate thread
        self.simulation_worker = None

        self.time_last_swapped = time.time_ns()

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

    def append_row_in_layer_table_if_last_row_clicked(self, row):
        if row == (self.view.layer_setup_table.rowCount()-1):
            self.view.layer_setup_table.append_row()

    def shift_plot_origin(self, index):
        try:
            new_shift = float(self.view.origin_shift_line_edits[index].text())
            self.model.plot_origin_shifts[index] += new_shift

            fig_comp, ax_comp = self.model.plot_components(index, self.model.momentum[index])
            fig_whole, ax_whole = self.model.plot_whole(index, self.model.momentum[index])

            # get the plot stack at specified index
            plot_stack = self.view.plot_stacks[index]

            # update both plots
            plot_widget_whole = plot_stack.widget(0)
            plot_widget_whole.update_plot(fig_whole, ax_whole)

            plot_widget_comp = plot_stack.widget(1)
            plot_widget_comp.update_plot(fig_comp, ax_comp)

        except (ValueError, AttributeError) as e:
            self.view.display_error_message(message="Invalid shift value!")
            raise e

    def reset_plot_origin(self, index):
        self.model.plot_origin_shifts[index] = self.model.default_origin_position
        self.view.origin_shift_line_edits[index].setText("0")

        fig_comp, ax_comp = self.model.plot_components(index, self.model.momentum[index])
        fig_whole, ax_whole = self.model.plot_whole(index, self.model.momentum[index])

        # get the plot stack at specified index
        plot_stack = self.view.plot_stacks[index]

        # update both plots
        plot_widget_whole = plot_stack.widget(0)
        plot_widget_whole.update_plot(fig_whole, ax_whole)

        plot_widget_comp = plot_stack.widget(1)
        plot_widget_comp.update_plot(fig_comp, ax_comp)

    def save_result(self, index):
        logger.debug("Saving result for index %s", index)

    def show_plot(self, index, momentumstr):
        self.view.stopping_profiles_tab_widget.setCurrentIndex(index)

    def on_slider_moved(self, val: int):
        dt = time.time_ns() - self.time_last_swapped

        if dt < 1e7:
            return # limit swapping plots to once every 10ms

        self.show_plot(val, self.model.momentum[val])
        self.time_last_swapped = time.time_ns()

    def format_model_layers(self, layers: list | None = None) -> list[list[str | float]]:
        """
        Formats the layers in TrimFitModel to a format compatible with the BaseTable's update_contents() method.

        Returns:
            Formatted array containing the layer data in TrimFitModel.
        """
        if layers is None:
            layers = self.model.input_layers

        return [[layer["name"], layer["thickness"], layer.get("density", " ")] for layer in layers]

    def get_layers_from_table(self) -> list[dict] | None:
        """
        Gets layers from table and restructures them to fit the format required by TrimFitModel

        Returns: Restructured layers
        """
        layers = self.view.layer_setup_table.get_contents()
        structured_layers = []

        for layer in layers:
            if layer[0] == "":
                # skip rows where sample name is blank - assume the whole row is empty
                continue

            name = layer[0]
            thickness = float(layer[1])

            layer_dict = {"name": name, "thickness": thickness}

            if layer_dict["thickness"] <= 0:
                raise ValueError

            # layer density is allowed to be empty for 'Beamline Window' and 'Air (compressed)'
            try:
                layer_dict["density"] = float(layer[2])

                if layer_dict["density"] <= 0:
                    raise ValueError

            except ValueError:
                if not (name == "Beamline Window" or name == "Air (compressed)"):
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

        # check that form contains valid srim settings
        valid, error = self.validate_srim_settings(form_data)

        if not valid:
            self.view.display_error_message(message=error)
            return

        # get table data
        try:
            self.model.input_layers = self.get_layers_from_table()

        except (ValueError, AttributeError, KeyError) as e:
            self.view.display_error_message(message="Invalid layers specified. All layers must have a thickness, and all layers apart from "
                                                    "Beamline window and Air must have a density specified. "
                                                    "Ensure all values are greater than 0.")
            raise e

        # check if srim exe and output path is valid
        srimdir_valid = self.model.is_valid_path(form_data["srim_dir"])
        outputdir_valid = self.model.is_valid_path(form_data["output_dir"])

        if not srimdir_valid or not outputdir_valid:
            self.view.display_error_message(message="Could not find SRIM.exe at specified location. "
                                     "Please ensure you have SRIM2013 installed.")
            return

        if form_data["momentum_spread"] and form_data["stats"] < 500:
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
            self.model.srim_exe_dir = form_data["srim_dir"]
            self.model.srim_out_dir = form_data["output_dir"]
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
        n_sim = self.model.number_of_sims()
        self.view.simulation_progress_bar.setMaximum(n_sim)
        self.view.simulation_progress_bar.setValue(0)

        self.view.estimated_time_remaining_label.setText(f"Estimated time left: calculating...")
        self.view.simulation_progress_label.setText(f"Running simulation 1 / {n_sim}")

        # start simulation on separate thread
        self.simulation_worker = Worker(self.model.start_trim_simulation)
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

        self.view.reset()

        # update table and implantation tree
        self.view.setup_results_table(self.model.momentum)

        self.view.update_results_tree(momenta=self.model.momentum,
                                      layer_names=[layer["name"] for layer in self.model.input_layers],
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

    def on_save_sim_result(self, row):
        if len(self.model.result_x) == 0: # if no simulations have been run
            self.view.display_error_message(message="No simulations to save.")
            return

        default_path = self.model.get_default_srim_save_name(self.model.momentum[row])
        filter_str = "Zip Archive (*.zip)"

        path = self.view.get_save_file_path(default_path, filter_str)

        if path:
            self.model.save_sim(path, row)

    def on_save_all_sim_results(self):
        if len(self.model.result_x) == 0: # if no simulations have been run
            self.view.display_error_message(message="No simulations to save.")
            return

        default_path = self.model.get_default_srim_save_name()
        filter_str = "Zip Archive (*.zip)"

        path = self.view.get_save_file_path(default_path, filter_str)

        if path:
            self.model.save_sim(path)

    def save_settings(self):
        try:
            form_data = self.view.get_form_data()
            layers = self.get_layers_from_table()

        except (AttributeError, ValueError) as e:
            self.view.display_error_message(message="Cannot save settings. Invalid data in form or layers table.")
            return

        valid, error = self.validate_srim_settings(form_data)

        if not valid:
            self.view.display_error_message(message=error)
            return

        path = self.view.get_save_file_path(get_config()["general"]["working_directory"],
                                            file_filter="Text file (*.txt)")
        if path != "":
            self.model.save_settings(**form_data, layers=layers, target_dir=path)

    def load_settings(self):
        path = self.view.get_load_file_path(get_config()["general"]["working_directory"],
                                            file_filter="Text file (*.txt)")
        if path != "":
            form_data, table_data = self.model.load_settings(path)
            self.view.set_form_data(form_data)
            self.view.layer_setup_table.update_contents(self.format_model_layers(table_data))

    def load_default_settings(self):
        path = get_path("./src/EVA/core/settings/srim_defaults.txt")

        form_data, table_data = self.model.load_settings(path)
        self.view.set_form_data(form_data)
        self.view.layer_setup_table.update_contents(self.format_model_layers(table_data))

    def validate_srim_settings(self, form_data: dict) -> tuple[bool, str]:
        """
        Checks if form data contains valid SRIM settings

        Args:
            form_data: dict containing all srim setting loaded from form

        Returns:
            bool indicating whether form is valid, string containing additional information
        """

        form_data["min_momentum"] = form_data["min_momentum"]
        form_data["max_momentum"] = form_data["max_momentum"]
        self.model.step_momentum = form_data["step_momentum"]
        self.model.momentum_spread = form_data["momentum_spread"]
        self.model.sample_name = form_data["sample_name"]
        self.model.stats = form_data["stats"]
        self.model.srim_exe_dir = form_data["srim_dir"]
        self.model.srim_out_dir = form_data["output_dir"]
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

