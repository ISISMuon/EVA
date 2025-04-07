import pytest
from pytestqt.plugin import qapp
from EVA.core.data_searching import get_match
from EVA.core.app import get_app
from tests.system.test_util import load_mudirac_test_db, load_gamma_test_db, load_legacy_test_db

# TODO: add more test parameters
# MUON DATABASE TEST PARAMETERS ###################################

default_peaks_list_mudirac = [
    [1050, 1210],
    [1080]
]

default_sigma_list_mudirac = [10, 5]

target_result_list_mudirac = [
    {"Aa": [1050, 1040, 1060, 1030, 1070, 1020, 1080], "Ab": [1210, 1200, 1220, 1190, 1230, 1180, 1240]},
    {"Aa": [1080, 1070]}
]

default_peaks_list_legacy = [
    #[330.9, 296.5, 92.6, 1253.7, 330.7]
    [1342, 1742]
]

default_sigma_list_legacy = [2]

target_result_list_legacy = [
    {"Aa": [1342.0, 1340.0, 1346.0, 1347.0], "Ab": [1341.0, 1741.0, 1740.0, 1742.3, 1747.0]},
    {"Aa": [1080, 1070]}
    #[{'element': 'Cu', 'energy': 330.9, 'error': 0, 'peak_centre': 330.9, 'transition': 'L(3d->2p)', 'diff': 0}, {'element': 'Mg', 'energy': 296.5, 'error': 0, 'peak_centre': 296.5, 'transition': 'K(2p->1s)', 'diff': 0}, {'element': 'Fe', 'energy': 92.6, 'error': 0, 'peak_centre': 92.6, 'transition': 'M(4f->3d)', 'diff': 0}, {'element': 'Fe', 'energy': 1253.7, 'error': 0, 'peak_centre': 1253.7, 'transition': 'K(2p1/2->1s1/2)', 'diff': 0}, {'element': 'Se', 'energy': 296.3, 'error': 0.45, 'peak_centre': 296.5, 'transition': 'M(7f->3d)', 'diff': 0.19999999999998863}, {'element': 'Cu', 'energy': 330.9, 'error': 0.45, 'peak_centre': 330.7, 'transition': 'L(3d->2p)', 'diff': 0.19999999999998863}, {'element': 'Mn', 'energy': 331.2, 'error': 0.45, 'peak_centre': 330.9, 'transition': 'L(4d->2p)', 'diff': 0.30000000000001137}, {'element': 'Sn', 'energy': 331.2, 'error': 0.45, 'peak_centre': 330.9, 'transition': 'N(8g->4f)', 'diff': 0.30000000000001137}, {'element': 'Mg', 'energy': 93.0, 'error': 0.45, 'peak_centre': 92.6, 'transition': 'L(7d->2p)', 'diff': 0.4000000000000057}, {'element': 'In', 'energy': 331.3, 'error': 0.45, 'peak_centre': 330.9, 'transition': 'M(4f->3d)', 'diff': 0.4000000000000341}, {'element': 'Ni', 'energy': 93.1, 'error': 0.9, 'peak_centre': 92.6, 'transition': 'N(7g->4f)', 'diff': 0.5}, {'element': 'Mn', 'energy': 331.2, 'error': 0.9, 'peak_centre': 330.7, 'transition': 'L(4d->2p)', 'diff': 0.5}, {'element': 'Sn', 'energy': 331.2, 'error': 0.9, 'peak_centre': 330.7, 'transition': 'N(8g->4f)', 'diff': 0.5}, {'element': 'Ce', 'energy': 331.5, 'error': 0.9, 'peak_centre': 330.9, 'transition': 'N(6g->4f)', 'diff': 0.6000000000000227}, {'element': 'In', 'energy': 331.3, 'error': 0.9, 'peak_centre': 330.7, 'transition': 'M(4f->3d)', 'diff': 0.6000000000000227}, {'element': 'Er', 'energy': 295.8, 'error': 0.9, 'peak_centre': 296.5, 'transition': 'N(5g->4f)', 'diff': 0.6999999999999886}, {'element': 'Na', 'energy': 297.2, 'error': 0.9, 'peak_centre': 296.5, 'transition': 'K(3p->1s)', 'diff': 0.6999999999999886}, {'element': 'Ta', 'energy': 295.8, 'error': 0.9, 'peak_centre': 296.5, 'transition': 'O(7h->5g)', 'diff': 0.6999999999999886}, {'element': 'K', 'energy': 93.3, 'error': 0.9, 'peak_centre': 92.6, 'transition': 'M(7f->3d)', 'diff': 0.7000000000000028}, {'element': 'Hf', 'energy': 331.6, 'error': 0.9, 'peak_centre': 330.9, 'transition': 'N(5g->4f)', 'diff': 0.7000000000000455}, {'element': 'V', 'energy': 331.6, 'error': 0.9, 'peak_centre': 330.9, 'transition': 'L(6d->2p)', 'diff': 0.7000000000000455}, {'element': 'Ce', 'energy': 331.5, 'error': 0.9, 'peak_centre': 330.7, 'transition': 'N(6g->4f)', 'diff': 0.8000000000000114}]
]


