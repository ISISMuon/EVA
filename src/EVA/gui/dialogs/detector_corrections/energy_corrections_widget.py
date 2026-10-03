from EVA.core.data_structures.run import Run
from EVA.gui.ui_files.energy_correction_window_gui import Ui_Energycorrections

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
)


class EnergyCorrectionsWidget(QDialog, Ui_Energycorrections):
    energy_corrections_applied_s = pyqtSignal(dict)
    widget_closed_s = pyqtSignal(object)

    def __init__(self, run: Run):
        super().__init__()

        self.run = run
        if self.run.energy_corrections:
            self.corrections = self.run.energy_corrections
        else:
            self.corrections = {
                detector: {
                    "e_corr_coeffs": (1.0, 0.0),
                    "use_e_corr": False,
                }
                for detector in self.run.active_detectors
            }

        self.setupUi(self)
        self.setWindowTitle("Energy corrections")

        self.checkboxes = []

        self.correction_table.stretch_horizontal_header()

        self.populate_table()

    def populate_table(self):
        current_corrections = self.corrections

        table_contents = [
            [detector, *settings["e_corr_coeffs"]]
            for detector, settings in current_corrections.items()
        ]

        use_corrections = [
            settings["use_e_corr"]
            for settings in current_corrections.values()
        ]

        self.correction_table.update_contents(table_contents)
        self.setup_table_checkboxes(use_corrections)

    def setup_table_checkboxes(self, init_checkstates: list):
        # Clear the existing references in case the table is repopulated.
        self.checkboxes.clear()

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
            try:
                detector = self.correction_table.item(row, 0).text()

                gradient = float(
                    self.correction_table.item(row, 1).text()
                )
                offset = float(
                    self.correction_table.item(row, 2).text()
                )

                use_e_corr = self.checkboxes[row].isChecked()

                result[detector] = {
                    "e_corr_coeffs": (gradient, offset),
                    "use_e_corr": use_e_corr,
                }
            except (ValueError, AttributeError):
                raise ValueError(
                    f"Invalid energy correction values for detector {detector}."
                )
        return result

    def on_apply(self):
        try:
            corrections = self.get_energy_correction_selections()
            return corrections

        except (ValueError, AttributeError):
            self.display_error_message(
                title="Form error",
                message="Invalid energy corrections in table!",
            )

    def display_error_message(
        self,
        title="Error",
        message="",
        buttons=QMessageBox.StandardButton.Ok,
    ):
        QMessageBox.critical(self, title, message, buttons)

    def display_message(
        self,
        title="Message",
        message="",
        buttons=QMessageBox.StandardButton.Ok,
    ):
        QMessageBox.information(self, title, message, buttons)

    def closeEvent(self, event: QCloseEvent):
        self.dialog_closed_s.emit(event)
        event.accept()