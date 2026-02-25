import os
import time
from zipfile import ZipFile

import numpy as np
from PyQt6.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt
from EVA.core.app import get_config

class G4blModel(QObject):
    simulation_error_s = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Default layers to display in table
        self.input_layers = [{
                "name": "Beamline Window",
                "thickness": 0.05
            },
            {
                "name": "Air (compressed)",
                "thickness": 0.067
            },
            {
                "name": "Al",
                "thickness": 0.05,
                "density": 2.7
            },
            {
                "name": "Cu",
                "thickness": 0.5,
                "density": 8.96
            }]

        # initialising layer variables
        self.sample_layers = None
        self.sample_names = []
        self.total_thickness = 0
        self.layer_boundary_positions = []

        ### Default G4BL settings ###
        self.stats = 1000
        self.g4bl_exe_dir = get_config()["g4bl"]["installation_directory"]
        self.g4bl_out_dir = get_config()["g4bl"]["output_directory"]

        self.sim_type = "Mono"
        self.momentum = [27.]
        self.momentum_spread = 4.

        self.min_momentum = 21.
        self.max_momentum = 30.
        self.step_momentum = 1.

        self.scan_type = "No"
        ####################

        # simulation results
        self.result_x = None # raw results
        self.result_y = None

        self.ydata_per_layer = None
        self.counts_per_layer = None
        self.counts_per_layer_err = None
        self.proportions_per_layer = None
        self.proportions_per_layer_err = None

        # for storing an x-axis shift for each momentum plot (one for each momentum)
        self.default_origin_position = 0
        self.stopping_plot_origin_shifts = []
        self.depth_plot_origin_shift = 0
        self.cancel_sim = False
        self.simulation_times = None # to store the time taken for each simulation

    def number_of_sims(self) -> int:
        """
        Calculates the number of simulations to be done given current settings.

        Returns: number of sims
        """

        if self.scan_type == 'Yes':
            n_sim = len(np.arange(start=self.min_momentum, stop=self.max_momentum, step=self.step_momentum))
        else:
            n_sim = len(self.momentum)

        return n_sim