# GAMMA DATABASE TEST PARAMETERS #################################

default_peaks_list_gamma = [
    [20.500]
]

default_sigma_list_gamma = [0.01]

target_result_list_gamma = [
    [{'isotope': '140Eu', 'energy': 20.5, 'diff': 0.0, 'intensity': 0.0, 'lifetime': '        '}]
]

#################################################################

class TestDatabasesGetMatch:
    # Parametrised test to check if database searches from legacy database matches expected results.
    @pytest.mark.parametrize("default_peaks, default_sigma, target_result",
                             list(zip(default_peaks_list_legacy, default_sigma_list_legacy, target_result_list_legacy)))
    def test_muon_legacy_db_match(self, qapp, default_peaks, default_sigma, target_result):
        # Switch to legacy db
        app = get_app()
        app.muon_database = load_legacy_test_db()

        # Generate input string to test matches
        input_data = list(zip(default_peaks, [default_sigma] * len(default_peaks)))

        res, res1, res2 = get_match.search_muxrays(input_data)
        matches = {}


        for match in res:
            if match["element"] not in matches.keys():
                matches[match["element"]] = [match["energy"]]
            else:
                matches[match["element"]].append(match["energy"])

        app.reset()
        assert matches.keys() == target_result.keys(), 'Data in legacy muon database did not match expected'
        assert all([[energy in target_result[elem] for energy in matches[elem]] for elem in matches]), \
            'Data in legacy muon database did not match expected'

    # Parameterised test to check if database searches from mudirac database matches expected results.
    @pytest.mark.parametrize("default_peaks, default_sigma, target_result",
                             list(zip(default_peaks_list_mudirac, default_sigma_list_mudirac, target_result_list_mudirac)))
    def test_muon_mudirac_db_match(self, qapp, default_peaks, default_sigma, target_result):
        # Switch to mudirac db
        app = get_app()
        app.muon_database = load_mudirac_test_db()

        # Generate input string to test matches
        input_data = list(zip(default_peaks, [default_sigma] * len(default_peaks)))

        res, _, _ = get_match.search_muxrays(input_data)

        matches = {}

        for match in res:
            if match["element"] not in matches.keys():
                matches[match["element"]] = [match["energy"]]
            else:
                matches[match["element"]].append(match["energy"])

        app.reset()
        assert matches.keys() == target_result.keys(), 'Data in mudirac muon database did not match expected'
        assert all([[energy in target_result[elem] for energy in matches[elem]] for elem in matches]), \
            'Data in mudirac muon database did not match expected'


    # Parameterised test to check if database searches from gamma database matches expected results.
    @pytest.mark.parametrize("default_peaks, default_sigma, target_result",
                             list(zip(default_peaks_list_gamma, default_sigma_list_gamma, target_result_list_gamma)))
    def test_gamma_match(self, qapp, default_peaks, default_sigma, target_result):

        # Generate input string to test matches
        input_data = list(zip(default_peaks, [default_sigma] * len(default_peaks)))
        res = get_match.search_gammas(input_data)
        print(res)

        assert res == target_result, 'Data in gamma database did not match expected'