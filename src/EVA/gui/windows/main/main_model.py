import logging
from PyQt6.QtCore import QObject

from EVA.core.app import get_config, get_app
from EVA.core.data_loading import load_data
logger = logging.getLogger(__name__)

class MainModel(QObject):
    def __init__(self):
        super().__init__()
        self.run = None

    def load_run(self, run_num):
        config = get_config()

        # create new record for the run if it has never been loaded before
        working_directory = config["general"]["working_directory"]
        corrections = config.get_run_save(working_directory, run_num)
        energy_corrections = corrections["detector_specific"]
        normalisation = corrections["normalisation"]
        binning = corrections["binning"]
        plot_mode = corrections["plot_mode"]
        prompt_limit = corrections["prompt_limit"]

        run, flags = load_data.load_run(run_num, working_directory, energy_corrections, normalisation, binning, plot_mode, prompt_limit)

        all_detectors = config["general"]["enabled_detectors"]

        if flags["no_files_found"]:  # no data was loaded - return now
            logging.error("No files were found in %s for run %s", config["general"]["working_directory"],
                          run_num)

            return flags, None

        # update run number field in gui and in config
        self.run = run
        config["general"]["default_run_num"] = str(run_num)

        logging.info("Found data for run number %s.", run_num)
        missing_detectors = [det for det in all_detectors if det not in self.run.loaded_detectors]

        if missing_detectors:
            logging.warning("No files were found for detectors %s.", ", ".join(missing_detectors))

        if flags["comment_not_found"]:  # Comment file was not found
            logging.error("No comment file found for run %s", run_num)

        else:  # write comment info to GUI
            logging.info("Found metadata from comment file for run %s", run_num)

        if flags["norm_by_spills_error"]:
            logging.error("Failed to apply normalisation by spills due to missing comment file. Normalisation set to None.")

        return flags, run

    @staticmethod
    def set_default_directory(new_dir):
        config = get_config()
        if new_dir:
            config["general"]["working_directory"] = new_dir
            logger.info("Working directory set to %s.", new_dir)
