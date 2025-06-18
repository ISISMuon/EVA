import os
import pytest
import numpy as np
from EVA.core.app import get_app, get_config
from EVA.core.data_loading import load_data
from pytestqt.plugin import qapp

# Run containing all data, run with one detector missing, invalid run
run_num_list = ["2630", "3064", "0"]

# Positional list - if file does not exist for a detector, add empty string
filenames_list = [
    ["ral02630.rooth2099.dat", "ral02630.rooth3099.dat", "ral02630.rooth4099.dat", "ral02630.rooth5099.dat"],
    ["ral03064.rooth2099.dat", "ral03064.rooth3099.dat", "ral03064.rooth4099.dat", ""],
    ["", "", "", ""]
]

class TestLoadRun:
    def manual_load(self, filename):
        config = get_config()
        if filename == "":
            return [], [] # return blank arrays if data is missing for the detector

        path = os.path.join(config["general"]["working_directory"], filename)
        xdata, ydata = np.loadtxt(path, delimiter=" ", unpack=True)
        return xdata, ydata

    @pytest.mark.parametrize("run_num, filenames", list(zip(run_num_list, filenames_list)))
    def test_load_run(self, qapp, run_num, filenames):

        wdir = get_config()["general"]["working_directory"]
        corrections = get_config()["default_corrections"]

        run, flags = load_data.load_run(run_num, working_directory=wdir, energy_corrections=corrections["detector_specific"],
                                        normalisation=corrections["normalisation"], binning=corrections["binning"])

        # Check that run is None if no detector data was loaded (invalid run number)
        if all([filename == "" for filename in filenames]):
            assert run.loaded_detectors is not None, "Invalid run was specified but run is not empty"
        else:
            for i, dataset in enumerate(run.get_raw().values()):
                xdata, ydata = self.manual_load(filenames[i])

                assert np.array_equal(dataset.x, xdata) and np.array_equal(dataset.y, ydata)
