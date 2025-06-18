import os.path
import json
import logging
from copy import deepcopy

from PyQt6.QtCore import QObject, pyqtSignal

from EVA.util.path_handler import get_path

logger = logging.getLogger(__name__)

default_config_path = get_path("src/EVA/core/settings/defaults.json")
config_path = get_path("src/EVA/core/settings/config.json")

class Config(QObject):
    config_modified_s = pyqtSignal(dict)

    """
    The config class manages reading and writing all settings to file.
    """
    def __init__(self):
        super().__init__()
        with open(default_config_path, "r") as default_file:
            self._defaults = json.load(default_file)

        # if config.json does not exist, create new config file from defaults settings
        if not os.path.exists(config_path):
            self._data = deepcopy(self._defaults)
            with open(config_path, "w") as config_file:
                logger.debug("Creating new configuration file from defaults.json")
                json.dump(self._defaults, config_file, indent=4)
        else:
            with open(config_path, "r") as file:
                self._data = json.load(file)

    def __getitem__(self, item):
        return self._data[item]

    def get_run_save(self, working_dir, run_num):
        default_corrections = self._data["default_corrections"]
        saved_corrections = self._data["saved_corrections"]

        if working_dir in saved_corrections.keys():
            if run_num in saved_corrections[working_dir].keys():
                return self._data["saved_corrections"][working_dir][run_num]
            else:
                self._data["saved_corrections"][working_dir][run_num] = default_corrections
        else:
            self._data["saved_corrections"][working_dir] = {
               run_num: default_corrections
            }

        return self._data["saved_corrections"][working_dir][run_num]




    def save_config(self):
        """
        Writes current settings stored in memory to config.json file.
        """
        with open(config_path, "w") as config_file:
            json.dump(self._data, config_file, indent=4)

        logger.info("Current configuration has been saved to file.")

    def restore_defaults(self):
        """
        Resets current settings stored in memory to default settings.
        """
        self._data = deepcopy(self._defaults)

        logger.info("Configuration has been reset to defaults.")


    def is_changed(self) -> bool:
        """
        Returns:
            Boolean indicating whether config loaded in memory is different to config saved in config.ini.
        """

        with open(config_path, "r") as file:
            config_in_file = json.load(file)

        return not (config_in_file == self._data)

