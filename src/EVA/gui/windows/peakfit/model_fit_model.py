import json
import time
import logging
from copy import deepcopy

import numpy as np
from PyQt6.QtCore import QObject
from matplotlib import pyplot as plt

from EVA.core.fitting import fit_data
from EVA.core.plot.plotting import replot_run, replot_run_residual
from EVA.util.trim_data import Trimdata

from EVA.core.app import get_config

from EVA.core.plot import plotting

logger = logging.getLogger(__name__)

class ModelFitModel(QObject):
    def __init__(self, run, detector, parent=None):
        super().__init__()

        # Get loaded spectrum from app
        self.run = run
        self.spectrum = self.run.data[detector]
        self.detector = detector

        # Set up containers to store initial and fitted parameters
        self.initial_bg_params = {
            "background": {
                "a": {
                    "value": 0,
                    "vary": True
                },
                "b": {
                    "value": 0,
                    "vary": True
                },
                "c": {
                    "value": 0,
                    "vary": True
                }
            }
        }

        self.fitted_bg_params = {}

        self.initial_model_params = {}
        self.fitted_model_params = {}

        self.initial_peak_params = {}
        self.fitted_peak_params = {}

        self.fit_result = None
        self.x_range = None
        self.y_range = None
        self.proportions_constraint = None

        plot_settings = {"colour": get_config()["plot"]["fill_colour"]}
        self.fig, self.axs = plotting.plot_spectrum_residual(self.spectrum, self.run.normalisation, **plot_settings)
        self.main_axs = self.axs[0]
        self.residual_axs = self.axs[1]

    def next_id(self, name):
        filtered_name = name.replace("_", "")  # if there is an underscore in the file name things will break

        if filtered_name not in self.initial_model_params.keys():
            return filtered_name

        i=0
        while f"{filtered_name}{i}" in self.initial_model_params.keys():
            i+=1
        return f"{filtered_name}{i}"

    def fit_model(self):
        # clear fit parameters in between fits
        self.fitted_model_params = {}

        logger.debug("Fitting range E = (%s, %s).", round(self.x_range[0], 2), round(self.x_range[1], 2))
        logger.debug("Initial peak parameters %s", self.initial_peak_params)
        logger.debug("Initial background parameters %s", self.initial_bg_params)
        x_data, y_data = Trimdata(self.spectrum.x, self.spectrum.y, self.x_range[0], self.x_range[1])

        t0 = time.time_ns()
        self.fit_result = fit_data.fit_model_lmfit(x_data, y_data, self.initial_peak_params, self.initial_bg_params,
                                                  self.initial_model_params, constrain_scale=self.proportions_constraint)
        t1 = time.time_ns()
        logger.info("Peak fitting finished in %ss.", round((t1-t0)/1e9, 3))

        self.fitted_bg_params = deepcopy(self.initial_bg_params)
        self.fitted_model_params = deepcopy(self.initial_model_params)

        for param_name, param in self.fit_result.params.items():
            prefix, var_name = param_name.split("_")

            # if error is not available, set error to 0
            stderr = param.stderr if param.stderr is not None else 0

            # separate the background parameters and the peak parameters
            if prefix == "background":
                self.fitted_bg_params["background"][var_name] = {
                    "value": param.value,
                    "stderr": stderr
                }

            elif prefix == "scale":
                self.const = {
                    "value": param.value,
                    "stderr": stderr
                }

            else:
                self.fitted_model_params[prefix][var_name] = {
                    "value": param.value,
                    "stderr": stderr
                }

        logger.debug("Fitted background parameters: %s", self.fitted_bg_params)
        logger.debug("Fitted peak parameters: %s", self.fitted_model_params)

    def replot_spectrum(self):
        replot_run(self.run, self.fig, self.axs, colour=get_config()["plot"]["fill_colour"])

    def replot_spectrum_residual(self):
            replot_run_residual(self.run, self.fig, self.axs, self.fit_result, colour=get_config()["plot"]["fill_colour"])

    def load_and_add_model(self, path):
        with open(path, "r") as file:
            obj = json.load(file)
            logger.debug("Loaded model from %s", path)

        file_name = path.replace("\\", "/").split("/")[-1]
        name = file_name[:-5] # remove last 5 characters - ".json"
        model_id = self.next_id(name)

        # remove background
        self.initial_peak_params[model_id] = obj["peaks"]
        self.initial_model_params[model_id] = {"x0": {"value": 0}, "scale": {"value": 1}}
        logger.debug("Adding new model %s: %s.", model_id, self.initial_model_params[model_id])

    def remove_model(self, model_id):
        self.initial_model_params.pop(model_id)
        self.initial_peak_params.pop(model_id)

    def calculate_x_range(self):
        # extract peak centres and sigmas from all loaded parameters

        # extract all peak centres and sigmas
        center_list = []
        sigma_list = []

        for model_id, model_params in self.initial_peak_params.items():
            for peak_id, peak_params in model_params.items():
                center_list.append(peak_params["center"]["value"])
                sigma_list.append(peak_params["sigma"]["value"])

        center = np.array(center_list)
        sigma = np.array(sigma_list)

        start_peak = np.min(center)
        start_sigma = sigma[center == start_peak][0]

        stop_peak = np.max(center)
        stop_sigma = sigma[center == stop_peak][0]

        e_start = start_peak - 8*start_sigma
        if e_start < 0:
            e_start = 0

        e_stop = stop_peak + 8*stop_sigma

        self.x_range = (e_start, e_stop)

    # y range for plotting (to make plot look nice)
    def calculate_y_range(self, ydata):
        y_range = (-np.max(ydata) * 0.05, np.max(ydata) * 1.3)
        self.y_range = y_range

    def plot_residual(self):
        # Because for some reason, this is not always the case... The residuals could be calculated manually
        # to avoid this, but it seems to only happen when the fit is really bad, so ignoring for now.
        x_data = self.fit_result.userkws["x"]
        if len(x_data) == len(self.fit_result.residual):
            residual_data = self.fit_result.residual
            self.residual_axs.plot(x_data, self.fit_result.residual, label="Residuals (Data - Best Fit)")
            self.residual_axs.set_ylim(-np.max(np.abs(residual_data)) * 1.2 , np.max(np.abs(residual_data)) * 1.2)
            self.residual_axs.set_xlim(self.x_range)
            self.residual_axs.grid(True)
            self.residual_axs.legend()
            
    def plot_fit(self, overwrite_old=True):
        if self.fit_result is None:
            raise AttributeError("No fit result found in model!")

        # removes previous fit from figure is prompted
        if overwrite_old:
            blacklisted_labels = ["Best fit", "Residuals (Data - Best Fit)", "Initial parameters"]
            for ax in self.axs:
                for line in ax.lines:
                    if line.get_label() in blacklisted_labels:
                        line.remove()

        x_data_high_res = np.linspace(self.x_range[0], self.x_range[1], 1000)
        y_data_high_res = self.fit_result.eval(x=x_data_high_res)

        self.main_axs.plot(x_data_high_res, y_data_high_res, label="Best fit")
        self.main_axs.set_xlim(self.x_range)
        self.main_axs.set_ylim(self.calculate_y_range(y_data_high_res))
        self.main_axs.legend()

        self.plot_residual()


    def save_params(self, path, x_range):
        obj = {
            "background": self.initial_bg_params,
            "peaks": self.initial_peak_params,
            "x_range": x_range
        }

        with open(path, "w") as file:
            json.dump(obj, file, indent=4)
            logger.debug("Saved initial parameters to %s", path)

        file.close()

    def load_params(self, path):
        with open(path, "r") as file:
            obj = json.load(file)
            logger.debug("Loaded initial parameters from %s", path)

        self.initial_peak_params = obj["peaks"]
        self.initial_bg_params = obj["background"]

        # update energy range
        self.x_range = obj["x_range"]
        file.close()

    def save_fit_report(self, path):
        with open(path, "w") as file:
            file.write(self.fit_result.fit_report())
            logger.debug("Saved fitted report to %s", path)

        file.close()

    def save_fitted_model(self, path: str):
        obj = {
            "background": self.fitted_bg_params,
            "peaks": self.fitted_peak_params,
            "x_range": self.x_range
        }

        with open(path, "w") as file:
            json.dump(obj, file, indent=4)
            logger.debug("Saved fitted parameters to %s", path)

        file.close()

    def close_figures(self):
        plt.close(self.fig)
