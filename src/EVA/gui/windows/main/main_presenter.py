import logging

from EVA.core.app import get_config
from EVA.core.data_structures.run import Run
from EVA.gui.dialogs.general_settings.settings_dialog import SettingsDialog
from EVA.gui.windows.main.main_model import MainModel
from EVA.gui.windows.main.main_view import MainView
from EVA.gui.windows.manual.manual_window import ManualWindow
from EVA.gui.windows.muonic_xray_simulation.model_spectra_window import ModelSpectraWindow
from EVA.gui.windows.periodic_table.periodic_table_widget import PeriodicTableWidget
from EVA.gui.windows.srim.trim_window import TrimWindow
from EVA.gui.windows.workspace.workspace_window import WorkspaceWindow
from EVA.util.path_handler import get_path

logger = logging.getLogger(__name__)

class MainPresenter:
    """ Presenter for the main window. """
    def __init__(self, view: MainView, model: MainModel):
        """
        Args:
            view: view for main window
            model: model for main window
        """
        self.view = view
        self.model = model

        self.view.set_run_num_line_edit(get_config()["general"]["default_run_num"])

        # Set up action bar connections
        self.view.file_save.triggered.connect(self.save_settings)
        self.view.file_browse_dir.triggered.connect(self.set_default_directory)
        self.view.file_load_default.triggered.connect(self.load_default_config)

        self.view.srim_sim_action.triggered.connect(self.open_trim)
        self.view.periodic_table_action.triggered.connect(self.open_periodic_table)
        self.view.muxray_sim_action.triggered.connect(self.open_model_muon_spectrum)

        self.view.general_settings.triggered.connect(self.open_general_settings_dialog)

        self.view.help_manual.triggered.connect(self.open_manual)

        self.view.get_next_run_button.clicked.connect(self.increment_run_num)
        self.view.load_next_run_button.clicked.connect(lambda: self.increment_run_num(load=True))
        self.view.get_prev_run_button.clicked.connect(self.decrement_run_num)
        self.view.load_prev_run_button.clicked.connect(lambda: self.decrement_run_num(load=True))
        self.view.load_button.clicked.connect(self.load_run_num)

    def save_settings(self):
        """
        Saves current config to file.
        """

        config = get_config()

        if config.is_changed():
            config.save_config()
            self.view.show_message_box(title="Save", msg="Current session has been saved.")
        else:
            self.view.show_message_box(title="Save", msg="No changes have been made since last save.")

    def set_default_directory(self):
        """
        Sets default directory in model.
        """
        new_dir = self.view.get_dir()
        self.model.set_default_directory(new_dir)

    def load_default_config(self):
        """
        Resets current config to defaults.
        """
        config = get_config()
        config.restore_defaults()

        # update the gui
        self.view.set_run_num_line_edit(config["general"]["default_run_num"])

        # reset the loaded run labels
        self.view.set_comment_labels("", "", "", "")
        self.view.set_run_num_label("")

        self.view.show_message_box("Configurations have been restored to defaults.")

    def increment_run_num(self, load: bool=False):
        """
        Increments the run number in the gui.

        Args:
            load: whether to load the new run number or not
        """
        try:
            run_num = int(self.view.get_run_num_line_edit()) + 1
            self.view.set_run_num_line_edit(str(run_num))

            if load:
                self.load_run_num()

        except (ValueError, AttributeError):
            self.view.show_error_box("Invalid run number!")
            return

    def decrement_run_num(self, load: bool=False):
        """
        Decrements the run number in the gui.

        Args:
            load: whether to load the new run number or not
        """
        try:
            run_num = int(self.view.get_run_num_line_edit()) - 1
            self.view.set_run_num_line_edit(str(run_num))

            if load:
                self.load_run_num()

        except (ValueError, AttributeError):
            self.view.show_error_box("Invalid run number!")
            return

    def load_run_num(self):
        """
        Loads current run number and launched workspace.
        """
        try:
            run_num = self.view.get_run_num_line_edit()
        except (ValueError, AttributeError):
            self.view.show_error_box("Invalid run number!")
            return

        flags, run = self.model.load_run(run_num)

        if flags["no_files_found"]: #  no data was loaded - return now
            # Update GUI
            self.view.set_run_num_label(f"No files found for run {run_num} in {get_path(get_config()["general"]["working_directory"])}")
            self.view.set_comment_labels("Comment file not found.", "N/A", "N/A", "N/A")
            return

        self.view.set_run_num_label(run_num)

        if flags["comment_not_found"]: # Comment file was not found
            self.view.set_comment_labels(comment="Comment file not found", start="N/A", end="N/A", events="N/A")

        else: # write comment info to GUI
            comment, start, end, events = self.model.read_comment_data()
            self.view.set_comment_labels(comment, start, end, events)

        if flags["norm_by_spills_error"]:  # normalisation by spills failed
            # display error message to let user know what happened
            err_str = ("Cannot use normalisation by spills when comment file has not been loaded. Normalisation has been "
                       "set to none.")

            self.view.show_error_box(err_str, title="Normalisation error")

        # open workspace
        self.open_workspace(run)

    def open_workspace(self, run: Run):
        """ Opens a new workspace for the loaded run. """
        logger.info("Opening workspace.")

        workspace = WorkspaceWindow(run)
        self.view.workspaces.append(workspace)

        workspace.widget().showMaximized()
        workspace.widget().window_closed_s.connect(lambda: self.close_workspace(workspace))

    def close_workspace(self, workspace: WorkspaceWindow):
        """ Remove reference to workspace when closed """
        logger.info("Closed workspace.")

        self.view.workspaces.remove(workspace)
        workspace.widget().deleteLater()

    def open_general_settings_dialog(self):
        """ Opens the general settings dialog. """
        logger.info("Opening settings dialog.")

        dialog = SettingsDialog()
        self.view.general_settings_dialogs.append(dialog)

        dialog.show()
        dialog.view.dialog_closed_s.connect(lambda: self.close_general_settings_dialog(dialog))

    def close_general_settings_dialog(self, dialog):
        """ Closes settings dialog"""
        logger.info("Closed settings dialog.")

        self.view.general_settings_dialogs.remove(dialog)
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

    def open_trim(self):
        """ Opens a window for TRIM simulations. """
        logger.info("Opening TRIM window.")

        window = TrimWindow()
        self.view.srim_windows.append(window)

        window.showMaximized()
        window.widget().window_closed_s.connect(lambda: self.close_trim(window))

    def close_trim(self, window):
        """ Remove reference to trim window when closed """
        logger.info("Closed TRIM window.")

        self.view.srim_windows.remove(window)
        window.widget().deleteLater()

    def open_model_muon_spectrum(self):
        """ Opens a tab for muonic x-ray modelling. """
        logger.info("Opening muonic x-ray modelling window.")

        window = ModelSpectraWindow()
        self.view.model_spectra_windows.append(window)

        window.showMaximized()
        window.widget().window_closed_s.connect(lambda: self.close_model_muon_spectrum(window))

    def close_model_muon_spectrum(self, window):
        """ Remove reference to mu-xray modelling window when closed """
        logger.info("Closed muonic x-ray modelling window.")

        self.view.model_spectra_windows.remove(window)
        window.widget().deleteLater()

