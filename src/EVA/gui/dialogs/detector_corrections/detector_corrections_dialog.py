from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QMessageBox,
    QTabWidget,
)

from EVA.core.data_structures.run import Run

from EVA.gui.dialogs.detector_corrections.energy_corrections_widget import (
    EnergyCorrectionsWidget,
)
from EVA.gui.dialogs.detector_corrections.efficiency_corrections_widget import (
    EfficiencyCorrectionsWidget,
)
from EVA.gui.dialogs.detector_corrections.detector_grouping_widget import (
    DetectorGroupingWidget,
)


class DetectorCorrectionsDialog(QDialog):
    detector_corrections_applied_s = pyqtSignal(dict)
    dialog_closed_s = pyqtSignal()

    def __init__(self, parent, run: Run):
        super().__init__(parent)

        self.run = run

        self.setWindowTitle("Detector Corrections")
        # self.setMinimumSize(800, 600)

        self.init_gui()

    def init_gui(self):
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()

        self.energy_corrections = EnergyCorrectionsWidget(self.run)
        self.efficiency_corrections = EfficiencyCorrectionsWidget(self.run)
        self.detector_grouping = DetectorGroupingWidget()

        self.tabs.addTab(
            self.energy_corrections,
            "Energy Corrections",
        )

        self.tabs.addTab(
            self.efficiency_corrections,
            "Efficiency Corrections",
        )

        self.tabs.addTab(
            self.detector_grouping,
            "Detector Grouping",
        )

        self.button_box = QDialogButtonBox()

        self.button_box.addButton(
            "Apply",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        self.button_box.addButton(
            "Cancel",
            QDialogButtonBox.ButtonRole.RejectRole,
        )

        self.button_box.accepted.connect(self.on_apply)
        self.button_box.rejected.connect(self.on_cancel)

        self.layout.addWidget(
            self.tabs,
            0,
            0,
            1,
            1,
        )

        self.layout.addWidget(
            self.button_box,
            1,
            0,
            1,
            1,
        )

    def on_apply(self):
        try:
            energy_corrections = self.energy_corrections.get_energy_correction_selections()
            efficiency_corrections = (
                self.efficiency_corrections.get_efficiency_correction_selections()
            )
            detector_grouping = self.detector_grouping.get_grouping_selections()

        except ValueError as e:
            self.display_message(
                title="Error",
                message=str(e),
                buttons=QMessageBox.StandardButton.Ok,
            )
            return

        corrections = {
            "energy_corrections": energy_corrections,
            "efficiency_corrections": efficiency_corrections,
            "detector_grouping": detector_grouping,
        }

        self.detector_corrections_applied_s.emit(corrections)

        self.accept()
        self.display_message(
            title="Success", message="Settings were successfully applied."
        )
    def on_cancel(self):
        self.reject()
        self.dialog_closed_s.emit()

    def display_message(
        self, title="Message", message="", buttons=QMessageBox.StandardButton.Ok
    ):
        _ = QMessageBox.information(self, title, message, buttons)
