import logging
from types import NoneType

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QGridLayout,
    QSizePolicy, QMainWindow, QApplication
)

from EVA.core.app import get_config
from EVA.gui.dialogs.general_settings.settings_dialog import SettingsDialog
from EVA.gui.windows.manual.manual_window import ManualWindow
from EVA.gui.windows.multiplot.multi_plot_window import MultiPlotWindow
from EVA.gui.windows.muonic_xray_simulation.model_spectra_window import ModelSpectraWindow
from EVA.gui.windows.periodic_table.periodic_table_widget import PeriodicTableWidget
from EVA.gui.windows.srim.trim_window import TrimWindow
from EVA.gui.windows.workspace.workspace_window import WorkspaceWindow

logger = logging.getLogger(__name__)

class MainView(QMainWindow):
    """ View class to provide the user interface for the main window. """
    update_all_plots_s = pyqtSignal(NoneType, NoneType)

    workspaces : list[WorkspaceWindow] = []
    model_spectra_windows : list[ModelSpectraWindow] = []
    manual_windows : list[ManualWindow] = []
    multiplot_windows : list[MultiPlotWindow] = []
    srim_windows : list[TrimWindow] = []
    periodic_table_windows : list[PeriodicTableWidget] = []
    general_settings_dialogs : list[SettingsDialog] = []

    def __init__(self):
        """ Initialise gui components. """
        super().__init__()
        self.init_gui()

        self.workspaces = []

    def init_gui(self):
        # Set up action bar items
        self.setWindowTitle("Elemental Analysis")
        self.setFixedSize(QSize(650, 300))

        self.bar = self.menuBar()
        self.file_menu = self.bar.addMenu('File')
        self.file_browse_dir = self.file_menu.addAction('Browse to data directory')


        self.settings_menu = self.bar.addMenu('Settings')
        self.general_settings = self.settings_menu.addAction("General settings")
        self.file_save = self.settings_menu.addAction("Save all settings")
        self.file_load_default = self.settings_menu.addAction('Load default settings')

        self.plotting_menu = self.bar.addMenu("Plotting")
        self.multiplot_action = self.plotting_menu.addAction("Multi-run Plot")

        self.tools_menu = self.bar.addMenu('Tools')
        self.srim_sim_action = self.tools_menu.addAction('SRIM/TRIM Simulation')
        self.periodic_table_action = self.tools_menu.addAction('Periodic Table')
        self.muxray_sim_action = self.tools_menu.addAction("Muonic X-ray Modelling")

        self.help_menu = self.bar.addMenu('Help')
        self.help_manual = self.help_menu.addAction("Manual")

        # Set up window components
        self.layout = QGridLayout()
        self.container = QWidget()
        self.container.setLayout(self.layout)

        self.run_number_label = QLabel(self)
        self.run_number_label.setText("Run Number")
        self.run_number_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.comment_label = QLabel(self)
        self.comment_label.setText("Comment")
        self.comment_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.events_label = QLabel(self)
        self.events_label.setText("Events")
        self.events_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.start_label = QLabel(self)
        self.start_label.setText("Start Time")
        self.start_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.end_label = QLabel(self)
        self.end_label.setText("End Time")
        self.end_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        # setting up the buttons and run number
        self.run_number_line_edit = QLineEdit(self)
        self.run_number_line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.run_number_line_edit.setMinimumWidth(200)
        self.run_number_line_edit.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,
                                                QSizePolicy.Policy.MinimumExpanding)

        self.get_next_run_button = QPushButton(self)
        self.get_next_run_button.setText('+1')
        self.get_next_run_button.setMinimumWidth(200)
        self.get_next_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.load_next_run_button = QPushButton(self)
        self.load_next_run_button.setText('Load +1')
        self.load_next_run_button.setMinimumWidth(200)
        self.load_next_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,
                                                QSizePolicy.Policy.MinimumExpanding)

        self.get_prev_run_button = QPushButton(self)
        self.get_prev_run_button.setText('-1')
        self.get_prev_run_button.setMinimumWidth(200)
        self.get_prev_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.load_prev_run_button = QPushButton(self)
        self.load_prev_run_button.setText('Load -1')
        self.load_prev_run_button.setMinimumWidth(200)
        self.load_prev_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,
                                                QSizePolicy.Policy.MinimumExpanding)

        self.load_button = QPushButton(self)
        self.load_button.setText('Load')
        self.load_button.setMinimumWidth(200)
        self.load_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.layout.addWidget(self.run_number_label, 0, 0, 1, 3)
        self.layout.addWidget(self.comment_label, 1, 0, 1, 3)
        self.layout.addWidget(self.events_label, 2, 0, 1, 3)
        self.layout.addWidget(self.start_label, 3, 0, 1, 3)
        self.layout.addWidget(self.end_label, 4, 0, 1, 3)

        self.layout.addWidget(self.run_number_line_edit, 5, 1)
        self.layout.addWidget(self.get_next_run_button, 5, 2)
        self.layout.addWidget(self.load_next_run_button, 6, 2)
        self.layout.addWidget(self.get_prev_run_button, 5, 0)
        self.layout.addWidget(self.load_prev_run_button, 6, 0)
        self.layout.addWidget(self.load_button, 6, 1)

        self.setCentralWidget(self.container)

    def set_run_num_line_edit(self, num: str):
        self.run_number_line_edit.setText(num)

    def get_run_num_line_edit(self):
        return self.run_number_line_edit.text()

    def set_run_num_label(self, run_num: str):
        self.run_number_label.setText(f"Run Number\t{run_num}")

    def set_comment_labels(self, comment: str, start: str, end: str, events: str):
        self.comment_label.setText(f"Comment\t{comment} ")
        self.events_label.setText(f"Events\t\t{events} ")
        self.start_label.setText(f"Start Time\t{start} ")
        self.end_label.setText(f"End Time\t{end} ")

    def get_dir(self):
        return QFileDialog.getExistingDirectory(self, "Choose Directory", "C:\\")

    def show_error_box(self, msg: str, title: str="Error"):
        # this will block the program until user presses "ok"
        _ = QMessageBox.critical(self, title, msg,
                                 buttons=QMessageBox.StandardButton.Ok,
                                 defaultButton=QMessageBox.StandardButton.Ok)

    def show_message_box(self, msg: str, title: str="Message"):
        # this will block the program until user presses "ok"
        _ = QMessageBox.information(self, title, msg,
                                 buttons=QMessageBox.StandardButton.Ok,
                                 defaultButton=QMessageBox.StandardButton.Ok)

    def show_question_box(self,
                         title: str = "Question",
                         message: str = "",
                         buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes |
                                                               QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                         default_button: QMessageBox.standardButton = QMessageBox.StandardButton.Yes) \
            -> QMessageBox.StandardButton:

        reply = QMessageBox.question(self, title, message, buttons, default_button)

        return reply == QMessageBox.StandardButton.Yes

    def closeEvent(self, event: QCloseEvent):
        #close window cleanly

        logger.debug("Has config been modified? %s", get_config().is_changed())
        if not get_config().is_changed(): # quit immediately if no changes have been made
            event.accept()
            QApplication.quit()
            return

        # Show save prompt window if any changes has been made to the config file
        quit_msg = "Would you like to save your changes?"
        reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
            get_config().save_config()
            logger.debug("User replied yes to close prompt.")
            event.accept()
            QApplication.quit()

        elif reply == QMessageBox.StandardButton.No:
            logger.debug("User replied no to close prompt.")
            event.accept()
            QApplication.quit()

        else:
            event.ignore()
            return
