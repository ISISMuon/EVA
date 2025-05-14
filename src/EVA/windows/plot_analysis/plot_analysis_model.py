import logging
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from PyQt6.QtCore import QObject

from EVA.core.data_searching import get_match, sort_match
from EVA.core.data_structures.detector import DetectorIndices
from EVA.core.peak_finding import find_peaks
from EVA.core.app import get_config
from EVA.core.physics.rebin import numpy_rebin
from EVA.core.plot.plotting import plot_run, Plot_Peak_Location
from EVA.core.physics import rebin

logger = logging.getLogger(__name__)

class PlotAnalysisModel(QObject):
    def __init__(self, run):
        super().__init__()
        self.run = run

        self.mu_xray_search_width = 2
        self.gamma_search_width = 0.5

        self.default_height = 10
        self.default_threshold = 15
        self.default_distance = 1

        self.peakfind_functions = ["SciPy find_peaks()", "SciPy find_peaks() w/ background filter"]
        self.peakfind_selected_function = self.peakfind_functions[1]

        self.peakfind_result = []
        self.peakfind_simplified_result = []

        self.plotted_gamma_lines = {}
        self.plotted_mu_xray_lines = {}

        # generate figure
        self.fig, self.axs = self.plot_run()

    @staticmethod
    def get_plot_detectors():
        all_dets = get_config()["general"]["all_detectors"].split(" ")
        plot_detectors = [det for det in all_dets if get_config()[det]["show_plot"] == "yes"]

        return plot_detectors

    def plot_run(self):
        config = get_config()

        # check config to see which detectors should be loaded
        colour = config["plot"]["fill_colour"]

        return plot_run(self.run, show_detectors=self.get_plot_detectors(), colour=colour)

    def plot_vlines_all_gammas(self, element):
        name = f"{element} (γ)"
        if name in self.plotted_gamma_lines.keys():
            return # skip if element has already been plotted

        res = get_match.search_gammas_single_isotope(element)

        next_colour = self.axs[0]._get_lines.get_next_color() # save next colour so that all lines have the same colour

        energies = [float([match['isotope'], match['energy'], match['intensity'], match['lifetime']][1]) for match in res]

        for energy in energies:
            for i in range(len(self.axs)):
                self.axs[i].axvline(energy, color=next_colour, linestyle='--', label=name)

        self.plotted_gamma_lines[name] = (energies, next_colour)

        return name

    def plot_vlines_single_gammas(self, element, energy):
        name = f"{element} {energy}keV (γ)"
        if name in self.plotted_gamma_lines.keys():
            return # ignore if it's already been plotted

        res = get_match.search_gammas_single_transition(element, energy)
        for match in res:
            rowres = [match['isotope'], match['energy'], match['intensity'], match['lifetime']]
            next_colour = self.axs[i]._get_lines.get_next_color()

            for i in range(len(self.axs)):
                self.axs[i].axvline(
                    float(rowres[1]), color=next_colour, linestyle='--',
                    label=name)

            self.plotted_gamma_lines[name] = (rowres[1], next_colour)
        return name

    def plot_vlines_all_mu_xrays(self, element):
        name = f"{element} (μ)"
        if name in self.plotted_mu_xray_lines.keys():
            return None # ignore if it's already been plotted

        res = get_match.search_muxrays_single_element(element)

        energies = [float([match['element'], match['energy'], match['transition']][1]) for match in res]

        next_colour = self.axs[0]._get_lines.get_next_color()

        for energy in energies:
            for i in range(len(self.axs)):
                self.axs[i].axvline(energy, color=next_colour, linestyle='--', label=name)

        self.plotted_mu_xray_lines[name] = (energies, next_colour)
        return name

    def plot_vlines_single_mu_xrays(self, element, transition):
        name = f"{element} {transition} (μ)"
        if name in self.plotted_mu_xray_lines.keys():
            return None # ignore if it's already been plotted

        res = get_match.search_muxrays_single_transition(element, transition)
        next_colour = self.axs[0]._get_lines.get_next_color()

        for match in res:
            rowres = [match['element'], match['energy'], match['transition']]
            for i in range(len(self.axs)):
                self.axs[i].axvline(
                    float(rowres[1]), color=next_colour, linestyle='--',
                    label=name)

        self.plotted_mu_xray_lines[name] = (rowres[1], next_colour)
        return name

    def remove_mu_xray_line(self, name):
        for i in range(len(self.axs)):

            # search for all lines with label == element
            lines_to_remove = [line for line in self.axs[i].lines if line.get_label() == name]
            num = len(lines_to_remove)
            for j in range(num):
                lines_to_remove[j].remove()

        self.plotted_mu_xray_lines.pop(name)

    def remove_gamma_line(self, name):
        for i in range(len(self.axs)):
            # search for all lines with label == element
            lines_to_remove = [line for line in self.axs[i].lines if line.get_label() == name]
            num = len(lines_to_remove)

            for j in range(num):
                lines_to_remove[j].remove()

        self.plotted_gamma_lines.pop(name)

    def plot_all_current_vlines(self):
        for label, values in self.plotted_mu_xray_lines.items():
            print(label)
            print(values)
            energies, colour = values
            for energy in energies:
                for i in range(len(self.axs)):
                    self.axs[i].axvline(
                        float(energy), color=colour, linestyle='--', label=label)

        for label, values in self.plotted_gamma_lines.items():
            energies, colour = values
            for energy in energies:
                for i in range(len(self.axs)):
                    self.axs[i].axvline(
                        float(energy), color=colour, linestyle='--', label=label)

        self.update_legend()


    def update_legend(self):
        for i in range(len(self.axs)):
            # get all unique labels for the legend to avoid duplicates when plotting multiple lines with same name
            h, l = self.axs[i].get_legend_handles_labels()
            by_label = dict(zip(l, h)) # gets only unique labels

            # remove legend if there are no labels left
            if len(by_label) == 0 and self.axs[i].get_legend() is not None:
                self.axs[i].get_legend().remove()
            else:
                self.axs[i].legend(by_label.values(), by_label.keys(), loc="upper right")

    def search_gammas(self, x):
            default_peaks = [x]
            default_sigma = [self.gamma_search_width] * len(default_peaks)

            input_data = list(zip(default_peaks, default_sigma))

            return get_match.search_gammas(input_data)

    def search_mu_xrays(self, x):
        default_peaks = [x]
        default_sigma = [self.mu_xray_search_width] * len(default_peaks)

        input_data = list(zip(default_peaks, default_sigma))
        return get_match.search_muxrays(input_data)

    def find_peaks(self):
        config = get_config()
        logger.debug("Running peak finding method '%s' with height = %s, threshold = %s, distance = %s.",
                     self.peakfind_selected_function, self.default_height, self.default_threshold, self.default_distance)

        # get selected function
        if self.peakfind_selected_function == self.peakfind_functions[0]: # scipy version
            func = find_peaks.findpeaks
        elif self.peakfind_selected_function == self.peakfind_functions[1]: # custom function
            func = find_peaks.findpeak_with_bck_removed
        else:
            raise ValueError("Invalid peak find method specified!")

        i = 0

        peakfind_res = {}
        result_simplified = []

        for dataset in self.run.data.values():
            # only find peaks in data which is plotted
            if config.parser.getboolean(dataset.detector, "show_plot"):
                peakfind_res[dataset.detector] = {}
                peaks, peaks_pos = func(dataset.x, dataset.y,
                                        self.default_height, self.default_threshold, self.default_distance)

                peak_indices = peaks[0]
                peak_positions = dataset.x[peak_indices]


                # search first once to get all transitions
                default_peaks = peak_positions
                default_sigma = [1] * len(default_peaks)
                input_data = list(zip(default_peaks, default_sigma))
                res_all, _, _, = get_match.search_muxrays(input_data)

                out = sort_match.sort_match(res_all)
                result_simplified.append([dataset.detector, str(dict(list(out.items())))])

                # search then for each peak
                for peak in peak_positions:
                    default_peaks = [peak]

                    default_sigma = [1] * len(default_peaks)
                    input_data = list(zip(default_peaks, default_sigma))
                    res_all, _, _, = get_match.search_muxrays(input_data)
                    peakfind_res[dataset.detector][peak] = res_all

                Plot_Peak_Location(self.axs[i], dataset.x, dataset.y, peak_indices)

                i += 1

        self.peakfind_result = peakfind_res
        self.peakfind_simplified_result = result_simplified

    def remove_plot_markers(self):
        for ax in self.axs:
            for coll in ax.collections:
                # delete every collection except the plotted data which is a PolyCollection
                if not isinstance(coll, matplotlib.collections.PolyCollection):
                    coll.remove()


    def update_detector_plot_selection(self, show_detector, detector):
        # generate figure
        config = get_config()

        if show_detector:
            config[detector]["show_plot"] = "yes"
            logger.debug("Enabled %s for plotting.", detector)
        else:
            config[detector]["show_plot"] = "no"
            logger.debug("Disabled %s for plotting.", detector)

        self.fig, self.axs = self.plot_run()
        self.plot_all_current_vlines()

