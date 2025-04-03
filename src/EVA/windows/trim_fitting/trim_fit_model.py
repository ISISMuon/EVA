from functools import partial

import re
import matplotlib.pyplot as plt
import numpy as np
from PyQt6.QtCore import pyqtSignal
from lmfit import Parameters, minimize

from EVA.windows.srim.trim_model import TrimModel

class TrimFitModel(TrimModel):
    def __init__(self):
        super().__init__()

        self.input_layers = [
            {
                "name": "Beamline Window",
                "thickness": 0.05
            },
            {
                "name": "Air (compressed)",
                "thickness": 0.067
            },
            {
                "name": "Al",
                "thickness": 0.01,
                "density": 2.70
            },
            {
                "name": "N",
                "thickness": 0.01,
                "density": 1.25
            },
            {
                "name": "Si",
                "thickness": 0.2,
                "density": 1.4
            },
            {
                "name": "Cu",
                "thickness": 0.2,
                "density": 8.96
            }
        ]

        self.target_indices = []
        self.loaded_data = []
        self.momentum = []
        self.proportions = []

        self.fit_iter = 0
        self.next_id = 0

    def get_layer_id(self):
        id_str = f"layer{self.next_id}"
        self.next_id += 1

        return id_str

    def plot_initial_proportions(self):
        fig, ax = plt.subplots()

        print(self.target_indices)
        for i in self.target_indices:
            ax.plot(self.momentum, self.proportions[i, :], "o-", label=self.sample_names[i])

        ax.legend()

        return fig, ax



    def plot_comparison(self):
        fig, ax = plt.subplots(2)

        for ix in self.target_indices:
            color = ax[0]._get_lines.get_next_color()
            ax[0].plot(self.momentum, (self.proportions_per_layer[ix, :] / 100), "o--", color=color,
                       label=f"{self.sample_names[ix]} (sim)")

            ax[0].plot(self.momentum, self.proportions[ix, :], "o-", color=color,
                       label=f"{self.sample_names[ix]}")

        ax[0].legend()

        return fig, ax

    def func(self, params, xdata, ydata, progress_callback, param_ids):
        self.fit_iter += 1

        """
        for i, ix in enumerate(self.target_indices):
            if i == 0:
                thickness = params[f"boundary{i}"] - base_pos
            else:
                thickness = params[f"boundary{i}"] - params[f"boundary{i-1}"]

            self.input_layers[ix]["thickness"] = thickness
        """

        for i, ix in enumerate(self.target_indices):
            self.input_layers[ix]["thickness"] = params[f"thickness{ix}_{param_ids[ix]}"]

        self.start_trim_simulation(progress_callback)
        
        if self.cancel_sim:
            return

        residuals = []

        for i in self.target_indices:
            sim_proportion = self.proportions_per_layer[i, :] / 100
            measured_proportion = self.proportions[i, :]
            residuals.append((sim_proportion - measured_proportion))

        # convolve all residual arrays to get total residual array (allows fitting multiple curves at once)
        total_residual = np.concatenate(residuals)

        progress_callback.emit({"iteration": self.fit_iter, "residuals": total_residual,
                                "sim_proportion": self.proportions_per_layer, "params": params})

        return total_residual

    def plot_progress(self, xdata: np.ndarray, ydatas: np.ndarray, n_iter: int) -> tuple[plt.Figure, plt.Axes]:
        """
        Plots the current fit and compares it with the experiment data
        Args:
            xdata: momentum array
            ydatas: current simulation result (proportions per layer)
            n_iter: current iteration number

        Returns:
            mpl figure, mpl axes with plotted data
        """
        fig, ax = plt.subplots(2)
        fig.suptitle(f"Iteration number {n_iter}")

        for ix in self.target_indices:
            color = ax[0]._get_lines.get_next_color()
            ax[0].plot(xdata, (ydatas[ix, :] / 100), "o--", color=color,
                       label=f"{self.sample_names[ix]} (sim)")

            ax[0].plot(self.momentum, self.proportions[ix, :], "o-", color=color,
                       label=f"{self.sample_names[ix]}")

            ax[1].plot(self.momentum, ((ydatas[ix, :] / 100) - self.proportions[ix]),
                       label=f"{self.sample_names[ix]}")

        ax[0].legend(fontsize=8)
        ax[1].legend(fontsize=8)

        return fig, ax

    def optimise(self, progress_callback):
        """
        Starts the TRIM fitting.

        Args:
            progress_callback: callback to report simulation progress to GUI

        Returns:
            status dict indicating whether simulation was finished or cancelled
        """
        self.fit_iter = 0

        # get the boundary positions of each layer given their thicknesses
        initial_boundaries = self.get_layer_boundary_positions()

        params = Parameters()

        # sets "init_bound" equal to the lower layer boundary of the first layer to be fitted
        # so that it can be used in the constraint expression for the first boundary parameter
        params._asteval.symtable['init_bound'] = initial_boundaries[self.target_indices[0]]

        # inspired by this: https://stackoverflow.com/questions/49931455/python-lmfit-constraints-a-b-c?rq=3
        # The boundary parameters are constrained to be in terms of the initial boundary and thicknesses

        param_ids = []

        for j, sample_name in enumerate(self.sample_names):
            name = re.sub('[()\\s]', '', sample_name)

            param_ids.append(name)

            thickness = self.input_layers[j]["thickness"]
            vary = j in self.target_indices # boolean for

            params.add(f'boundary{j}_{name}', value=initial_boundaries[j + 1], vary=vary,)

            if j == 0:
                params.add(f"thickness{j}_{name}", value=thickness, expr=f"boundary{j}_{name}", min=0)
            else:
                params.add(f"thickness{j}_{name}", value=thickness, expr=f"boundary{j}_{name} - boundary{j-1}_{param_ids[j-1]}", min=0)

        # since the fitting data is simulated it will vary a little in between iterations, so it is important that the
        # changes made by lmfit to parameters between iterations is greater than the noise of the simulation.
        # the size of the parameter changes can be modified with the "epsfcn" parameter (i think it's the derivative multiplier)

        self.fit_result = minimize(self.func, method="leastsq", nan_policy="omit", params=params, iter_cb=self.on_iteration_complete, args=(self.momentum, self.proportions, progress_callback, param_ids),
                       epsfcn=0.01, max_nfev=100)

        # returns status to the GUI so that it can update it correspondingly
        if self.cancel_sim:
            return {"status": "cancelled"}
        else:
            return {"status": "success"}

    def on_iteration_complete(self, params, iter, resid, *args, **kwargs):
        """
        Is called in between every fit iteration. Checks if the simulation has been cancelled, and stops fitting if so.

        Args:
            params: fitting params
            iter: iteration number
            resid: residuals
            *args: other positional args supplied by lmfit
            **kwargs: other keyword args supplied by lmfit

        Returns:
            True if fitting should stop, None if fitting should continue
        """
        if self.cancel_sim:
            return True

    def test_first_iter(self, progress_callback):
        """
        Start a single momentum scan using initial parameters and momentum steps in experiment data.

        Args:
            progress_callback: callback to return simulation progress to GUI between simulations

        Returns:
            result dictionary indicating whether simulation was finished or cancelled
        """
        return self.start_trim_simulation(progress_callback)
