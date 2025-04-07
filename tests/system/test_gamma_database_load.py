from pytestqt.plugin import qapp
from EVA.core.app import get_app

class TestGammaDatabaseLoad:
    def test_number_of_entries_in_gamma_db(self, qapp):
        app = get_app()
        gammas = app.gamma_database

        length = sum([len(sub_list) for sub_list in gammas.values()])
        assert length == 274570, 'unexpected number of gamma energies were loaded'

    def test_number_of_elements_in_gamma_db(self, qapp):
        app = get_app()
        gammas = app.gamma_database

        assert len(gammas) == 118, 'unexpected number of elements were loaded'
