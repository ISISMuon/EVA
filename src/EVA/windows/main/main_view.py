import logging
from types import NoneType

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QGridLayout,
    QSizePolicy
)

from EVA.core.app import get_app, get_config
logger = logging.getLogger(__name__)

class MainView(QWidget):
    update_all_plots_s = pyqtSignal(NoneType, NoneType)

    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        config = get_config()
        self.detector_list = config["general"]["all_detectors"].split(" ")

        # Set up action bar items
        self.bar = self.parent.menuBar() # since parent is the QMainWindow instance
        self.file_menu = self.bar.addMenu('File')
        self.file_load_default = self.file_menu.addAction('Load default settings')
        self.file_browse_dir = self.file_menu.addAction('Browse to data directory')
        self.file_save = self.file_menu.addAction("Save all settings")


        self.help_menu = self.bar.addMenu('Help')
        self.help_manual = self.help_menu.addAction("Manual")

        # Set up window components
        self.layout = QGridLayout()
        self.setLayout(self.layout)

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
        self.run_number_line_edit.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.run_number_line_edit.setText(config["general"]["run_num"])

        self.get_next_run_button = QPushButton(self)
        self.get_next_run_button.setText('+1')
        self.get_next_run_button.setMinimumWidth(200)
        self.get_next_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.load_next_run_button = QPushButton(self)
        self.load_next_run_button.setText('Load +1')
        self.load_next_run_button.setMinimumWidth(200)
        self.load_next_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.get_prev_run_button = QPushButton(self)
        self.get_prev_run_button.setText('-1')
        self.get_prev_run_button.setMinimumWidth(200)
        self.get_prev_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.load_prev_run_button = QPushButton(self)
        self.load_prev_run_button.setText('Load -1')
        self.load_prev_run_button.setMinimumWidth(200)
        self.load_prev_run_button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

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

        # Store references to all windows in the view
        self.main_window = None
        self.plot_window = None
        self.multiplot_window = None
        self.peakfit_window = None
        self.trim_window = None
        self.trim_fit_window = None
        self.efficiency_correction_window = None
        self.energy_correction_window = None
        self.manual_window = None
        self.muon_spectrum_window = None
        self.periodic_table_window = None


    def set_run_num_line_edit(self, num):
        self.run_number_line_edit.setText(num)

    def get_run_num_line_edit(self):
        run_num = self.run_number_line_edit.text()
        print(run_num)
        return self.run_number_line_edit.text()

    def set_run_num_label(self, run_num):
        self.run_number_label.setText(f"Run Number\t{run_num}")

    def set_comment_labels(self, comment, start, end, events):
        self.comment_label.setText(f"Comment\t{comment} ")
        self.events_label.setText(f"Events\t\t{events} ")
        self.start_label.setText(f"Start Time\t{start} ")
        self.end_label.setText(f"End Time\t{end} ")

    def update_normalisation_menu(self, norm):
        self.norm_counts.setChecked(norm == "counts")
        self.norm_none.setChecked(norm == "none")
        self.norm_events.setChecked(norm == "events")

    def update_plot_detectors_menu(self, plot_which):
        for i, plot_detector in enumerate(plot_which):
            self.plot_detectors_actions[i].setChecked(plot_detector)

    def get_dir(self):
        return QFileDialog.getExistingDirectory(self, "Choose Directory", "C:\\")

    def show_info_box(self, msg):
        _ = QMessageBox.information(parent=self, title="Information", text=msg, buttons=QMessageBox.StandardButton.Ok)

    def show_error_box(self, msg, title="Error"):
        # this will block the program until user presses "ok"
        _ = QMessageBox.critical(self, title, msg,
                                 buttons=QMessageBox.StandardButton.Ok,
                                 defaultButton=QMessageBox.StandardButton.Ok)

    def show_message_box(self, msg, title="Message"):
        # this will block the program until user presses "ok"
        _ = QMessageBox.information(self, title, msg,
                                 buttons=QMessageBox.StandardButton.Ok,
                                 defaultButton=QMessageBox.StandardButton.Ok)



