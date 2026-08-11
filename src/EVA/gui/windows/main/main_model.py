import logging
from PyQt6.QtCore import QObject

from EVA.core.app import get_config, get_app
from EVA.core.data_loading import load_data

logger = logging.getLogger(__name__)


class MainModel(QObject):
    def __init__(self):
        super().__init__()
        self.run = None
        self.run_type = "single"

    def load_run(self, run_num):
        config = get_config()

        # create new record for the run if it has never been loaded before
        data_directory = config["general"]["data_directory"]
        corrections = config.get_run_save(data_directory, run_num)
        energy_corrections = corrections["detector_specific"]
        normalisation = corrections["normalisation"]
        binning = corrections["binning"]
        plot_mode = corrections["plot_mode"]
        prompt_limit = corrections["prompt_limit"]
        delayed_limit = corrections["delayed_limit"]

        if self.run_type == "single":
            run, flags = load_data.load_run(
                run_num,
                data_directory,
                energy_corrections,
                normalisation,
                binning,
                plot_mode,
                prompt_limit,
                delayed_limit,
            )

        elif self.run_type == "multi":
            run, flags = load_data.load_run_multi(
                run_num,
                data_directory,
                energy_corrections,
                normalisation,
                binning,
                plot_mode,
                prompt_limit,
                delayed_limit,
            )

        if flags["no_files_found"]:  # no data was loaded - return now
            logging.error(
                "No files were found in %s for run %s",
                config["general"]["data_directory"],
                run_num,
            )

            return flags, None

        # update run number field in gui and in config
        self.run = run
        config["general"]["default_run_num"] = str(run_num)

        logging.info("Found data for run number %s.", run_num)
        logging.info(
            "Data was found for detectors %s.", ", ".join(loaded_detector for loaded_detector in run.loaded_detectors)
        )

        if flags["comment_not_found"]:  # Comment file was not found
            logging.error("No comment file found for run %s", run_num)

        else:  # write comment info to GUI
            logging.info("Found metadata from comment file for run %s", run_num)

        if flags["norm_by_spills_error"]:
            logging.error(
                "Failed to apply normalisation by spills due to missing comment file. Normalisation set to None."
            )

        return flags, run

    @staticmethod
    def set_default_directory(new_dir):
        config = get_config()
        if new_dir:
            config["general"]["data_directory"] = new_dir
            logger.info("Data directory set to %s.", new_dir)
