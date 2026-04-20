import matplotlib
import pytest
import numpy as np
import copy
from EVA.core.app import get_app, get_config
from EVA.core.data_loading import load_data
from EVA.core.data_structures.spectrum_nexus import SpectrumNexus
from EVA.gui.windows.workspace.workspace_window import WorkspaceWindow
from gc import get_referrers
from PyQt6.QtCore import Qt
from pytestqt.plugin import qtbot
from matplotlib.backend_bases import MouseButton
from unittest.mock import MagicMock

run_list = ["780", "2630", "0"]
plot_modes = [["IBEX Prompt Spectrum", 0],["IBEX Delayed Spectrum", 1], ["Manual Prompt Spectrum", 2], ["Manual Delayed Spectrum", 3]]
normalisation_methods = [["none", 0], ["counts", 1], ["events", 2]]
bin_values = [0.5, 2]


class TestLoadWorkspaceWindow:
    @pytest.mark.parametrize("run_num", run_list)
    @pytest.mark.parametrize("test_normalisation", normalisation_methods)
    @pytest.mark.parametrize("test_binning", bin_values)
    @pytest.mark.parametrize("test_plot_mode", plot_modes)
    def test_load_workspace(
        self, qtbot, run_num, test_normalisation, test_binning, test_plot_mode,
    ):
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
        self.run_copy, _ = load_data.load_run(
            run_num,
            wdir,
            energy_corrections,
            normalisation,
            binning,
            plot_mode,
            prompt_limit,
            delayed_limit,
        )

        if flags["no_files_found"]:
            assert flags["no_files_found"]
        else:
            self.window = WorkspaceWindow(run)
            self.view = self.window.widget()
            self.view.display_error_message = MagicMock()
            qtbot.addWidget(self.view)
            self.model = self.window._model
            self.window.show()
            qtbot.wait(500)
            assert self.model.run.run_num == run_num
            self.view.nexus_plot_display_combo_box.setCurrentIndex(test_plot_mode[1])
            self.view.normalisation_type_combo_box.setCurrentIndex(test_normalisation[1])
            self.view.binning_spin_box.setValue(test_binning)
            qtbot.mouseClick(
                self.view.apply_run_settings_button, Qt.MouseButton.LeftButton
            )
            qtbot.wait(500)
            self.run_copy.set_corrections(
                plot_mode=test_plot_mode[0],
                normalisation=test_normalisation[0],
                bin_rate=float(test_binning),
                prompt_limit=2000,
                delayed_limit=20000000,
            )
            # Check if run metadata is the same as input (if the original run matches input, the copy would also match as it uses the same set_corrections method)
            assert self.model.run.normalisation == test_normalisation[0]
            assert self.model.run.bin_rate == test_binning
            # Also check if extra parameters got updated in Nexus runs
            if self.model.run.data_type == "nexus":
                assert self.model.run.plot_mode == test_plot_mode[0]
                assert self.model.run.prompt_limit == 2000
                assert self.model.run.delayed_limit == 20000000

            for i, (run_spectrum, run_copy_spectrum) in enumerate(
                zip(self.model.run._raw.values(), self.run_copy._raw.values())
            ):
                assert np.array_equal(run_spectrum.x, run_copy_spectrum.x)
                assert np.array_equal(run_spectrum.y, run_copy_spectrum.y)
            matplotlib.pyplot.close()
