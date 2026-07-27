import json
import logging
import os
from EVA.core.app import get_config
from EVA.gui.windows.detector_grouping.detector_grouping_model import DetectorGroupingModel
from EVA.gui.windows.detector_grouping.detector_grouping_view import DetectorGroupingView

logger = logging.getLogger(__name__)


class DetectorGroupingPresenter:
    def __init__(self, view: DetectorGroupingView, model: DetectorGroupingModel):
        self.view = view
        self.model = model
        self.view.ConfigTable.cellClicked.connect(
            self.append_row_in_layer_table_if_last_row_clicked
        )
        self.view.save_profile_button.clicked.connect(self.save_profile)
        self.updated_combo_box_options(get_config()["general"]["saved_grouping_profiles"].keys())
        current_profile = get_config()["general"]["current_grouping_profile"]
        if current_profile:
            self.view.saved_profile_options_combobox.setCurrentText(current_profile)
            detector_grouping_data = self.model.load_profile(get_config()["general"]["saved_grouping_profiles"][current_profile])
            self.view.ConfigTable.update_contents(detector_grouping_data)
        self.view.saved_profile_options_combobox.currentIndexChanged.connect(self.load_selected_profile)

    def load_selected_profile(self):
        selected_profile = self.view.saved_profile_options_combobox.currentText()
        if selected_profile:
            detector_grouping_data = self.model.load_profile(get_config()["general"]["saved_grouping_profiles"][selected_profile])
            self.view.ConfigTable.update_contents(detector_grouping_data)
            config = get_config()
            config["general"]["current_grouping_profile"] = selected_profile
            config.save_config()
            self.view.profile_changed_s.emit(selected_profile)

    def append_row_in_layer_table_if_last_row_clicked(self, row):
        if row == (self.view.ConfigTable.rowCount() - 1):
            self.view.ConfigTable.append_row()

    def updated_combo_box_options(self, add_items: list):
        self.view.saved_profile_options_combobox.blockSignals(True)
        for item in add_items:
            self.view.saved_profile_options_combobox.addItem(item)
        self.view.saved_profile_options_combobox.blockSignals(False)
        # At first ever instance of creating a profile, load it automatically
        if self.view.saved_profile_options_combobox.count() == 1:
            self.load_selected_profile()
    def save_profile(self):
        """
        Save the current contents of the ConfigTable to a detector grouping profile dictionary.
        """
        duplicate = False
        profile_name = self.view.new_profile_name_line_edit.text()
        if not profile_name:
            self.view.display_error_message(message="Please select a profile name to save.")
            return
        if profile_name in get_config()["general"]["saved_grouping_profiles"]:
            reply = self.view.display_question(message=
                f"A profile named '{profile_name}' already exists. Would you like to overwrite it?"
            )
            if not reply:
                return
            if reply:
                duplicate = True
        data = self.view.ConfigTable.get_contents()
        if len(data) == 0:
            self.view.display_error_message(message="Cannot save an empty profile.")
            return
        groups = {}
        for row in data:
            if not row or not row[0]:
                continue  # skip empty rows

            group_name = row[0].strip()
            if not group_name:
                continue

            detectors = []
            if len(row) > 1 and row[1]:
                detectors = [det.strip() for det in row[1].split(",") if det.strip()]

            groups[group_name] = detectors
        config = get_config()
        config["general"]["saved_grouping_profiles"][profile_name] = groups
        config.save_config()
        logger.info(f"Saved new detector grouping profile: {profile_name}")
        if not duplicate:
            self.updated_combo_box_options(add_items=[profile_name])
