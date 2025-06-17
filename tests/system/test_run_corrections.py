import numpy as np
from EVA.core.app import get_app
import pytest
from pytestqt.plugin import qapp

from EVA.core.data_loading import load_data
from EVA.core.app import get_config


# Which detectors to use for each test
test_detectors = [[],
                  ["GE1"],
                  ["GE1", "GE2"],
                  ["GE1", "GE2", "GE3"],
                  ["GE1", "GE2", "GE3", "GE4"]]


class TestRunCorrections:
    @pytest.mark.parametrize("e_corr_which", test_detectors)
    def test_energy_correction(self, e_corr_which, qapp):
        wdir = get_config()["general"]["working_directory"]

        e_corr = {}
        for i, detector in enumerate(get_config()["general"]["enabled_detectors"]):
            use_e_corr = detector in e_corr_which

            e_corr[detector] = {
                "e_corr_coeffs": [30.001, 100.555], # random parameters,
                "use_e_corr": use_e_corr
            }

        default_e_corr = get_config()["default_corrections"]["detector_specific"]
        normalisation = get_config()["default_corrections"]["normalisation"]
        binning = get_config()["default_corrections"]["binning"]

        run, _ = load_data.load_run("2630", working_directory=wdir, energy_corrections=default_e_corr,
                                    normalisation=normalisation, binning=binning)

        # energy correction done by EVA
        run.set_corrections(energy_corrections=e_corr)

        # Manual energy correction
        raw = run.get_raw() # get a copy of raw data

        for detector, dataset in raw.items():
            if detector in e_corr_which:
                params = e_corr[detector]["e_corr_coeffs"]
                corrected = raw[detector].x * params[0] + params[1]
            else:
                corrected = raw[detector].x

            assert np.array_equal(corrected, run.data[detector].x), (f"energy correction failed when correcting "
                                                                   f"{" and ".join(e_corr_which)}")