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
        self.set_checkboxes()
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

    def set_checkboxes(self):
        plot_detectors = self.model.get_plot_detectors()

        # MORE_CHANNELS IN FUTURE TO ADD MORE CHECKBOXES EXTEND THIS LIST AND UPDATE MULTI_PLOT_VIEW
        checkboxes = [
            self.view.det1_checkbox,
            self.view.det2_checkbox,
            self.view.det3_checkbox,
            self.view.det4_checkbox,
        ]
        # Loop through and set up checkboxes
        for i, checkbox in enumerate(checkboxes):
            if i < len(self.model.loaded_runs[0].loaded_detectors):
                label = self.model.loaded_runs[0].loaded_detectors[i]

                checkbox.setText(label)
                checkbox.show()

                # set checked state based on plot_detectors
                checkbox.setChecked(label in plot_detectors)

                # connect with frozen values
                checkbox.checkStateChanged.connect(
                    lambda state, name=label, cb=checkbox: self.checkbox_checked(
                        state, name, cb
                    )
                )
            else:
                checkbox.hide()

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
        # normalisation can fail if user wants to normalise by events but no comment file have been loaded
        try:
            [
                run.set_corrections(
                    normalisation=norm_type,
                    bin_rate=binning,
                    plot_mode=plot_type,
                    prompt_limit=prompt_limit,
                )
                for run in self.model.loaded_runs
            ]

            self.start_multiplot()
        except ValueError:
            self.view.display_error_message(
                title="Normalisation error",
                message="Cannot normalise by events when comment file is not loaded. Please ensure that the comment.dat file is in your loaded directory.",
            )

            self.populate_settings_panel()

    def populate_settings_panel(self):
        """
        Sets values in settings panel to settings in config.
        """
        config = get_config()
        self.binning = config["default_corrections"]["binning"]
        self.normalisation = config["default_corrections"]["normalisation"]
        self.plot_mode = config["default_corrections"]["plot_mode"]
        self.prompt_limit = config["default_corrections"]["prompt_limit"]
        self.view.binning_spin_box.setValue(self.binning)
        self.view.normalisation_type_combo_box.setCurrentIndex(
            normalisation_types.index(self.normalisation)
        )
        self.view.nexus_plot_display_combo_box.setCurrentText(self.plot_mode)
        self.view.prompt_limit_textbox.setText(str(self.prompt_limit))

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
        if len(self.model.get_plot_detectors()) == 1 and not checked:
            checkbox.setChecked(True)
            return


#        self.view.plot.update_plot(self.model.fig, self.model.axs)
