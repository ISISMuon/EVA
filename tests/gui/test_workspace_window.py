
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
run_list = ["780", "2630", "0"]
plot_modes = ["IBEX Prompt Spectrum", "IBEX Delayed Spectrum", "Manual Prompt Spectrum", "Manual Delayed Spectrum"]
normalisation_methods = ["none", "counts", "events"]
class TestLoadWorkspaceWindow:
    @pytest.mark.parametrize(
        "run_num", run_list)
    def test_load_workspace(self, qtbot, run_num):
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
            self.view = self.window._view
            qtbot.addWidget(self.view)
            self.model = self.window._model
            self.window.show()
            assert self.model.run.run_num == run_num
            # self.check_plot_modes(qtbot)
            self.check_normalisation(qtbot)

    def check_plot_modes(self, qtbot):
            if self.run_copy.data_type == "biriani":
                assert self.run_copy.plot_mode == "Biriani Spectrum"
            elif self.run_copy.data_type == "nexus":
                for plot_mode in plot_modes:
                    self.view.nexus_plot_display_combo_box.setCurrentText(plot_mode)
                    qtbot.mouseClick(self.view.apply_run_settings_button, Qt.MouseButton.LeftButton)
                    qtbot.wait(1000)
                    self.run_copy.set_corrections(plot_mode=plot_mode, prompt_limit=2000, delayed_limit=20000000)
                    for i, (run_spectrum, run_copy_spectrum) in enumerate(zip(self.model.run._raw.values(), self.run_copy._raw.values())):
                        assert np.array_equal(run_spectrum.x, run_copy_spectrum.x)
                        assert np.array_equal(run_spectrum.y, run_copy_spectrum.y)

    def check_normalisation(self, qtbot):
            if self.run_copy.data_type == "biriani":
                assert self.run_copy.plot_mode == "Biriani Spectrum"
            elif self.run_copy.data_type == "nexus":
                for i, normalisation in enumerate(normalisation_methods):
                    self.view.nexus_plot_display_combo_box.setCurrentText("IBEX Delayed Spectrum")
                    self.view.normalisation_type_combo_box.setCurrentIndex(i)
                    qtbot.mouseClick(self.view.apply_run_settings_button, Qt.MouseButton.LeftButton)
                    qtbot.wait(1000)
                    self.run_copy.set_corrections(plot_mode="IBEX Delayed Spectrum", normalisation=normalisation)
                    for i, (run_spectrum, run_copy_spectrum) in enumerate(zip(self.model.run._raw.values(), self.run_copy._raw.values())):
                        assert np.array_equal(run_spectrum.x, run_copy_spectrum.x)
                        assert np.array_equal(run_spectrum.y, run_copy_spectrum.y)