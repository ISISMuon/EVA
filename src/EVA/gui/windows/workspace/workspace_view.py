from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QWidget, QMainWindow, QMessageBox, QTabBar, QFileDialog, QDialog

from EVA.core.data_structures.run import Run
from EVA.gui.dialogs.energy_corrections.energy_corrections_dialog import EnergyCorrectionsDialog
from EVA.gui.dialogs.general_settings.settings_dialog import SettingsDialog
from EVA.gui.ui_files.workspace_nxs_gui import Ui_workspace
from EVA.gui.windows.elemental_analysis.elemental_analysis_window import ElementalAnalysisWindow
from EVA.gui.windows.manual.manual_window import ManualWindow
from EVA.gui.windows.periodic_table.periodic_table_widget import PeriodicTableWidget
from EVA.util.path_handler import get_path

class WorkspaceView(Ui_workspace, QMainWindow):
    """
    View class to provide the gui for the workspaces
    """
    manual_windows : list[ManualWindow] = []
    periodic_table_windows : list[PeriodicTableWidget] = []
    general_settings_dialogs : list[SettingsDialog] = []
    energy_corrections_dialogs : list[EnergyCorrectionsDialog] = []

    replot_spectra_s = pyqtSignal()
    update_plot_fill_colour_s = pyqtSignal()
    update_detector_plot_selection_s = pyqtSignal()
    save_and_close_requested_s = pyqtSignal(QCloseEvent)
    window_closed_s = pyqtSignal(object)

    def __init__(self, run: Run):
        """
        Args:
            run: Run object for the workspace
        """
        super().__init__()
        self.run = run

        self.setupUi(self)
        self.setWindowTitle(f"Workspace {run.run_num} - EVA")

        self.detector_list = list(run.data.keys())

        self.layout().setContentsMargins(0, 0, 0, 0)

        # Set up action bar items
        self.peakfit_menu_actions = []

        for detector in self.detector_list:
            action = self.peak_fit_menu.addAction(detector)
            self.peakfit_menu_actions.append(action)

        # Store references to all windows in the view
        self.set_run_info()

        self.binning_spin_box.setSuffix("x")

        # hide the logbook for now (not implemented)
        self.logbook_group_box.hide()

        # initialise elemental analysis widget
        self.elemental_analysis_widget = ElementalAnalysisWindow(parent=self, run=run)
        self.open_new_tab(self.elemental_analysis_widget.widget(), "Elemental Analysis", closable=False)

    def display_error_message(self, message: str = "", title: str = "Error",
                              buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok):
        """ Displays given error message """

        _ = QMessageBox.critical(self, title, message, buttons)

    def display_message(self, message: str = "", title: str = "Message",
                              buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok):
        """ Displays given message """

        _ = QMessageBox.information(self, title, message, buttons)

    def display_question(self, title: str = "", message: str = "",
                         buttons: QMessageBox.standardButton =
                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                         default_button: QMessageBox.standardButton = QMessageBox.StandardButton.Yes) \
            -> QMessageBox.StandardButton:

        reply = QMessageBox.question(self, title, message, buttons, default_button)

        return reply

    def get_dir(self):
        """ Opens file dialog window """
        return QFileDialog.getExistingDirectory(self, "Choose Directory", "C:\\")

    def open_new_tab(self, widget: QWidget, name: str = "", closable: bool = True):
        """
        Opens a new tab in the tab area.

        Args:
            widget: widget to embed in tab
            name: title of tab
            closable: allow tab to be closed
        """

        widget.layout().setContentsMargins(0,0,0,0)

        ix = self.tabWidget.addTab(widget, name)
        self.tabWidget.setCurrentIndex(ix)

        if not closable:
            self.tabWidget.tabBar().tabButton(ix, QTabBar.ButtonPosition.RightSide).deleteLater()
            self.tabWidget.tabBar().setTabButton(ix, QTabBar.ButtonPosition.RightSide, None)

    def close_tab(self, i: int):
        """
        Opens a prompt to the user and closes the targeted tab is user accepts.

        Args:
            i: index of tab to close
        """

        response = QMessageBox.question(self, "Close tab", "Are you sure you want to close this tab?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)

        if not response == QMessageBox.StandardButton.Yes:
            return

        widget = self.tabWidget.widget(i)
        self.tabWidget.removeTab(i)

        widget.close()

    def set_run_info(self):
        """
        Updates the run info in the view.
        """

        mapping = dict.fromkeys(range(32))
        start = self.run.start_time.translate(mapping)[21:]
        end = self.run.end_time.translate(mapping)[21:]
        events = self.run.events_str.translate(mapping)[20:]
        comment = self.run.comment.translate(mapping)[11:]

        run_str = f"Run number: {self.run.run_num}\n\n{comment}\nEvents:{events}\n\nStart time:\n{start}\n\nEnd time:\n{end}"
        """
        self.run_number_label.setText(f"Run number {self.run.run_num}")
        self.time_label.setText(f"Start time {self.run.start_time}, End time {self.run.end_time}")
        self.events_label.setText(f"Events {self.run.events_str}")
        """
        self.comment_text.setText(f"{run_str}")

        """
        # lastly, resize all columns
        self.treeWidget.resizeColumnToContents(0)
        self.treeWidget.resizeColumnToContents(1)
        self.treeWidget.resizeColumnToContents(2)
        self.treeWidget.resizeColumnToContents(3)
        """

    def closeEvent(self, event: QCloseEvent):
        self.save_and_close_requested_s.emit(event)
