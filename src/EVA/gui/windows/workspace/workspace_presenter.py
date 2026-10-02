import logging
from PyQt6.QtGui import QCloseEvent

from EVA.core.app import get_config
from EVA.core.data_structures.run import normalisation_types
from EVA.gui.dialogs.detector_corrections.detector_corrections_dialog import (
    DetectorCorrectionsDialog,
)
from EVA.gui.dialogs.general_settings.settings_dialog import SettingsDialog
from EVA.gui.windows.manual.manual_window import ManualWindow
from EVA.gui.windows.muonic_xray_simulation.model_spectra_window import (
    ModelSpectraWindow,
)
from EVA.gui.windows.peakfit.peakfit_window import PeakFitWindow
from EVA.gui.windows.fit_table_plot.fit_table_plot_window import FitTablePlotWindow
from EVA.gui.windows.periodic_table.periodic_table_widget import PeriodicTableWidget
from EVA.gui.windows.srim.trim_window import TrimWindow
from EVA.gui.windows.workspace.workspace_model import WorkspaceModel
from EVA.gui.windows.workspace.workspace_view import WorkspaceView

logger = logging.getLogger(__name__)


class WorkspacePresenter:
    """Presenter class to connect workspace view to workspace model."""

    def __init__(self, view: WorkspaceView, model: WorkspaceModel):
        """
        Initialises presenter.

        Args:
            view:
            model:
        """

        self.view = view
        self.model = model

        # Set up action bar connections
        self.generate_peakfit_options()
        if get_config()["general"]["current_grouping_profile"] is not None:
            self.current_profile = get_config()["general"]["current_grouping_profile"]
        else:
            self.current_profile = None

        # load settings from config into settings panel
        self.populate_settings_panel()
        # self.view.trim_fit.triggered.connect(self.open_trim_fit)
        self.view.trim_simulation.triggered.connect(self.open_trim)
        self.view.model_muon_spectrum.triggered.connect(self.open_model_muon_spectrum)
        self.view.periodic_table.triggered.connect(self.open_periodic_table)
        self.view.apply_run_settings_button.clicked.connect(self.on_apply_settings)
        self.view.fit_table_plot.triggered.connect(self.open_fit_table_plot)

        self.view.detector_corrections_menu_button.clicked.connect(self.open_detector_corrections_dialog)
        self.view.general_settings.triggered.connect(self.open_general_settings_dialog)

        self.view.help_manual.triggered.connect(self.open_manual)
        self.view.tabWidget.tabCloseRequested.connect(self.view.close_tab)

        self.view.group_detector_checkbox.toggled.connect(
            self.on_group_detector_checkbox_toggled
        )
        self.view.export_run_data_button.clicked.connect(self.export_run_data)
        self.view.save_and_close_requested_s.connect(self.save_and_close)

        get_config().config_modified_s.connect(self.process_setting_updates)

    def process_setting_updates(self, settings):
        """
        This method is called every time the config is updated, checks what was changed,
        and takes care of signaling to the rest of the program how it should respond to the change.

        This ensures that all parts of the code are in sync.

        Args:
            settings: what was changed
        """
        if "plot" in settings.keys():
            if "show_plot" in settings["plot"].keys():
                self.view.update_detector_plot_selection_s.emit()

            if "fill_colour" in settings["plot"].keys():
                self.view.update_plot_fill_colour_s.emit()

    def populate_settings_panel(self):
        """
        Sets values in settings panel to settings in config.
        """

        self.view.binning_spin_box.setValue(self.model.binning)
        self.view.normalisation_type_combo_box.setCurrentIndex(
            normalisation_types.index(self.model.normalisation)
        )
        self.view.nexus_plot_display_combo_box.setCurrentText(self.model.plot_mode)
        self.view.prompt_limit_textbox.setText(str(self.model.prompt_limit))
        self.view.delayed_limit_textbox.setText(str(self.model.delayed_limit))

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

        detector_group_dict = None
        efficiency_corrections_dict = None
        energy_corrections_dict = None
        if self.view.group_detector_checkbox.isChecked():
            detector_group_dict = self.detector_group_dict

        if self.view.efficiency_correction_checkbox.isChecked():
            efficiency_corrections_dict = self.efficiency_corrections

        if self.view.energy_correction_checkbox.isChecked():
            energy_corrections_dict = self.energy_corrections

        # normalisation can fail if user wants to normalise by events but no comment file have been loaded
        try:
            run_correction_settings = dict(
                normalisation=norm_type,
                bin_rate=binning,
                plot_mode=plot_type,
                prompt_limit=int(prompt_limit),
                delayed_limit=int(delayed_limit),
                detector_group_dict=detector_group_dict,
                efficiency_corrections=efficiency_corrections_dict,
                energy_corrections=energy_corrections_dict,
            )

            self.model.run.set_corrections(**run_correction_settings)

        except ValueError as e:
            self.view.display_error_message(
                title="Error occured while applying settings",
                message=str(e),
            )

            self.populate_settings_panel()

    def on_settings_applied(self, settings: dict):
        """
        Is called whenever settings are applied in the settings dialog. Checks to see if anything needs to be
        updated in the workspace.

        Args:
            settings: what was changed.
        """

        if "plot" in settings.keys():
            if "fill_colour" in settings["plot"].keys():
                self.view.replot_spectra_s.emit()

    def on_detector_corrections_applied(self, corrections: dict):
        self.current_profile = corrections["detector_grouping"]
        self.energy_corrections = corrections["energy_corrections"]
        self.efficiency_corrections = corrections["efficiency_corrections"]
        self.view.efficiency_corrections_checkbox.setChecked(False)
        self.view.energy_corrections_checkbox.setChecked(False)
        self.view.group_detector_checkbox.setChecked(False)

    def generate_peakfit_options(self):
        self.view.setup_peakfit_options()
        for i, detector in enumerate(self.view.detector_list):
            self.view.peakfit_menu_actions[i].triggered.connect(
                lambda _, det=detector: self.open_peakfit(det)
            )

    def on_group_detector_checkbox_toggled(self):
        valid = self.validate_grouping_profile()
        if not valid:
            self.view.group_detector_checkbox.blockSignals(True)
            self.view.group_detector_checkbox.setChecked(False)
            self.view.group_detector_checkbox.blockSignals(False)
            return
        self.on_apply_settings()
        self.generate_peakfit_options()

    def validate_grouping_profile(self):
        if self.current_profile is None:
            self.view.display_error_message(
                title="No grouping profile selected",
                message="Please select a grouping profile before enabling detector grouping.",
            )
            return False

        grouping_profile = get_config()["general"]["saved_grouping_profiles"][
            self.current_profile
        ]
        # Filter out groups that do not have any detectors in the current run
        valid_groups = {
            group: [det for det in detectors if det in self.model.run._raw]
            for group, detectors in grouping_profile.items()
            if any(det in self.model.run._raw for det in detectors)
        }
        if len(valid_groups) == 0:
            self.view.display_error_message(
                title="Invalid grouping profile",
                message=f"Grouping profile {self.current_profile} does not include any detectors. Please update the grouping profile.",
            )
            return False
        else:
            self.detector_group_dict = valid_groups
            return True

    def reset_to_default_config(self):
        """
        Resets all settings to default values.
        """

        config = get_config()
        config.restore_defaults()

        self.view.display_message(
            message="Configurations have been restored to defaults."
        )

    #### OPENING / CLOSING WINDOWS ############################################
    def open_general_settings_dialog(self):
        """Opens the general settings dialog."""
        logger.info("Opening settings dialog.")

        dialog = SettingsDialog()
        self.view.general_settings_dialogs.append(dialog)

        dialog.show()
        dialog.view.dialog_closed_s.connect(
            lambda: self.close_general_settings_dialog(dialog)
        )
        dialog.view.settings_applied_s.connect(self.on_settings_applied)

    def close_general_settings_dialog(self, dialog: SettingsDialog):
        """Closes settings dialog"""
        logger.info("Closed settings dialog.")

        self.view.general_settings_dialogs.remove(dialog)
        dialog.view.deleteLater()

    def open_detector_corrections_dialog(self):
        """Opens the detector corrections dialog."""
        dialog = DetectorCorrectionsDialog(self.view, self.model.run)
        self.view.detector_corrections_dialogs.append(dialog)
        dialog.detector_corrections_applied_s.connect(self.on_detector_corrections_applied)
        dialog.show()
        dialog.dialog_closed_s.connect(
            lambda: self.close_detector_corrections_dialog(dialog)
        )

    def close_detector_corrections_dialog(self, dialog: DetectorCorrectionsDialog):
        """Closes detector corrections dialog."""
        logger.info("Closed detector corrections dialog.")

        self.view.detector_corrections_dialogs.remove(dialog)
        dialog.view.deleteLater()

    def open_manual(self):
        """Opens manual window."""
        logger.info("Opening manual window.")

        window = ManualWindow()
        self.view.manual_windows.append(window)

        window.show()
        window.window_closed_s.connect(lambda: self.close_manual(window))

    def close_manual(self, window: ManualWindow):
        """Remove reference to manual window when closed"""
        logger.info("Closing manual window.")

        self.view.manual_windows.remove(window)
        window.deleteLater()

    def open_periodic_table(self):
        """Opens periodic table window."""
        logger.info("Opening periodic table window.")

        window = PeriodicTableWidget()
        self.view.periodic_table_windows.append(window)

        window.showMaximized()
        window.window_closed_s.connect(lambda: self.close_periodic_table(window))

    def close_periodic_table(self, window):
        """Remove reference to periodic table window when closed"""
        logger.info("Closed periodic table window.")

        self.view.periodic_table_windows.remove(window)
        window.deleteLater()

    #### OPENING TABS ##################################################
    def open_peakfit(self, detector):
        """Opens a tab for peakfit."""

        logger.info("Launching peak fitting tab for %s.", detector)
        window = PeakFitWindow(self.view.run, detector, parent=self.view)
        self.view.open_new_tab(window.widget(), f"{detector} Peak Fitting")

    def open_fit_table_plot(self, detector):
        """Opens a tab for peakfit."""

        logger.info("Launching fit table plot tab.")
        window = FitTablePlotWindow()
        self.view.open_new_tab(window.widget(), "Fit Table Plotting")

    def open_trim(self):
        """Opens a tab for TRIM."""

        logger.info("Launching TRIM tab.")
        window = TrimWindow()
        self.view.open_new_tab(window.widget(), "TRIM Simulations")

    def open_model_muon_spectrum(self):
        """Opens a tab for muonic x-ray modelling."""

        logger.info("Launching muonic x-ray modelling tab.")
        window = ModelSpectraWindow()
        self.view.open_new_tab(window.widget(), "Muonic X-ray Modelling")

    """
    def open_trim_fit(self):

        logger.info("Launching TRIM fit window.")
        if self.view.trim_fit_window is None:
            self.view.trim_fit_window = TrimFitWidget()
            self.view.trim_fit_window.show()
        else:
            self.view.trim_fit_window.show()
            
    """

    def save_and_close(self, event: QCloseEvent):
        """
        Saves current run corrections before closing the workspace.

        Args:
            event: close event
        """

        self.model.save_run_corrections()
        event.accept()

        # notify rest of program that window has closed
        self.view.window_closed_s.emit(event)

    def export_run_data(self):
        # default filename
        def_dir = get_config()["general"]["working_directory"]
        filter_str = "Zip Archive (*.zip)"
        # get path from user
        path = self.view.get_save_file_path(def_dir, filter_str)
        if path:
            self.model.export_run_data(path)