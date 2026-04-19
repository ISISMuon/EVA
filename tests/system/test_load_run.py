import os
import h5py
import pytest
import numpy as np
from EVA.core.app import get_config
from EVA.core.data_loading import load_data

# Run containing all data, run with one detector missing, invalid run
brni_run_num_list = ["2630", "3064", "0"]

# Positional list - if file does not exist for a detector, add empty string
brni_filenames_list = [
    [
        "ral02630.rooth2099.dat",
        "ral02630.rooth3099.dat",
        "ral02630.rooth4099.dat",
        "ral02630.rooth5099.dat",
    ],
    ["ral03064.rooth2099.dat", "ral03064.rooth3099.dat", "ral03064.rooth4099.dat", ""],
    ["", "", "", ""],
]
nxs_run_num_list = ["780", "0"]
nxs_filenames_list = ["MUX00000780.nxs", ""]
expected_detectors_list = [["GE6", "GE5", "GE8", "GE7"], []]


class TestLoadRun:
    def manual_load_brni_run(self, filename):
        config = get_config()
        if filename == "":
            return [], []  # return blank arrays if data is missing for the detector

        path = os.path.join(config["general"]["working_directory"], filename)
        xdata, ydata = np.loadtxt(path, delimiter=" ", unpack=True)
        return xdata, ydata

    def manual_load_nxs_run(self, filename):
        config = get_config()
        prompt_data = []
        delayed_data = []
        detector_names = []
        if filename == "":
            return [], []  # return blank arrays if data is missing for the detector
        path = os.path.join(config["general"]["working_directory"], filename)
        data_file = h5py.File(path, "r")

        for i in range(1, 5):
            check_loaded_cond_1 = f"raw_data_1/detector_{i}_energyA/counts"
            check_loaded_cond_2 = f"raw_data_1/detector_{i}_energyHist/energy"

            if (
                data_file[check_loaded_cond_1][()].any()
                or data_file[check_loaded_cond_2][()].any()
            ):
                detector_names.append(
                    data_file[f"raw_data_1/instrument/detector_{i}/name"][()].decode(
                        "utf-8"
                    )
                )

                prompt_energy = data_file[f"raw_data_1/detector_{i}_energyA/energy"]
                prompt_count = data_file[f"raw_data_1/detector_{i}_energyA/counts"]

                delayed_energy = data_file[f"raw_data_1/detector_{i}_energyB/energy"]
                delayed_count = data_file[f"raw_data_1/detector_{i}_energyB/counts"]
                prompt_data.append((prompt_energy[:], prompt_count[:]))
                delayed_data.append((delayed_energy[:], delayed_count[:]))
        return detector_names, prompt_data, delayed_data

    @pytest.mark.parametrize(
        "run_num, filenames", list(zip(brni_run_num_list, brni_filenames_list))
    )
    def test_brni_load_run(self, qapp, run_num, filenames):
        wdir = get_config()["general"]["working_directory"]
        energy_corrections = get_config()["default_corrections"]["detector_specific"]
        normalisation = get_config()["default_corrections"]["normalisation"]
        binning = get_config()["default_corrections"]["binning"]
        plot_mode = get_config()["default_corrections"]["plot_mode"]
        prompt_limit = get_config()["default_corrections"]["prompt_limit"]
        delayed_limit = get_config()["default_corrections"]["delayed_limit"]

        run, _ = load_data.load_run(
            run_num,
            wdir,
            energy_corrections,
            normalisation,
            binning,
            plot_mode,
            prompt_limit,
            delayed_limit,
        )

        # Check that run is 0 if no detector data was loaded (invalid run number)
        if run == 0:
            assert run == 0
        else:
            assert run.loaded_detectors is not None

            for i, dataset in enumerate(run.get_raw().values()):
                xdata, ydata = self.manual_load_brni_run(filenames[i])

                assert np.array_equal(dataset.x, xdata)
                assert np.array_equal(dataset.y, ydata)

    @pytest.mark.parametrize(
        "run_num, filename, expected_detectors",
        list(zip(nxs_run_num_list, nxs_filenames_list, expected_detectors_list)),
    )
    def test_nxs_load_run(self, qapp, run_num, filename, expected_detectors):
        wdir = get_config()["general"]["working_directory"]
        energy_corrections = get_config()["default_corrections"]["detector_specific"]
        normalisation = get_config()["default_corrections"]["normalisation"]
        binning = get_config()["default_corrections"]["binning"]
        plot_mode = get_config()["default_corrections"]["plot_mode"]
        prompt_limit = get_config()["default_corrections"]["prompt_limit"]
        delayed_limit = get_config()["default_corrections"]["delayed_limit"]

        run, flags = load_data.load_run(
            run_num,
            wdir,
            energy_corrections,
            normalisation,
            binning,
            plot_mode,
            prompt_limit,
            delayed_limit,
        )

        # Check that run is 0 if no detector data was loaded (invalid run number)
        if flags["no_files_found"] == 1:
            assert flags["no_files_found"] == 1
        else:
            assert run.loaded_detectors == expected_detectors
            detector_names, prompt_data, delayed_data = self.manual_load_nxs_run(
                filename
            )
            run.set_corrections(plot_mode="IBEX Prompt Spectrum")
            for i, (detector, spectrum) in enumerate(run._raw.items()):
                assert np.array_equal(spectrum.x, prompt_data[i][0])
                assert np.array_equal(spectrum.y, prompt_data[i][1])

            run.set_corrections(plot_mode="IBEX Delayed Spectrum")
            for i, (detector, spectrum) in enumerate(run._raw.items()):
                assert np.array_equal(spectrum.x, delayed_data[i][0])
                assert np.array_equal(spectrum.y, delayed_data[i][1])
