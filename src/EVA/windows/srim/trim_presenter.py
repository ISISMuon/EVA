import time
import logging

from copy import copy

from PyQt6.QtWidgets import QWidget

from EVA.util.path_handler import get_path

logger = logging.getLogger(__name__)

from EVA.core.app import get_config


class TrimPresenter(QWidget):
    def __init__(self, view, model, parent=None):
        super().__init__(parent)
        self.view = view
        self.model = model

        self.view.sample_name_linedit.setText("Cu")
        self.view.momentum_linedit.setText(str(self.model.momentum))
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

        self.view.run_sim_button.clicked.connect(self.start_sim)
        self.view.shift_plot_origin_s.connect(self.shift_plot_origin)
        self.view.reset_plot_origin_s.connect(self.reset_plot_origin)

        self.view.save_s.connect(self.on_save_sim_result)
        self.view.save_all_sims_button.clicked.connect(self.on_save_all_sim_results)
        self.view.show_plot_s.connect(self.show_plot)

        self.view.file_load.triggered.connect(self.load_settings)
        self.view.file_save.triggered.connect(self.save_settings)
        self.view.file_reset.triggered.connect(self.load_default_settings)

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
        logger.debug("Showing plot for momentum %s at index %s", momentumstr, index)
        self.view.results_tabs.setCurrentIndex(index)

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

            try:
                name = layer[0]
                thickness = float(layer[1])

            except ValueError:
                self.view.display_error_message(message="Invalid layers in table.")
                return

            layer_dict = {"name": name, "thickness": thickness}

            # layer density is allowed to be empty for 'Beamline Window' and 'Air (compressed)'
            try:
                layer_dict["density"] = float(layer[2])

            except ValueError:
                if not (name == "Beamline Window" or name == "Air (compressed)"):
                    self.view.display_error_message(message=f"Invalid density for '{name}'.")
                    return

            structured_layers.append(layer_dict)

        return structured_layers

    def remove_layer(self, row):
        self.model.remove_layer(row)
        self.view.layer_setup_table.update_contents(self.format_model_layers())

    def start_sim(self):
        # get form data
        try:
            form_data = self.view.get_form_data()
        except (ValueError, AttributeError) as e:
            self.view.show_error_box("Invalid form input!")
            return

        # get table data
        try:
            self.model.input_layers = self.get_layers_from_table()

        except (ValueError, AttributeError) as e:
            self.view.display_error_message(message="You must specify a valid sample name and thickness for all layers.")
            raise e

        except KeyError:
            self.view.display_error_message(message="All element layers must have a specified density.")
            return

        # check if path is valid
        srimdir_valid = self.model.is_valid_path(form_data["srim_dir"])
        outputdir_valid = self.model.is_valid_path(form_data["output_dir"])

        if not srimdir_valid or not outputdir_valid:
            self.view.display_error_message(message="Could not find SRIM.exe at specified location. "
                                     "Please ensure you have SRIM2013 installed.")
            return

        # if everything is ok, send data to model and simulate
        try:
            self.model.momentum = form_data["momentum"]
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

            self.model.start_trim_simulation()

        except Exception as e:
            self.view.display_error_message(message=f"An unexpected error has occurred! \n{e.args}")
            raise e

        self.view.reset()

        for i, momentum in enumerate(self.model.momentum):
            fig_whole, ax_whole = self.model.plot_whole(i, momentum)
            fig_comp, ax_comp = self.model.plot_components(i, momentum)

            self.view.generate_plot_tab(momentum, i, fig_whole, ax_whole, fig_comp, ax_comp)

        #self.view.plot_comp.update_plot(*self.model.plot_components(0, str(self.model.momentum[0])))

        self.view.setup_results_table(self.model.momentum)

        self.view.update_results_tree(momenta=self.model.momentum, layer_names=[layer["name"] for layer in self.model.input_layers],
                                      components=self.model.components)

        #self.view.setup_results_table(self.model.momentum, self.model.components) # display results in table

    def on_show_plot_comp(self, row, momentum):
        t0 = time.time_ns()
        # Generate figure to display in view
        fig, ax = self.model.plot_components(row, momentum)
        self.view.plot_comp.update_plot(fig, ax)
        t1 = time.time_ns()
        print("time taken: ", (t1-t0)/1e9)

    def on_cell_clicked(self, row, col):
        table = self.view.tab1.table_TRIMsetup
        if row == table.rowCount() - 1: # if cell on last row is edited
            self.view.add_trimsetup_row()

    def on_show_plot_whole(self, row, momentum):
        # Generate figure to display in view
        fig, ax = self.model.plot_whole(row, momentum)
        self.view.plot_whole.update_plot(fig, ax)

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
            raise e
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