import os.path
from configparser import ConfigParser
import logging

from EVA.util.path_handler import get_path

logger = logging.getLogger(__name__)

default_config_path = get_path("src/EVA/core/settings/defaults.ini")
config_path = get_path("src/EVA/core/settings/config.ini")

class Config(object):
    """
    The Config class uses the python built-in module configparser to read and write configurations as .ini files.
    Configparser stores the config as a dictionary, which allows reading and writing to the configuration in memory.
    Any changes in the configuration can be saved to the file using the save_config() function.
    The configparser is stored under the 'parser' attribute of the Config class, but can also be accessed by indexing
    directly into the Config object.
    """
    def __init__(self):
        super().__init__()
        self.default_parser = None
        self._data = None

    def get(self, key):
        return self._data[key]

    def set(self, key, value):
        self._data[key] = value

    def load(self):
        """
        Loads settings from config.ini file.
        """
        self.default_parser = ConfigParser()
        self.default_parser.read(default_config_path)

        # if config.ini does not exist, create new config file from defaults settings
        if not os.path.exists(config_path):
            with open(config_path, "w") as file:
                logger.debug("Creating new configuration file from defaults.ini")
                self.default_parser.write(file)

        # read configurations from config.ini into ConfigParser
        self.read(config_path)
        logger.debug("Loading configuration from config.ini")


    def save_config(self):
        """
        Writes current settings stored in memory to config.ini file.
        """
        with open(config_path, "w") as config_file:
            self.write(config_file)
            config_file.close()

        logger.info("Current configuration has been saved to file.")


    def restore_defaults(self):
        """
        Resets current settings stored in memory to default settings by reading defaults.ini and overwriting each
        key in config dictionary with corresponding key in default config dictionary.
        """
        for section in self.default_parser:
            self[section] = self.default_parser[section]

        logger.info("Configuration has been reset to defaults.")


    def is_changed(self) -> bool:
        """
        Returns:
            Boolean indicating whether config loaded in memory is different to config saved in config.ini.
        """
        temp_parser = ConfigParser()
        temp_parser.read(config_path)

        for section in self.parser:
            if self.parser[section] != temp_parser[section]:
                return True # return True as soon as a difference is found
        return False


    def to_array(self, input_str: str) -> list:
        """
        Args:
            input_str: string to convert to list

        Returns:
            list containing space-separated values in input string.

        Splits space-separated string into a list. Ex: "1 2 3 4" -> ["1", "2", "3", "4"].
        Useful for reading arrays in config,ini as .ini format does not support array data types.
        """
        return input_str.split(" ")

