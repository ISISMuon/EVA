import matplotlib.text
import numpy as np
import pytest

from pandas.core.dtypes.missing import array_equals
from EVA.core.physics.functions import gaussian
from EVA.core.data_searching.get_match import search_muxrays_single_element
from EVA.gui.windows.muonic_xray_simulation.model_spectra_model import ModelSpectraModel

base_test = {
    "elements": ["Ag"],
    "proportions": [1],
    "detectors": ["GE1"],
    "show_primary": True,
    "show_secondary": True
}

class TestModelSpectrumModel:
    # this will run once before all other tests in the class
    @pytest.fixture(autouse=True)
    def setup(self):
        # create new model at beginning of test
        self.model = ModelSpectraModel()

    def test_correct_data_fetched(self):
        test = base_test.copy()
        test["elements"] = ["Au", "Fe", "Zn", "Hg", "Pb"]
        test["proportions"] = [1, 1, 1, 1, 1]

        self.model.model_spectrum(**test)

        get_match_transitions = []
        for i, element in enumerate(test["elements"]):
            matches = search_muxrays_single_element(element)
            get_match_transitions += [[match["transition"], match["energy"]] for match in matches]

        modelled_transitions = self.model.all_transitions[0]
        for j, transition in enumerate(modelled_transitions):
            modelled_transition = [transition["name"], float(transition["E"])]

        assert any(transition["name"] == m[0] and transition["E"] == pytest.approx(m[1], rel=1e-5)
                for m in get_match_transitions), \
                f"Missing transition for {transition['element']}: {modelled_transition}"

    def test_linear_sigma_model(self):
        sigma_params = np.loadtxt("src/EVA/databases/detectors/energy_resolution_linear.txt",
                                  skiprows=1, delimiter=",")
        def line(x, m, c):
            return m * x + c

        # Pre-calculcated values
        energies = [10, 100, 1000, 200]
        detectors = ["GE1", "GE2", "GE3", "GE4"]

        for i, detector in enumerate(detectors):
            for energy in energies:
                sigma = self.model.calculate_sigma("linear", energy, detector)

                intercept = sigma_params[i][1]
                slope = sigma_params[i][2]
                sigma2 = line(energy, slope, intercept) / (2 * np.sqrt(2 * np.log(2))) # converting from fwhm to sigma

                assert round(sigma, 6) == round(sigma2, 6)

    def test_quadratic_sigma_model(self):
        sigma_params = np.loadtxt("src/EVA/databases/detectors/energy_resolution_quadratic.txt",
                                  skiprows=1, delimiter=",")
        def quadratic(x, a, b, c):
            return a * x * x + b * x + c

        # Pre-calculcated values
        energies = [10, 100, 1000, 200]
        detectors = ["GE1", "GE2", "GE3", "GE4"]

        for i, detector in enumerate(detectors):
            for energy in energies:
                sigma = self.model.calculate_sigma("quadratic", energy, detector)

                a = sigma_params[i][3]
                b = sigma_params[i][2]
                c = sigma_params[i][1]

                sigma2 = quadratic(energy, a, b, c) / (2 * np.sqrt(2 * np.log(2))) # converting from fwhm to sigma

                assert round(sigma, 6) == round(sigma2, 6)

    def test_gaussian(self):
        test = base_test
        self.model.model_spectrum(**test)

        spectrum = self.model.all_spectra[0]

        total_curve = np.zeros_like(spectrum.x)
        for transition in self.model.all_transitions[0]:
            total_curve += (transition["weights"] * gaussian(spectrum.x, mean=transition["E"],
                                                             sigma=transition["sigma"], intensity=transition["intensity"]))

        assert array_equals(spectrum.y, total_curve), "Incorrect Gaussian calculated"

    @pytest.mark.parametrize("detectors", [["GE1"], ["GE1", "GE2", "GE3", "GE4"], ["GE1", "GE3"], ["GE2", "GE4"]])
    def test_figure_generated(self, detectors):
        test = base_test.copy()
        test["detectors"] = detectors

        fig, axs = self.model.model_spectrum(**test)

        assert len(self.model.all_spectra) == len(test["detectors"]), "Incorrect number of detectors were simulated"

        for i, detector in enumerate(detectors):
            ax = axs[i] if len(detectors) != 1 else axs

            ydata = ax.lines[0].get_ydata()
            xdata = ax.lines[0].get_xdata()

            spectrum = self.model.all_spectra[i]
            assert spectrum.detector == detector, "Incorrect detectors were simulated for"

            assert np.array_equal(spectrum.x, xdata), "Incorrect xdata plotted"
            assert np.array_equal(spectrum.y, ydata), "Incorrect ydata plotted"


    @pytest.mark.parametrize("notation", [0, 1, 2])
    def test_plot_components(self, notation):
        test = base_test.copy()
        test["show_components"] = True
        test["notation"] = notation

        fig, ax = self.model.model_spectrum(**test)

        element = test["elements"][0]
        transitions = {result["transition"]: result["energy"] for result in search_muxrays_single_element(element)}

        assert len(ax.lines) == len(transitions) + 1, "Not all transitions were plotted"

        # get all text items
        text_labels = [child for child in ax.get_children() if isinstance(child, matplotlib.text.Text)]

        # filter out only peak labels
        peak_labels = {label.get_text()[3:]: float(label.get_position()[0]) for label in text_labels if label.get_text()[:2] == element}

        # check that all transitions for the given element has a label (unless notation is siegbahn)
        if notation != 0:
            assert len(peak_labels) == len(transitions), "incorrect number of labels plotted"

        # if notation is set to siegbahn (which does not have labels for all peaks)
        if notation == 0:
            for spec_name in transitions:
                siegbahn_name = self.model.notations[spec_name][1]

                # only assert if siegbahn name exists for that peak and that peak is in spectrum
                if spec_name in transitions.keys() and siegbahn_name != "":
                    # the matplotlib labels have $ signs in front of them to be rendered as mathtext
                    label_name = f"${siegbahn_name}$"
                    assert transitions[spec_name] == peak_labels[label_name], \
                        "label was not plotted at correct position"

        # if notation is set to spectroscopic
        if notation == 1:
            for spec_name in peak_labels:
                assert peak_labels[spec_name] == transitions[spec_name], \
                    "label was not plotted at correct position"

        # if notation is set to iupac
        if notation == 2:
            for spec_name in transitions:
                iupac_name = self.model.notations[spec_name][0]

                # if peak is in labels
                if spec_name in transitions.keys():
                    assert transitions[spec_name] == peak_labels[iupac_name], \
                        "label was not plotted at correct position"
