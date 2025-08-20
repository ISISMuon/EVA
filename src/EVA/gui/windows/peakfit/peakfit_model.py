import json
import time
import logging
from copy import copy, deepcopy

import numpy as np
from PyQt6.QtCore import QObject
from matplotlib import pyplot as plt

from EVA.core.fitting import fit_data
from EVA.core.physics.functions import gaussian
from EVA.core.plot.plotting import replot_run, replot_run_residual
from EVA.util.trim_data import Trimdata

from EVA.core.app import get_app, get_config

from EVA.core.data_structures.detector import DetectorIndices
from EVA.core.plot import plotting

logger = logging.getLogger(__name__)

class PeakFitModel(QObject):
		def __init__(self, run, detector, parent=None):
				super().__init__()

				# Get loaded spectrum from app
				self.run = run
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

				self.initial_peak_params = {}
				self.fitted_peak_params = {}

				self.fit_result = None
				self.x_range = None

				self.y_range = None

				self.id_counter = 0

				self.add_peak_mode = False

				self.plot_settings = {"colour": get_config()["plot"]["fill_colour"]}
				self.fig, self.axs = plotting.plot_spectrum_residual(self.run.data[self.detector], self.run.normalisation, **self.plot_settings)
				self.main_axs = self.axs[0]
				self.residual_axs = self.axs[1]

		# im sure there is a nice way to do this. exercise for the reader...
		def next_id(self) -> str:
				p_id = self.id_counter
				self.id_counter += 1
				return f"p{p_id}"

		def fit_peaks(self):
				# clear fit parameters in between fits
				self.fitted_bg_params = {}
				self.fitted_peak_params = {}

				logger.debug("Fitting range E = (%s, %s).", round(self.x_range[0], 2), round(self.x_range[1], 2))
				logger.debug("Initial peak parameters %s", self.initial_peak_params)
				logger.debug("Initial background parameters %s", self.initial_bg_params)
				x_data, y_data = Trimdata(self.run.data[self.detector].x, self.run.data[self.detector].y, self.x_range[0], self.x_range[1])
				t0 = time.time_ns()
				self.fit_result = fit_data.fit_gaussian_lmfit(x_data, y_data, self.initial_peak_params, self.initial_bg_params)

				t1 = time.time_ns()
				logger.info("Peak fitting finished in %ss.", round((t1-t0)/1e9, 3))

				# store new fit parameters in model
				self.fitted_bg_params = deepcopy(self.initial_bg_params)
				self.fitted_peak_params = deepcopy(self.initial_peak_params)

				for param_name, param in self.fit_result.params.items():
						prefix, var_name = param_name.split("_")

						if var_name == "fwhm" or var_name == "height": # ignore these
								continue

						# if error is not available, set error to 0
						stderr = param.stderr if param.stderr is not None else 0

						# separate the background parameters and the peak parameters
						if prefix == "background":
								self.fitted_bg_params["background"][var_name] = {
								"value": param.value,
								"stderr": stderr
						}

						else:
								self.fitted_peak_params[prefix][var_name] = {
								"value": param.value,
								"stderr": stderr
						}

				logger.debug("Fitted background parameters: %s", self.fitted_bg_params)
				logger.debug("Fitted peak parameters: %s", self.fitted_peak_params)

		def add_initial_peak_params(self, x: float):
				# find height of curve at specified x to give as initial peak height guess
				ix = np.argmin(abs(self.run.data[self.detector].x - x))
				height = self.run.data[self.detector].y[ix]

				center = x
				sigma = 0.7 # estimated sigma based on measurements
				area = height * sigma * np.sqrt(np.pi*2) # calculating area from height and sigma

				# generate new ID for the peak
				peak_id = self.next_id()

				self.initial_peak_params[peak_id] = {
						"center": {
								"value": center,
								"vary": True,
								"min": 0
						},
						"sigma": {
								"value": sigma,
								"vary": True,
								"min": 0
						},
						"amplitude": {
								"value": area,
								"vary": True,
								"min": 0
						}
				}

				logger.debug("Adding new peak %s: %s.", peak_id, self.initial_peak_params[peak_id])

		def remove_initial_peak_param(self, peak_id: str):
				self.initial_peak_params.pop(peak_id)

		def calculate_x_range(self):
				# extract peak centres and sigmas from all loaded parameters
				params = list(zip(*[[self.initial_peak_params[name]["center"]["value"],
														 self.initial_peak_params[name]["sigma"]["value"]]
														for name in self.initial_peak_params.keys()]))

				center = np.array(params[0])
				sigma = np.array(params[1])

				start_peak = np.min(center)
				start_sigma = sigma[center == start_peak][0]

				stop_peak = np.max(center)
				stop_sigma = sigma[center == stop_peak][0]

				e_start = start_peak - 8*start_sigma
				if e_start < 0:
						e_start = 0

				e_stop = stop_peak + 8*stop_sigma

				self.x_range = (e_start, e_stop)

		def plot_initial_params(self, overwrite_old: bool=True):
			bg = self.initial_bg_params["background"]

			x = self.run.data[self.detector].x

			func = bg["a"]["value"] * x * x + bg["b"]["value"] * x + bg["c"]["value"]

			for _, param in self.initial_peak_params.items():
					func += gaussian(x, param["center"]["value"], param["sigma"]["value"], param["amplitude"]["value"])

			if overwrite_old:
				blacklisted_labels = ["Initial parameters"]
				for line in self.main_axs.lines:
					if line.get_label() in blacklisted_labels:
						line.remove()
			self.main_axs.plot(x, func, label="Initial parameters")
			self.main_axs.legend()

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

		def plot_fit(self, overwrite_old: bool=True):
			
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

			self.fig.tight_layout()

		# y range for plotting (to make plot look nice)
		def calculate_y_range(self, ydata: np.ndarray):
				y_range = (-np.max(ydata) * 0.05, np.max(ydata) * 1.3)
				self.y_range = y_range

		def save_params(self, path: str, x_range: tuple):
				obj = {
						"background": self.initial_bg_params,
						"peaks": self.initial_peak_params,
						"x_range": x_range
				}

				with open(path, "w") as file:
						json.dump(obj, file, indent=4)
						logger.debug("Saved initial parameters to %s", path)

				file.close()


		def replot_spectrum(self):
				replot_run(self.run, self.fig, self.axs, colour=get_config()["plot"]["fill_colour"])


		def replot_spectrum_residual(self):
				replot_run_residual(self.run, self.fig, self.axs, colour=get_config()["plot"]["fill_colour"])


		def load_params(self, path: str):
				with open(path, "r") as file:
						obj = json.load(file)
						logger.debug("Loaded initial parameters from %s", path)

				self.initial_peak_params = obj["peaks"]
				self.initial_bg_params = obj["background"]

				# update energy range
				self.x_range = obj["x_range"]
				file.close()

		def save_fit_report(self, path: str):
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