from copy import deepcopy, copy

import numpy as np
from PyQt6.QtWidgets import QTableWidgetItem

from EVA.core.app import get_app
from EVA.util.worker import Worker
from EVA.windows.trim_fitting.layer_data_assignment_window import LayerDataAssignmentWidget


class TrimFitPresenter:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.model.input_layers = self.model.input_layers
        self.view.layer_table.update_contents(self.format_model_layers(), round_to=4)
        self.view.layer_table.append_row()

        self.view.momentum_spread_line_edit.setText(str(self.model.momentum_spread))
        self.view.num_ions_line_edit.setText(str(self.model.stats))

        self.view.sim_type_combo.setCurrentText(self.model.sim_type)

        self.view.layer_table.cellClicked.connect(self.on_cell_clicked)

        self.view.load_data_button.clicked.connect(self.load_data)
        self.view.plot_data_button.clicked.connect(self.plot_experiment_data)
        self.view.fit_button.clicked.connect(self.start_fit)
        self.view.test_simulation_button.clicked.connect(self.on_test_first_iter)

        self.view.cancel_button.clicked.connect(self.cancel_sim)

        self.layer_data_assignment_window = None
        self.layer_assignment_form_data = None

    def load_data(self):
        """
        Opens the layer data assignment window and saves a copy of the sample layer names for later reference.
        """

        self.model.input_layers = self.get_layers()
        self.model.setup_sample(self.model.input_layers)

        if self.layer_assignment_form_data is None:
            self.layer_data_assignment_window = LayerDataAssignmentWidget(layer_names=self.model.sample_names)

        else:
            self.layer_data_assignment_window = LayerDataAssignmentWidget(layer_names=self.model.sample_names,
                                                                          form_data=self.layer_assignment_form_data)
        self.layer_data_assignment_window.show()
        self.layer_data_assignment_window.data_loaded_s.connect(self.on_experiment_data_loaded)

    def on_experiment_data_loaded(self, form_data: dict, selections: np.ndarray):
        """
        Takes experiment data loaded by user via the layer data assignment window and updates the model and view with it.

        Args:
            selections: list of numpy arrays containing the data loaded. layers with no loaded data have an empty array.
            form_data: parameters used for loading the file (saved in presenter so that user does not have to re-enter them when reopening the window)
        """

        self.layer_assignment_form_data = form_data

        self.model.momentum = np.array(selections[0])
        self.model.proportions = np.array(selections[1:])

        # get the indices of the layers in self.proportions which contain non-zero values (layers to be fitted)
        self.model.target_indices = [i for i, layer in enumerate(self.model.proportions) if any(layer)]

        # save a copy of the sample names now to compare later before simulation to avoid bugs
        self.model.proportions_sample_names = copy(self.model.sample_names)

        labels = ["Momentum", *self.model.sample_names]
        self.view.experiment_data_table.setRowCount(len(labels))
        self.view.experiment_data_table.setVerticalHeaderLabels(labels)

        # make a printable copy of the experiment data (with empty cells rather than zeroes where no data is present)
        experiment_data_printable = deepcopy(selections)

        for i, data in enumerate(selections):
            if not np.any(data):
                experiment_data_printable[i] = ["(No data)", *["" for _ in range(len(selections[0])-1)]]

        # update table finally
        self.view.experiment_data_table.update_contents(experiment_data_printable, resize_columns=True)

    def plot_experiment_data(self):
        """
        Updates the experiment data plot using the selections set in model.
        """
        self.view.plot.update_plot(*self.model.plot_initial_proportions())
        self.view.trim_results.setCurrentIndex(1)

    def prepare_model(self):
        """
        Gets all simulation parameters from the view and sets them in the model
        """
        try:
            form_data = self.view.get_form_data()
        except (ValueError, AttributeError):
            self.view.display_error_message("Invalid form data!")
            return

        self.model.input_layers = self.get_layers()
        self.model.sample_names = [layer["name"] for layer in self.model.input_layers]

        self.model.sim_type = form_data["sim_type"]
        self.model.momentum_spread = form_data["momentum_spread"]
        self.model.scan_type = "Yes"
        self.model.stats = form_data["num_ions"]

        # checks if there is a mismatch between the sample name list currently in the table and the sample name list
        # which was saved when user data was loaded (if a new layer is added and the user forgot to update the data)

        if self.model.proportions_sample_names != self.model.sample_names:
            self.view.display_error_message(message="Mismatch between layers in simulation layers and layers in loaded data! Please ensure the correct data is loaded before starting.")
            self.load_data()
            return

    def start_fit(self):
        self.prepare_model() # get all data from the form

        try:
            # start simulation on separate thread
            self.simulation_worker = Worker(self.model.optimise)
            self.simulation_worker.signals.result.connect(self.on_simulation_finished)
            self.simulation_worker.signals.progress.connect(self.progress_fn)

            get_app().threadpool.start(self.simulation_worker)

        except Exception as e:
            self.view.display_error_message(message=f"SRIM error: {e}")
            raise e

    def progress_fn(self, progress: dict):
        """
        Updates progress text. Is called every time the simulation worker emits a progress signal.

        Args:
            progress: dict with keys 'current' - current simulation number, 'total' - number of simulations planned

        """

        # is emitted every time an iteration is completed
        if progress.get("iteration", None) is not None:
            self.view.fit_iteration_label.setText(f"Fit iteration: {progress["iteration"]}")
            sim_data = progress["sim_proportion"]

            fig, ax = self.model.plot_progress(self.model.momentum, sim_data, progress["iteration"])
            self.view.comparison_plot.update_plot(fig, ax)
            self.view.trim_results.setCurrentIndex(0)

            self.view.fit_log_text_browser.setText(f"Current fit error: {np.sum(progress["residuals"])**2}\n" + "\n".join([f"{name} = {val}"
                                                              for name, val in progress["params"].valuesdict().items()]))
            return

        # otherwise, every time a single simulation is completed
        n = progress["current"]
        total = progress["total"]

        if n == total:
            return

        time_str = self.model.estimate_time_left(n, total)
        self.view.time_remaining_label.setText(f"Estimated time left of iteration: {time_str}")
        self.view.simulation_number_label.setText(f"Running simulation {n} / {total}")
        self.view.simulation_progress_bar.setMaximum(total)
        self.view.simulation_progress_bar.setValue(n)

    def on_simulation_finished(self, result: dict):
        """
        Is called when simulation is over.

        Args:
            result:

        Returns:

        """
        self.view.time_remaining_label.setText("Time left:")

        if result["status"] == "cancelled":
            return

        for m, momentum in enumerate(self.model.momentum):
            fig_whole, ax_whole = self.model.plot_whole(m, momentum)
            fig_comp, ax_comp = self.model.plot_components(m, momentum)

            self.view.generate_plot_tab(momentum, m, fig_whole, ax_whole, fig_comp, ax_comp)

        self.view.comparison_plot.update_plot(*self.model.plot_comparison())

    def on_test_first_iter(self):
        self.prepare_model()

        try:
            # start simulation on separate thread
            self.simulation_worker = Worker(self.model.test_first_iter)
            self.simulation_worker.signals.result.connect(self.on_simulation_finished)
            self.simulation_worker.signals.progress.connect(self.progress_fn)

            get_app().threadpool.start(self.simulation_worker)

        except Exception as e:
            self.view.display_error_message(message=f"SRIM error: {e}")
            raise e

    def format_model_layers(self) -> list[list[str | float]]:
        """
        Formats the layers in TrimFitModel to a format compatible with the BaseTable's update_contents() method.

        Returns:
            Formatted array containing the layer data in TrimFitModel.
        """
        return [[layer["name"], layer["thickness"], layer.get("density", " ")] for layer in self.model.input_layers]

    def on_cell_clicked(self, row: int):
        """
        Adds a row to the layer table when cell in last row is clicked

        Args:
            row: row number
        """
        table = self.view.layer_table
        if row == table.rowCount() - 1: # if cell on last row is edited
            self.view.layer_table.append_row()

    def get_layers(self) -> list[dict] | None:
        """
        Gets layers from table and restructures them to fit the format required by TrimFitModel

        Returns: Restructured layers
        """
        layers = self.view.layer_table.get_contents()
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

    def cancel_sim(self):
        self.model.cancel_sim = True