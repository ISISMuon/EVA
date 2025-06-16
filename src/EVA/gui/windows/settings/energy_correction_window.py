import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QWidget,
    QLineEdit,
    QGridLayout, QMessageBox,
)

logger = logging.getLogger(__name__)

from EVA.core.app import get_app, get_config

class Correction_E(QWidget):
    energycorr_window_closed_s = pyqtSignal(QCloseEvent)

    def __init__(self, parent = None):
        super(Correction_E,self).__init__(parent)

        self.setMaximumSize(850, 500)
        self.setWindowTitle("Energy Correction")

        config = get_config()
        self.detector_list = config["general"]["all_detectors"].split(" ")

        self.layout = QGridLayout()

        self.layout.addWidget(QLabel("Offset"), 0, 1)
        self.layout.addWidget(QLabel("Gradient"), 0, 2)
        self.layout.addWidget(QLabel("Enable\nenergy correction"), 0, 3)

        self.save_buttons = []
        self.apply_checkboxes = []
        self.gradient_line_edits = []
        self.offset_line_edits = []

        for i, detector in enumerate(self.detector_list):
            settings = config[detector]
            offset = settings["e_corr_offset"]
            gradient = settings["e_corr_gradient"]
            apply = settings["use_e_corr"] == "yes"

            # set up check boxes
            checkbox = QCheckBox()
            checkbox.setChecked(apply)
            self.apply_checkboxes.append(checkbox)
            self.apply_checkboxes[i].checkStateChanged.connect(self.on_checkbox_click)

            # set up line edits
            offset_line_edit = QLineEdit(offset)
            gradient_line_edit = QLineEdit(gradient)

            #offset_line_edit.setEnabled(apply)
            #gradient_line_edit.setEnabled(apply)

            self.offset_line_edits.append(offset_line_edit)
            self.gradient_line_edits.append(gradient_line_edit)

            self.layout.addWidget(QLabel(f"Detector {detector}"), i + 1, 0)
            self.layout.addWidget(offset_line_edit, i + 1, 1)
            self.layout.addWidget(gradient_line_edit, i + 1, 2)
            self.layout.addWidget(checkbox, i + 1, 3)


        self.save_button = QPushButton("Apply and close")
        self.save_button.clicked.connect(self.save_detector_settings)
        self.layout.addWidget(self.save_button, len(self.detector_list)+2, 4, 1, -1)

        self.setLayout(self.layout)
        self.show()

    def save_detector_settings(self):
        if not self.validate_form():
            error = "Invalid form input."
            msg = QMessageBox.critical(self, "Input error", error)
            logger.error("Invalid energy correction form data.")
            return

        for i, detector in enumerate(self.detector_list):
            config = get_config()

            offset = self.offset_line_edits[i].text()
            gradient = self.gradient_line_edits[i].text()

            config[detector]["e_corr_offset"] = offset
            config[detector]["e_corr_gradient"] = gradient

            if self.apply_checkboxes[i].isChecked():
                config[detector]["use_e_corr"] = "yes"
            else:
                config[detector]["use_e_corr"] = "no"

        logger.info("Saved current energy corrections.")
        self.close()

    def on_checkbox_click(self):
        """
        for i, checkbox in enumerate(self.apply_checkboxes):
            checked = checkbox.isChecked()
            self.offset_line_edits[i].setEnabled(checked)
            self.gradient_line_edits[i].setEnabled(checked)
        """
        pass

    def validate_form(self):
        for i, detector in enumerate(self.detector_list):
            try:
                grad = float(self.gradient_line_edits[i].text())
                offset = float(self.offset_line_edits[i].text())
            except ValueError:
                return False
        return True

    def closeEvent(self, event):
        self.energycorr_window_closed_s.emit(event) # emit signal to notify mainwindow
