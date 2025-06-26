from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialog, QMessageBox, QCheckBox, QDialogButtonBox

from EVA.gui.ui_files.energy_correction_window_gui import Ui_Energycorrections

class EnergyCorrectionsView(QDialog, Ui_Energycorrections):
    energy_corrections_applied_s = pyqtSignal(dict)
    dialog_closed_s = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Energy corrections")
        self.apply_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Apply)

        self.checkboxes = []

        self.correction_table.stretch_horizontal_header()

    def setup_table_checkboxes(self, init_checkstates: list):
        col = 3
        rows = self.correction_table.rowCount()

        for row in range(rows):
            checkbox = QCheckBox()
            checkbox.setChecked(init_checkstates[row])

            self.correction_table.setCellWidget(row, col, checkbox)
            self.checkboxes.append(checkbox)

    def get_energy_correction_selections(self):
        rows = self.correction_table.rowCount()

        result = {}
        for row in range(rows):
            detector = self.correction_table.item(row, 0).text()
            gradient = float(self.correction_table.item(row, 1).text())
            offset = float(self.correction_table.item(row, 2).text())
            apply = self.checkboxes[row].isChecked()

            result[detector] =  {
                "e_corr_coeffs": (gradient, offset),
                "use_e_corr": apply
            }

        return result

    def display_error_message(self, title="Error", message="", buttons=QMessageBox.StandardButton.Ok):
        _ = QMessageBox.critical(self, title, message, buttons)

    def display_message(self, title="Message", message="", buttons=QMessageBox.StandardButton.Ok):
        _ = QMessageBox.information(self, title, message, buttons)

    def closeEvent(self, event: QCloseEvent):
        self.dialog_closed_s.emit(event)
        event.accept()
