from EVA.core.app import get_config
from EVA.core.data_structures.run import normalisation_types
import logging
from EVA.gui.windows.multiplot.multi_plot_model import MultiPlotModel
from EVA.gui.windows.multiplot.multi_plot_view import MultiPlotView
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox

# from EVA.core.data_structures.multirun import MultiRun
logger = logging.getLogger(__name__)


class MultiPlotPresenter:
    def __init__(self, view: MultiPlotView, model: MultiPlotModel):
        self.view = view
        self.model = model
        self.populate_settings_panel()
        self.view.load_multi.clicked.connect(self.load_multirun)
        self.view.plot_multi.clicked.connect(self.start_multiplot)
        self.view.apply_run_settings_button.clicked.connect(self.on_apply_settings)

    def start_multiplot(self):
        # plots multiple runs from the runlist and with a y offset
        if len(self.model.loaded_runs) == 0 or not self.model.loaded_runs:
            logger.error("Cannot plot with no runs loaded.")
            self.view.display_error_message(
                title="Multi-run plot error",
                message="Error: You must specify at least one valid run number in the table and load it to plot.",
            )
            return
        offset, _ = self.view.get_form_data()
        plot_detectors = self.view.get_checked_detectors()
        if not any(plot_detectors.values()):
            self.view.display_error_message(
                title="No detectors selected",
                message="Please select at least one detector."
            )
            return
        self.model.fig, self.model.axs = self.model.multi_plot(
            self.model.loaded_runs, offset, plot_detectors
        )
        self.view.plot.update_plot(self.model.fig, self.model.axs)

    def load_multirun(self):
        try:
            offset, table_data = self.view.get_form_data()
        except (ValueError, AttributeError):
            self.view.display_message(title="Input error", message="Invalid input.")
            return

        run_list = self.detect_runs(table_data)
        if not run_list:  # if no runs found
            self.model.loaded_runs = []
            logger.error("No runs specified for multiplot.")
            self.view.display_error_message(
                title="Multi-run plot error",
                message="Error: You must specify at least one valid run number in the table.",
            )
            return

        runs, empty_runs, norm_failed_runs = self.model.load_multirun(run_list)
        # reads data and returns as each detector and as an array
        self.model.loaded_runs = runs
        self.model.offset = offset
        # error handling
        run_numbers_str = ", ".join([str(run.run_num) for run in empty_runs])

        if 0 < len(empty_runs) < 10:
            self.view.display_message(
                title="Multi-run plot error",
                message=f"Error: No files found for following run(s): {run_numbers_str}",
            )
        elif len(empty_runs) >= 10:
            self.view.display_message(
                title="Multi-run plot error",
                message="Error: More than 10 runs failed to load.",
            )

        if len(runs) == 0:
            logger.error("No files found for runs %s.", run_numbers_str)
            return  # Quit now if all runs failed to load
        else:
            logger.warning("No files found for runs %s.", run_numbers_str)

        # Assuming all runs have same detectors loaded.
        self.setup_detector_checkboxes()
        self.view.apply_run_settings_button.setEnabled(True)

    def detect_runs(self, table_data):
        run_list = self.model.GenReadList(table_data)
        if not run_list:  # if no runs found
            logger.error("No runs specified for multiplot.")
            self.view.display_error_message(
                title="Multi-run plot error",
                message="Error: You must specify at least one valid run number in the table.",
            )

            return
        else:
            return run_list

    def setup_detector_checkboxes(self):
        # Clear existing checkboxes/widgets from the grid layout
        while self.view.detector_select_layout.count():
            item = self.view.detector_select_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        self.view.checkboxes = []

        for i, detector_name in enumerate(self.model.loaded_runs[0].loaded_detectors):
            checkbox = QCheckBox(detector_name)

            # 4 checkboxes per row
            row = i // 4
            column = i % 4

            self.view.detector_select_layout.addWidget(
                checkbox, row, column
            )

            self.view.checkboxes.append(checkbox)

            # if detector_name in self.model.loaded_runs[0].plot_detectors:
            checkbox.setChecked(False)  # Uncheck all checkboxes by default

            # Connect with frozen values
            checkbox.checkStateChanged.connect(
                lambda state, name=detector_name, cb=checkbox:
                    self.checkbox_checked(state, name, cb)
            )

            checkbox.show()

    def on_apply_settings(self):
        """
        Is called when user clicks apply in the run settings area. Calls the model to update
        normalisation and binning in config and to reapply the parameters to the data.
        """

        binning = self.view.binning_spin_box.value()
        normalisation_index = self.view.normalisation_type_combo_box.currentIndex()
        norm_type = normalisation_types[normalisation_index]
        plot_type = self.view.nexus_plot_display_combo_box.currentText()
        prompt_limit = self.view.prompt_limit_textbox.text()
        delayed_limit = self.view.delayed_limit_textbox.text()

        # normalisation can fail if user wants to normalise by events but no comment file have been loaded
        try:
            [
                run.set_corrections(
                    normalisation=norm_type,
                    bin_rate=binning,
                    plot_mode=plot_type,
                    prompt_limit=prompt_limit,
                    delayed_limit=delayed_limit,
                )
                for run in self.model.loaded_runs
            ]

            self.start_multiplot()
        except ValueError as e:
            self.view.display_error_message(
                title="Run correction error",
                message=str(e),
            )
            # self.populate_settings_panel()

    def populate_settings_panel(self):
        """
        Sets values in settings panel to settings in config.
        """
        config = get_config()
        self.binning = config["default_corrections"]["binning"]
        self.normalisation = config["default_corrections"]["normalisation"]
        self.plot_mode = config["default_corrections"]["plot_mode"]
        self.prompt_limit = config["default_corrections"]["prompt_limit"]
        self.delayed_limit = config["default_corrections"]["delayed_limit"]

        self.view.binning_spin_box.setValue(self.binning)
        self.view.normalisation_type_combo_box.setCurrentIndex(
            normalisation_types.index(self.normalisation)
        )
        self.view.nexus_plot_display_combo_box.setCurrentText(self.plot_mode)
        self.view.prompt_limit_textbox.setText(str(self.prompt_limit))
        self.view.delayed_limit_textbox.setText(str(self.delayed_limit))

    def checkbox_checked(
        self, checkstate: Qt.CheckState, detector: str, checkbox: QCheckBox
    ):
        """
        Is called when user checks one of the detector checkboxes to select which detectors to plot for.

        Args:
            checkstate: checkstate of box
            detector: detector name
            checkbox: reference to checkbox checked
        """

        checked = checkstate == Qt.CheckState.Checked

        # only allow loaded detectors to be plotted

        # if last detector has been unchecked
        checked_detectors = [cb for cb in self.view.checkboxes if cb.isChecked()]
        if checked_detectors == 1 and not checked:
            checkbox.setChecked(True)
            return
        # Currently disabling as updating plot on every checkbox change is very slow for large number of runs.
        # offset, _ = self.view.get_form_data()
        # self.model.fig, self.model.axs = self.model.multi_plot(self.model.loaded_runs, offset, checked_detectors)
        # self.view.plot.update_plot(self.model.fig, self.model.axs)

