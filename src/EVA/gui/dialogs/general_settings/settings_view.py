from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent, QColor
from PyQt6.QtWidgets import QDialog, QMessageBox, QLineEdit, QCheckBox, QLabel, QDialogButtonBox, QColorDialog, \
    QFileDialog

from EVA.gui.ui_files.settings_widget_gui import Ui_settings

class SettingsView(QDialog, Ui_settings):
    settings_applied_s = pyqtSignal(dict)
    dialog_closed_s = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.colour_dialog = QColorDialog()

        self.apply_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Apply)

    def open_colour_dialog(self):
        self.colour_dialog.show()

    def set_settings(self, settings: dict):
        self.working_dir_label.setText(settings["working_dir"])
        self.srim_exe_dir_label.setText(settings["srim_exe_dir"])
        self.srim_out_dir_label.setText(settings["srim_out_dir"])
        self.set_fill_colour_preview(settings["fill_colour"])
        self.colour_dialog.setCurrentColor(QColor(settings["fill_colour"]))

    def set_fill_colour_preview(self, colour):
        self.plot_fill_colour_preview.setStyleSheet(f"background-color: {colour}")

    def get_settings(self):
        settings = {
            "srim_exe_dir": self.srim_exe_dir_label.text(),
            "srim_out_dir": self.srim_out_dir_label.text(),
            "fill_colour": self.colour_dialog.currentColor().name(),
            "working_dir": self.working_dir_label.text()
        }

        return settings

    def display_error_message(self, title="Error", message="", buttons=QMessageBox.StandardButton.Ok):
        _ = QMessageBox.critical(self, title, message, buttons)

    def display_message(self, title="Message", message="", buttons=QMessageBox.StandardButton.Ok):
        _ = QMessageBox.information(self, title, message, buttons)

    def get_directory(self):
        dir = QFileDialog.getExistingDirectory(self, "Choose Directory", "C:\\")

        if dir == "":
            return None
        else:
            return dir

    def closeEvent(self, event: QCloseEvent):
        self.dialog_closed_s.emit(event)
        event.accept()
