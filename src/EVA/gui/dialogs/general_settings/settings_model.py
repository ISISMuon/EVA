import logging
from EVA.core.app import get_config

logger = logging.getLogger(__name__)


class SettingsModel:
    def __init__(self):
        pass

    def apply_settings(self, settings: dict):
        config = get_config()

        config["general"]["working_directory"] = settings["general"][
            "working_directory"
        ]
        config["plot"]["fill_colour"] = settings["plot"]["fill_colour"]

        config["SRIM"]["installation_directory"] = settings["SRIM"][
            "installation_directory"
        ]
        config["SRIM"]["output_directory"] = settings["SRIM"]["output_directory"]

        logger.debug("Applied settings: %s", settings)
