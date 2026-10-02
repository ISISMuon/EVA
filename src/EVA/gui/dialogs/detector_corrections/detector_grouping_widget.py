import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QWidget,
)

from EVA.core.app import get_config
from EVA.gui.ui_files.detector_grouping_window_gui import Ui_DetectorGrouping


logger = logging.getLogger(__name__)


class DetectorGroupingWidget(QWidget, Ui_DetectorGrouping):
    """
    Detector Grouping configuration widget.

    Handles:
    - Detector grouping table
    - Saved grouping profiles
    - Loading/saving profiles
    - Dynamic table rows
    - Current profile selection
    """

    profile_changed_s = pyqtSignal(str)
    window_closed_s = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)

        self.setWindowTitle("Detector Grouping Configuration - EVA")
        # self.resize(400, 310)

        self.ConfigTable.stretch_horizontal_header()

        # Signals
        self.ConfigTable.cellClicked.connect(
            self.append_row_in_layer_table_if_last_row_clicked
        )

        self.save_profile_button.clicked.connect(
            self.save_profile
        )

        self.saved_profile_options_combobox.currentIndexChanged.connect(
            self.load_selected_profile
        )

        # Load saved profiles
        config = get_config()

        self.update_combo_box_options(
            config["general"]["saved_grouping_profiles"].keys()
        )

        # Load current profile
        current_profile = config["general"]["current_grouping_profile"]
        # if get_config()["general"]["current_grouping_profile"] is not None:
        #     self.current_profile = get_config()["general"]["current_grouping_profile"]
        #     self.view.detector_grouping_profile_label.setText(f"Current Profile: {self.current_profile}")
        # else:
        #     self.current_profile = None
        #     self.view.detector_grouping_profile_label.setText(f"Current Profile: None")
        if current_profile:
            self.saved_profile_options_combobox.setCurrentText(
                current_profile
            )

            detector_grouping_data = self.load_profile(
                config["general"]["saved_grouping_profiles"][
                    current_profile
                ]
            )

            self.ConfigTable.update_contents(
                detector_grouping_data
            )

    def load_profile(self, groups: dict) -> list:
        """
        Convert a detector grouping profile dictionary into
        table-compatible data.
        """
        detector_grouping_data = []

        for group_name, detectors in groups.items():
            detectors_str = ",".join(
                str(detector)
                for detector in detectors
            )

            detector_grouping_data.append(
                [group_name, detectors_str]
            )

        return detector_grouping_data

    def load_selected_profile(self):
        selected_profile = (
            self.saved_profile_options_combobox.currentText()
        )

        if not selected_profile:
            return

        config = get_config()

        detector_grouping_data = self.load_profile(
            config["general"]["saved_grouping_profiles"][
                selected_profile
            ]
        )

        self.ConfigTable.update_contents(
            detector_grouping_data
        )

        config["general"]["current_grouping_profile"] = (
            selected_profile
        )
        config.save_config()

        self.profile_changed_s.emit(selected_profile)

    def update_combo_box_options(self, add_items):
        self.saved_profile_options_combobox.blockSignals(True)

        for item in add_items:
            self.saved_profile_options_combobox.addItem(item)

        self.saved_profile_options_combobox.blockSignals(False)

        # If this is the first profile, load it automatically.
        if self.saved_profile_options_combobox.count() == 1:
            self.load_selected_profile()

    def save_profile(self):
        """
        Save the current contents of ConfigTable as a detector
        grouping profile.
        """
        profile_name = (
            self.new_profile_name_line_edit.text().strip()
        )

        if not profile_name:
            self.display_error_message(
                message="Please select a profile name to save."
            )
            return

        config = get_config()

        saved_profiles = (
            config["general"]["saved_grouping_profiles"]
        )

        duplicate = profile_name in saved_profiles

        if duplicate:
            reply = self.display_question(
                message=(
                    f"A profile named '{profile_name}' already exists. "
                    "Would you like to overwrite it?"
                )
            )

            if not reply:
                return

        data = self.ConfigTable.get_contents()

        if not data:
            self.display_error_message(
                message="Cannot save an empty profile."
            )
            return

        groups = {}

        for row in data:
            if not row or not row[0]:
                continue

            group_name = row[0].strip()

            if not group_name:
                continue

            detectors = []

            if len(row) > 1 and row[1]:
                detectors = [
                    detector.strip()
                    for detector in row[1].split(",")
                    if detector.strip()
                ]

            groups[group_name] = detectors

        saved_profiles[profile_name] = groups

        config.save_config()

        logger.info(
            "Saved new detector grouping profile: %s",
            profile_name,
        )

        if not duplicate:
            self.update_combo_box_options(
                [profile_name]
            )

    def append_row_in_layer_table_if_last_row_clicked(self, row):
        if row == self.ConfigTable.rowCount() - 1:
            self.ConfigTable.append_row()

    def get_grouping_selections(self):
        """
        Returns the current detector grouping profile name.
        """
        config = get_config()
        return config["general"]["current_grouping_profile"]

    def display_error_message(
        self,
        title="Error",
        message="",
        buttons=QMessageBox.StandardButton.Ok,
    ):
        QMessageBox.critical(
            self,
            title,
            message,
            buttons,
        )

    def display_message(
        self,
        title="Message",
        message="",
        buttons=QMessageBox.StandardButton.Ok,
    ):
        QMessageBox.information(
            self,
            title,
            message,
            buttons,
        )

    def display_question(
        self,
        title="Question",
        message="",
        buttons=(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        ),
    ):
        reply = QMessageBox.question(
            self,
            title,
            message,
            buttons,
        )

        return reply == QMessageBox.StandardButton.Yes
