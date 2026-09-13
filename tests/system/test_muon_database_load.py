import pytest

from EVA.core.app import get_app


class TestMuonDatabaseLoad:
    # this will run once before all other tests in the class
    @pytest.fixture(autouse=True)
    def setup(self, qapp, qtbot):
        app = get_app()
        if not app._databases_ready:
            with qtbot.waitSignal(app.databases_loaded, timeout=10_000):
                pass

    def test_mudirac_json_loaded(self, qapp):
        app = get_app()
        assert len(app.muon_database) == 10, (
            "Mudirac muonic xray JSON file was not loaded correctly"
        )

    def test_mudirac_correct_number_of_isotopes_loaded(self, qapp):
        app = get_app()
        assert len(app.muon_database["All isotopes"]["All energies"]) == 265, (
            "Incorrect number of isotopes loaded from mudirac muonic xray JSON file"
        )

    def test_load_legacy_json(self, qapp):
        app = get_app()
        app.use_legacy_muon_db()
        db = app.muon_database
        app.reset()
        assert len(db) == 3, "Legacy muonic xray JSON file was not loaded correctly"

    def test_legacy_correct_number_of_isotopes_loaded(self, qapp):
        app = get_app()
        app.use_legacy_muon_db()
        db = app.muon_database
        app.reset()
        assert len(db["All energies"]) == 79, (
            "Incorrect number of elements loaded from legacy muonic xray JSON file"
        )
