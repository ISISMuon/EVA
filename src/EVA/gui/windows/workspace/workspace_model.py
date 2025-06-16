import matplotlib
import numpy as np

from EVA.core.app import get_config
from EVA.core.data_structures.run import normalisation_types
from EVA.core.settings.config import Config


class WorkspaceModel:
    """ Model for handling workspace logic """
    def __init__(self, run):
        """
        Initialise model.

        Args:
            run: run object
        """
        self.run = run
        self.binning = self.run.bin_rate
        self.normalisation = self.run.normalisation

    def on_apply_settings(self, settings: dict):
        """
        Updates normalisation and binning in config and reapplies all corrections to the loaded run.

        Args:
            settings: input from run settings form.

        """
        self.binning = settings.get("binning", self.binning)
        self.normalisation = normalisation_types[settings.get("normalisation", self.normalisation)]

        self.run.set_corrections(normalisation=self.normalisation, bin_rate=self.binning)

    def on_config_changed(self, fields):
        config = get_config()

        normalisation = config["general"]["normalisation"]
        binning = config["general"]["binning"]

        e_corr_which = []
        e_corr_params = {}

        for det, obj in config["detector_settings"].items():
            e_corr_params[det] = obj["e_corr_coeffs"]
            if obj["use_e_corr"]:
                e_corr_which.append(det)

        self.run.set_corrections(e_corr_params, e_corr_which, normalisation, binning)

    def save_run_corrections(self):
        config = get_config()

        working_dir = config["general"]["working_directory"]
        run_num = self.run.run_num

        corrections = {
            "normalisation": self.run.normalisation,
            "binning": self.run.bin_rate,
            "detector_specific": self.run.energy_corrections,
        }

        print(self.run.normalisation)
        print(self.run.bin_rate)

        config["saved_corrections"][working_dir][run_num] = corrections
