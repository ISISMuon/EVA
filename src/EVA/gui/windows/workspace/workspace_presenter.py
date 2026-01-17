import logging
import inspect
from PyQt6.QtGui import QCloseEvent

from EVA.core.app import get_config
from EVA.core.data_structures.run import normalisation_types
from EVA.gui.dialogs.energy_corrections.energy_corrections_dialog import EnergyCorrectionsDialog
from EVA.gui.dialogs.general_settings.settings_dialog import SettingsDialog
from EVA.gui.windows.manual import manual_window
from EVA.gui.windows.manual.manual_window import ManualWindow
from EVA.gui.windows.muonic_xray_simulation.model_spectra_window import ModelSpectraWindow
from EVA.gui.windows.peakfit.peakfit_window import PeakFitWindow
from EVA.gui.windows.periodic_table.periodic_table_widget import PeriodicTableWidget
from EVA.gui.windows.srim.trim_window import TrimWindow
from EVA.gui.windows.trim_fitting.trim_fit_widget import TrimFitWidget
from EVA.gui.windows.workspace.workspace_model import WorkspaceModel
from EVA.gui.windows.workspace.workspace_view import WorkspaceView

logger = logging.getLogger(__name__)

class WorkspacePresenter:
    """ Presenter class to connect workspace view to workspace model. """
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

        for i, detector in enumerate(self.view.detector_list):
            self.view.peakfit_menu_actions[i].triggered.connect(lambda _, det=detector: self.open_peakfit(det))

        # self.view.trim_fit.triggered.connect(self.open_trim_fit)
        self.view.trim_simulation.triggered.connect(self.open_trim)
        self.view.model_muon_spectrum.triggered.connect(self.open_model_muon_spectrum)
        self.view.periodic_table.triggered.connect(self.open_periodic_table)
        self.view.apply_run_settings_button.clicked.connect(self.on_apply_settings)

        self.view.energy_correction_settings.triggered.connect(self.open_energy_corrections_dialog)
        self.view.general_settings.triggered.connect(self.open_general_settings_dialog)

        self.view.help_manual.triggered.connect(self.open_manual)

        self.view.tabWidget.tabCloseRequested.connect(self.view.close_tab)
        self.populate_settings_panel()

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
        self.view.normalisation_type_combo_box.setCurrentIndex(normalisation_types.index(self.model.normalisation))
        self.view.nexus_plot_display_combo_box.setCurrentText(self.model.plot_mode)
        self.view.prompt_limit_textbox.setText(str(self.model.prompt_limit))

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
            kwargs = dict(
                normalisation=norm_type,
                bin_rate=binning,
                plot_mode=plot_type,
                prompt_limit=int(prompt_limit),
                )
            # dynamically filter only supported arguments for loaded run type
            sig = inspect.signature(self.model.run.set_corrections)
            valid_params = sig.parameters.keys()
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
            self.model.run.set_corrections(**filtered_kwargs)

        except ValueError:
            self.view.display_error_message(title="Normalisation error",
                                            message="Cannot normalise by events when comment file is not loaded. Please ensure that the comment.dat file is in your loaded directory.")

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

    def reset_to_default_config(self):
        """
        Resets all settings to default values.
        """

        config = get_config()
        config.restore_defaults()

        self.view.display_message(message="Configurations have been restored to defaults.")

    #### OPENING / CLOSING WINDOWS ############################################

    def open_general_settings_dialog(self):
        """ Opens the general settings dialog. """
        logger.info("Opening settings dialog.")

        dialog = SettingsDialog()
        self.view.general_settings_dialogs.append(dialog)

        dialog.show()
        dialog.view.dialog_closed_s.connect(lambda: self.close_general_settings_dialog(dialog))
        dialog.view.settings_applied_s.connect(self.on_settings_applied)

    def close_general_settings_dialog(self, dialog: SettingsDialog):
        """ Closes settings dialog"""
        logger.info("Closed settings dialog.")

        self.view.general_settings_dialogs.remove(dialog)
        dialog.view.deleteLater()

    def open_energy_corrections_dialog(self):
        """ Opens the energy corrections dialog. """
        dialog = EnergyCorrectionsDialog(self.model.run)
        self.view.energy_corrections_dialogs.append(dialog)

        dialog.show()
        dialog.view.dialog_closed_s.connect(lambda: self.close_energy_corrections_dialog(dialog))

    def close_energy_corrections_dialog(self, dialog: EnergyCorrectionsDialog):
        """ Closes energy corrections dialog. """
        logger.info("Closed energy corrections dialog.")

        self.view.energy_corrections_dialogs.remove(dialog)
        dialog.view.deleteLater()

    def open_manual(self):
        """ Opens manual window. """
        logger.info("Opening manual window.")

        window = ManualWindow()
        self.view.manual_windows.append(window)

        window.show()
        window.window_closed_s.connect(lambda: self.close_manual(window))

    def close_manual(self, window: ManualWindow):
        """ Remove reference to manual window when closed """
        logger.info("Closing manual window.")

        self.view.manual_windows.remove(window)
        window.deleteLater()

    def open_periodic_table(self):
        """ Opens periodic table window. """
        logger.info("Opening periodic table window.")

        window = PeriodicTableWidget()
        self.view.periodic_table_windows.append(window)

        window.showMaximized()
        window.window_closed_s.connect(lambda: self.close_periodic_table(window))

    def close_periodic_table(self, window):
        """ Remove reference to periodic table window when closed """
        logger.info("Closed periodic table window.")

        self.view.periodic_table_windows.remove(window)
        window.deleteLater()

    #### OPENING TABS ##################################################
    def open_peakfit(self, detector):
        """ Opens a tab for peakfit. """

        logger.info("Launching peak fitting tab for %s.", detector)
        window = PeakFitWindow(self.view.run, detector, parent=self.view)
        self.view.open_new_tab(window.widget(), f"{detector} Peak Fitting")

    def open_trim(self):
        """ Opens a tab for TRIM. """

        logger.info("Launching TRIM tab.")
        window = TrimWindow()
        self.view.open_new_tab(window.widget(), "TRIM Simulations")

    def open_model_muon_spectrum(self):
        """ Opens a tab for muonic x-ray modelling. """

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

