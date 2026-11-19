import numpy as np
import pytest
import torch

from EVA.core.app import get_app, get_config
from EVA.core.data_loading import load_data
from EVA.core.ml_identification import element_presence as ep
from EVA.gui.windows.elemental_analysis.elemental_analysis_window import (
    ElementalAnalysisWindow,
)

ELEMENTS = ["Al", "B", "Bi", "C", "Co", "Fe", "Pb", "Si", "W"]


class TestElementIdentification:
    @pytest.fixture(autouse=True)
    def setup(self, qapp, qtbot, tmp_path, monkeypatch):
        # a tiny random-weight model, so the test does not depend on the real trained models
        models_dir = tmp_path / "models"
        folder = models_dir / "test_model"
        folder.mkdir(parents=True)
        np.savez(
            folder / ep.ELEMENTS_LIBRARY_FILENAME, element_order=np.array(ELEMENTS)
        )
        model = ep.CNNPresenceTiny(n_out=len(ELEMENTS))
        with torch.no_grad():
            model(torch.zeros(1, 1, ep.DEFAULT_L))
        torch.save(model.state_dict(), folder / ep.CHECKPOINT_FILENAME)
        monkeypatch.setattr(ep, "MODEL_DIR", models_dir)

        app = get_app()
        if not app._databases_ready:
            with qtbot.waitSignal(app.databases_loaded, timeout=10_000):
                pass
        app.use_mudirac_muon_db()

        config = get_config()
        corrections = config["default_corrections"]
        run, _ = load_data.load_run(
            "2630",
            config["general"]["test_directory"],
            corrections["energy_corrections"],
            corrections["efficiency_corrections"],
            corrections["normalisation"],
            corrections["binning"],
            corrections["plot_mode"],
            corrections["prompt_limit"],
            corrections["delayed_limit"],
        )
        self.run = run

        self.window = ElementalAnalysisWindow(run)
        self.view = self.window.widget()
        self.presenter = self.window._presenter
        qtbot.addWidget(self.view)
        self.window.showMaximized()

        self.errors = []
        monkeypatch.setattr(
            self.view, "display_error_message", lambda **kw: self.errors.append(kw)
        )

    def plotted_detectors(self):
        return [
            d.detector
            for d in self.run.data.values()
            if d.detector in self.run.plot_detectors and d.x.size > 0
        ]

    def test_model_dropdown_lists_installed_models(self):
        combo = self.view.ml_model_select_combo
        assert [combo.itemText(i) for i in range(combo.count())] == ["Test Model"]

    def test_identify_elements_button_fills_results_table(self):
        self.view.identify_elements_button.click()

        assert self.errors == []
        table = self.view.ml_results_table
        expected = self.plotted_detectors()
        assert len(expected) > 0
        assert table.rowCount() == len(expected)
        assert [table.item(r, 0).text() for r in range(table.rowCount())] == expected
        for r in range(table.rowCount()):
            assert table.item(r, 1).text() != ""  # likely elements, or "None"
            assert table.item(r, 2).text() != ""  # top probabilities

    def test_non_spectrum_display_mode_is_refused(self):
        self.run.plot_mode = "Time Plot"
        self.view.identify_elements_button.click()

        assert len(self.errors) == 1
        assert "energy spectrum" in self.errors[0]["message"]
        assert self.view.ml_results_table.rowCount() == 0

    def test_error_shown_when_no_models_installed(self):
        self.presenter.model.ml_models = {}
        self.view.identify_elements_button.click()

        assert len(self.errors) == 1
        assert "No trained ML models" in self.errors[0]["message"]
