import json
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTabWidget,
)

from EVA.core.app import get_config
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
        self.setMinimumSize(500, 400)

        self.init_gui()
        self.load_settings_button.clicked.connect(self.load_settings)
        self.export_settings_button.clicked.connect(self.export_settings)

    def init_gui(self):
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        # Settings buttons
        self.load_settings_button = QPushButton("Load Settings")
        self.export_settings_button = QPushButton("Export Settings")

        self.settings_button_layout = QHBoxLayout()
        self.settings_button_layout.addWidget(self.load_settings_button)
        self.settings_button_layout.addWidget(self.export_settings_button)
        self.settings_button_layout.addStretch()
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

    def fetch_corrections(self):
        try:
            energy_corrections = self.energy_corrections.get_energy_correction_selections()
            efficiency_corrections = (
                self.efficiency_corrections.get_efficiency_correction_selections()
            )
            profile_name, profile_data = self.detector_grouping.get_grouping_selections()

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
            "detector_grouping": {"profile_name": profile_name, "profile_data": profile_data},
        }
        return corrections

    def on_apply(self):
        corrections = self.fetch_corrections()
        self.detector_corrections_applied_s.emit(corrections)

        self.accept()
        self.display_message(
            title="Success", message="Settings were successfully applied."
        )
    def on_cancel(self):
        self.reject()
        self.dialog_closed_s.emit()

    def export_settings(self):
        corrections = self.fetch_corrections()
        def_dir = get_config()["general"]["working_directory"]
        save_path = self.get_save_file_path(default_dir=def_dir, file_filter="JSON Files (*.json)", caption="Export Settings", default_extension=".json")
        with open(save_path, "w") as f:
            json.dump(corrections, f, indent=4)

    def load_settings(self):
        def_dir = get_config()["general"]["working_directory"]
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Settings", directory=def_dir, filter="JSON Files (*.json)"
        )
        if not file_path:
            return

        with open(file_path, "r") as f:
            corrections = json.load(f)

        self.energy_corrections.populate_table(corrections["energy_corrections"])
        self.efficiency_corrections.populate_table(corrections["efficiency_corrections"])
        self.detector_grouping.add_profile(
            profile_name=corrections["detector_grouping"]["profile_name"],
            profile_data=corrections["detector_grouping"]["profile_data"]
        )
    def get_save_file_path(
        self,
        default_dir: str,
        file_filter: str,
        caption="Save File",
        default_extension: str = None,
    ) -> str:
        file_path, _ = QFileDialog.getSaveFileName(
            self, caption, directory=default_dir, filter=file_filter
        )
        if file_path and default_extension:
            if not file_path.lower().endswith(default_extension.lower()):
                file_path += default_extension
        if file_path:
            return file_path
        return ""

    def display_message(
        self, title="Message", message="", buttons=QMessageBox.StandardButton.Ok
    ):
        _ = QMessageBox.information(self, title, message, buttons)
