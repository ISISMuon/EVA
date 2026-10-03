from EVA.core.data_structures.run import Run
from EVA.gui.ui_files.efficiency_corrections_gui import Ui_EfficiencyCorrections

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
)


class EfficiencyCorrectionsWidget(QDialog, Ui_EfficiencyCorrections):
    def __init__(self, run: Run):
        super().__init__()

        self.run = run

        self.setupUi(self)
        self.setWindowTitle("Efficiency corrections")
        self.low_energy_label.setText(
            "Low energy correction: "
            "<b>exp</b>(a + b·log(x/100) + c·log²(x/100))"
        )
        self.high_energy_label.setText(
            "High energy correction: "
            "<b>exp</b>(d + e·log(x/1000) + f·log²(x/1000))"
        )
        self.checkboxes = []

        self.correction_table.stretch_horizontal_header()
        if self.run.efficiency_corrections:
            self.corrections = self.run.efficiency_corrections
        else:
            self.corrections = {}
            self.corrections["detectors"] = {
                detector: {
                    "eff_corr_coeffs": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                    "use_eff_corr": False,
                        }
                for detector in self.run.active_detectors
                }
            self.corrections.update(
                {
                    "energy_cutoff": 0.0,
                    "units": "Percentage"
                }
            )
        self.populate_table()

    def populate_table(self):
        self.efficiency_correction_units_combobox.setCurrentText(self.corrections["units"])
        self.cutoff_energy_line_edit.setText(str(self.corrections["energy_cutoff"]))
        table_contents = [
            [detector, *settings["eff_corr_coeffs"]]
            for detector, settings in self.corrections["detectors"].items()
        ]

        use_corrections = [
            settings["use_eff_corr"]
            for settings in self.corrections["detectors"].values()
        ]

        self.correction_table.update_contents(table_contents)
        self.setup_table_checkboxes(use_corrections)

    def setup_table_checkboxes(self, init_checkstates: list):
        # Clear existing checkboxes
        self.checkboxes.clear()

        col = 7
        rows = self.correction_table.rowCount()

        for row in range(rows):
            checkbox = QCheckBox()
            checkbox.setChecked(init_checkstates[row])

            self.correction_table.setCellWidget(row, col, checkbox)
            self.checkboxes.append(checkbox)

    def get_efficiency_correction_selections(self):
        rows = self.correction_table.rowCount()

        result = {"detectors": {}}

        for row in range(rows):
            detector = self.correction_table.item(row, 0).text()

            params = [
                float(self.correction_table.item(row, i).text())
                for i in range(1, 7)
            ]

            use_eff_corr = self.checkboxes[row].isChecked()

            result["detectors"][detector] = {
                "eff_corr_coeffs": params,
                "use_eff_corr": use_eff_corr,
            }
        result["energy_cutoff"] = float(self.cutoff_energy_line_edit.text())
        result["units"] = self.efficiency_correction_units_combobox.currentText()

        return result

    def on_apply(self):
        try:
            corrections = self.get_efficiency_correction_selections()
            return corrections

        except (ValueError, AttributeError):
            self.display_error_message(
                title="Form error",
                message="Invalid efficiency corrections in table!",
            )
    def display_error_message(
        self, title="Error", message="", buttons=QMessageBox.StandardButton.Ok
    ):
        _ = QMessageBox.critical(self, title, message, buttons)