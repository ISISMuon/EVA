import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QWidget,
    QLineEdit,
    QGridLayout,
    QMessageBox
)

logger = logging.getLogger(__name__)

from EVA.core.app import get_config

class Correction_Eff(QWidget):
    effcorr_window_closed_s = pyqtSignal(QCloseEvent)
    def __init__(self, parent = None):
        super().__init__(parent)

        self.setMaximumSize(1200, 500)
        self.setWindowTitle("Efficiency Correction ")

        config = get_config()
        self.detector_list = config["general"]["all_detectors"].split(" ")

        self.layout = QGridLayout()

        self.layout.addWidget(QLabel("Enable efficiency\ncorrection"), 0, 6)

        self.param_names = ["P0", "P1", "P2", "P3", "P4"]
        self.param_line_edits = []
        self.checkboxes = []

        self.effcorr_window_closed_s.connect(self.test)

        for i, param in enumerate(self.param_names):
            self.layout.addWidget(QLabel(param), 0, i + 1)

        for i, detector in enumerate(self.detector_list):
            settings = config[detector]
            current_params = settings["eff_corr_coeffs"].split(" ")
            apply = settings["use_eff_corr"] == "yes"

            self.layout.addWidget(QLabel(f"Detector {detector}"), i+1, 0)

            checkbox = QCheckBox()
            checkbox.setChecked(apply)
            checkbox.checkStateChanged.connect(self.on_checkbox_state_change)
            self.checkboxes.append(checkbox)
            self.layout.addWidget(checkbox, i + 1, 6)

            detector_param_line_edits = []
            for j, param in enumerate(self.param_names):
                param_line_edit = QLineEdit(current_params[j])
                param_line_edit.setMaximumWidth(70)
                #param_line_edit.setEnabled(settings["use_eff_corr"] == "yes")
                detector_param_line_edits.append(param_line_edit)
                self.layout.addWidget(param_line_edit, i+1, j + 1)

            self.param_line_edits.append(detector_param_line_edits)

        self.save_button = QPushButton("Apply and close")
        self.save_button.clicked.connect(self.save_settings)

        self.layout.addWidget(self.save_button, len(self.detector_list)+1, 7, 1, -1)

        self.setLayout(self.layout)
        self.show()
        logger.debug("Efficiency window initialised.")

    def test(self):
        logger.info("works!")

    def save_settings(self):
        if not self.validate_form():
            error = "Invalid form input."
            _ = QMessageBox.critical(self, "Input error", error)
            logger.error("Invalid efficiency correction form data.")
            return

        config = get_config()
        for i, detector in enumerate(self.detector_list):
            params = []
            for j, param in enumerate(self.param_line_edits[i]):
                params.append(f"{param.text()}")

            paramstr = " ".join(params)

            config[detector]["eff_corr_coeffs"] = paramstr

            if self.checkboxes[i].isChecked():
                config[detector]["use_eff_corr"] = "yes"
            else:
                config[detector]["use_eff_corr"] = "no"

        logger.info("Saved current efficiency corrections.")

    def closeEvent(self, event):
        self.effcorr_window_closed_s.emit(event) # emit signal to notify mainwindow


    def validate_form(self):
        for i, _ in enumerate(self.detector_list):
            for j, param in enumerate(self.param_line_edits[i]):
                try:
                    p = float(param.text())
                except ValueError:
                    return False
        return True

    def on_checkbox_state_change(self):
        """
        for i, box in enumerate(self.checkboxes):
            checked = box.isChecked()
            for j, param in enumerate(self.param_line_edits[i]):
                param.setEnabled(checked)
        """
        pass

