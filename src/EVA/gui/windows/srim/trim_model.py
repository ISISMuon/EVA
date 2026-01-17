import os
import time
from zipfile import ZipFile

import numpy as np
from PyQt6.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt
from EVA.core.app import get_config
from srim import TRIM, Ion, Layer, Target


class TrimModel(QObject):
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

        ### Default SRIM settings ###
        self.stats = 1000
        self.srim_exe_dir = get_config()["SRIM"]["installation_directory"]
        self.srim_out_dir = get_config()["SRIM"]["output_directory"]

        self.sim_type = "Mono"
        self.momentum = [27.]
        self.momentum_spread = 4.

        self.min_momentum = 21.
        self.max_momentum = 30.
        self.step_momentum = 1.

        self.scan_type = "No"
        self.sigma_step = 12 # number of runs for each momentum when calculating momentum spread
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

        if self.sim_type == "Momentum Spread":
            n_sim = n_sim * (self.sigma_step + 1)

        return n_sim

    def start_trim_simulation(self, progress_callback: pyqtSignal) -> dict:
        """
        Runs the srim simulation using parameters set in the model.
        """
        # Calculate momentum array if momentum scan is wanted
        if self.scan_type == 'Yes':
            self.momentum = np.round(np.arange(start=self.min_momentum, stop=self.max_momentum, step=self.step_momentum), 5)

        # initialise empty data arrays
        self.result_x = np.zeros(shape=(len(self.momentum), 100))
        self.result_y = np.zeros_like(self.result_x)

        # set up TRIM sample object
        self.setup_sample(self.input_layers)
        target_sample = Target(self.sample_layers)

        simulation_count = 0
        total_sims = self.number_of_sims()

        # MONO simulations
        if self.sim_type == 'Mono':
            self.simulation_times = np.zeros_like(self.momentum)

            for momentum_index, mom in enumerate(self.momentum):
                t0 = time.time_ns()

                # calculate muon for given momentum
                muon_ion = self.get_muon(mom)

                x, y, cancel_flag = self.run_TRIM(target=target_sample, muon=muon_ion, n_muons=self.stats)
                simulation_count += 1

                # if simulation stop is requested
                if cancel_flag:
                    return {"status": "cancelled"}

                # insert results into results arrays
                self.result_x[momentum_index, :] = x
                self.result_y[momentum_index, :] = y

                t1 = time.time_ns()

                dt = (t1 - t0) / 1e9
                self.simulation_times[simulation_count - 1] = dt

                # report progress to gui
                progress_callback.emit(
                    {"current": simulation_count, "total": total_sims, "sim_times": self.simulation_times})

        # Simulation with momentum bite
        elif self.sim_type == 'Momentum Spread':

            # array to store time taken for each simulation
            self.simulation_times = np.zeros(shape=(len(self.momentum) * (self.sigma_step + 1)))

            for momentum_index, mom in enumerate(self.momentum):
                MomSigma = 0.01 * self.momentum_spread * mom

                xres, yres = [], []

                for i in range(self.sigma_step + 1):
                    t0 = time.time_ns()

                    P = mom - 3 * MomSigma + i * 0.5 * MomSigma  # momentum for each iteration

                    # Number of simulated muons dependent on Gaussian distribution of muon momentum
                    NE = int(self.stats * (1.0 / (np.sqrt(2.0 * np.pi) * MomSigma)) * np.exp(
                        -0.5 * (P - mom) ** 2 / (MomSigma ** 2)))

                    # get muon information
                    muon_ion = self.get_muon(P)

                    x1, y1, cancel_flag = self.run_TRIM(target_sample, muon_ion, n_muons=NE)
                    simulation_count += 1

                    # if simulation stop is requested
                    if cancel_flag:
                        return {"status": "cancelled"}

                    if i == 0:
                        yres = y1
                        xres = x1
                    else:
                        for index in range(0, len(y1)):
                            yres[index] = yres[index] + y1[index]

                    # insert results into results arrays
                    self.result_x[momentum_index, :] = xres
                    self.result_y[momentum_index, :] = yres

                    # add simulation time list
                    t1 = time.time_ns()
                    dt = (t1 - t0) / 1e9

                    self.simulation_times[simulation_count - 1] = dt

                    # report progress to gui
                    progress_callback.emit(
                        {"current": simulation_count, "total": total_sims, "sim_times": self.simulation_times})

        else:
            raise ValueError("Invalid simulation type specified")

        # calculate the layer boundary positions as a cumulative sum of layer thicknesses
        self.layer_boundary_positions = self.get_layer_boundary_positions()

        self.ydata_per_layer = np.zeros(shape=(len(self.sample_layers), len(self.momentum), 100))
        self.counts_per_layer = np.zeros(shape=(len(self.sample_layers), len(self.momentum)))
        self.counts_per_layer_err = np.zeros(shape=(len(self.sample_layers), len(self.momentum)))

        self.proportions_per_layer = np.zeros(shape=(len(self.sample_layers), len(self.momentum)))
        self.proportions_per_layer_err = np.zeros(shape=(len(self.sample_layers), len(self.momentum)))

        for m, mom in enumerate(self.momentum):
            # split the ydata into a separate array for each layer and insert into big list
            comp = self.split_layers(m)

            # sum counts for each layer to get counts per layer for current momentum
            counts_per_layer = np.sum(comp, axis=1)
            layer_count_err = np.sqrt(counts_per_layer) # error

            # sum counts per layer for each momentum to get total counts for current momentum
            total_count = np.sum(counts_per_layer)
            total_count_err = np.sqrt(total_count) # error

            # calculate the proportion of total counts each layer contains for current momentum
            frac = counts_per_layer / total_count

            # error propagation
            frac_err = np.sqrt((total_count_err / total_count) ** 2 + (layer_count_err / counts_per_layer) ** 2) * frac

            # replace all nan values with 0
            frac_err_filtered = np.nan_to_num(frac_err, nan=0)

            # insert results into data arrays
            self.ydata_per_layer[:, m, :] = np.round(comp, 4)
            self.counts_per_layer[:, m] = np.round(counts_per_layer, 4)
            self.counts_per_layer_err[:, m] = np.round(np.sqrt(counts_per_layer), 4)
            self.proportions_per_layer[:, m] = np.round(frac*100, 4)
            self.proportions_per_layer_err[:, m] = np.round(frac_err_filtered*100, 4)

        # set all plot origins to be shifted by default so that 0 on the x-axis is located at end of aluminium layer
        self.default_origin_position = self.layer_boundary_positions[3]
        self.stopping_plot_origin_shifts = np.full(shape=len(self.momentum), fill_value=self.default_origin_position)

        # after sucessful run, update srim installation directory in config
        get_config()["SRIM"]["installation_directory"] = self.srim_exe_dir
        get_config()["SRIM"]["output_directory"] = self.srim_out_dir

        return {"status": "success"}

    def setup_sample(self, layers: list[dict]):
        """
        Builds SRIM layers from layer input dictionary.

        Args:
            layers: list of dictionaries containing information about layers to simulate for. Dict keys:

            * name: (str) Name of layer - must be valid name in SRIM and is case-sensitive.

            * thickness: (float) layer thickness.

            * density: (float) Not required for beamline window or compressed air.
        """

        i = 0
        sample_layers = []
        sample_names = []
        total_thickness = 0.0

        for layer in layers:
            sample_name = layer["name"]
            if sample_name == 'Beamline Window':
                layer_thickness = layer["thickness"]
                total_thickness =+ layer_thickness
                beamwindow = Layer({'H': {'stoich': 8, 'E_d': 10, 'lattice': 3, 'surface': 2
                                          },
                                    'C': {'stoich': 10, 'E_d': 28.0, 'lattice': 3.0,
                                          'surface': 7.41
                                          },
                                    'O': {'stoich': 4, 'E_d': 28.0, 'lattice': 3.0,
                                          'surface': 2.0}},
                                   density=1.4, width=layer_thickness * 1e7, phase=0)
                sample_layers.append(beamwindow)
                sample_names.append('Beamline Window')

            elif sample_name == 'Air (compressed)':

                layer_thickness = layer["thickness"]
                total_thickness =+ total_thickness

                air = Layer({'C': {'stoich': 1.24e-2, 'E_d': 28.0, 'lattice': 3.0,
                                   'surface': 7.41
                                   },
                             'O': {'stoich': 23.1781, 'E_d': 28.0, 'lattice': 3.0,
                                   'surface': 2.0
                                   },
                             'N': {'stoich': 75.5268, 'E_d': 28.0, 'lattice': 3.0,
                                   'surface': 2.0
                                   },
                             'Ar': {'stoich': 1.2827, 'E_d': 5.0, 'lattice': 1.0,
                                    'surface': 2.0}}, density=1500 * 1.20479e-3, width=layer_thickness * 1e7,
                            # air layer compressed from 150mm to 0.1mm to optimise bins
                            phase=1)
                sample_layers.append(air)
                sample_names.append('Air (compressed)')
            else:
                sampledensity = layer["density"]
                layer_thickness = layer["thickness"]
                total_thickness = + layer_thickness
                thislayer = Layer.from_formula(sample_name, density=sampledensity, width=layer_thickness * 1e7,
                                                      phase=0)

                sample_layers.append(thislayer)  # 0.016 mm = 160000Athick sample holder
                sample_names.append(sample_name)

        self.sample_layers = sample_layers
        self.sample_names = sample_names
        self.total_thickness = total_thickness

    def get_muon(self, momentum: float) -> Ion:
        """
        Defines muon momentum, mass and kinetic energy and models the muon as a hydrogen ion in pysrim

        Args:
            momentum: Muon momentum

        Returns:
            pysrim 'Ion' object with muon properties.
        """

        mass_mevc = 105.6583745  # mass o muon in MeV/c^2
        mass_amu = mass_mevc / 931.5  # mass of muon in atomic mass units

        # kinetic energy associate with the momentum (relativistic)
        kinetic_energy = np.sqrt(mass_mevc ** 2 + momentum ** 2) - mass_mevc

        # corresponding SRIM muon ion definitions
        # define muon as Hydrogen ion with mass of muon, with a given kinetic energy
        muon_ion = Ion('H', kinetic_energy * 1e6, mass_amu)

        return muon_ion

    def run_TRIM(self, target: Target, muon: Ion, n_muons: int) -> tuple[list | None, list | None, int]:
        """
        Runs TRIM simulation for a single momentum.

        Args:
            target: sample target
            muon: muon object
            n_muons: number of muons to simulate for

        Returns: xdata, ydata, cancel_flag - 1 is simulation stop was requested while simulating, 0 if all good
        """

        if self.cancel_sim:
            return None, None, 1

        trim_sim = TRIM(target, muon, number_ions=n_muons, calculation=1)

        try:
            trim_data_output = trim_sim.run(self.srim_exe_dir)  # Simulation run by executing SRIM.exe in directory

            # output files from SRIM copied to desired output directory
            TRIM.copy_output_files(self.srim_exe_dir, self.srim_out_dir)

        except FileNotFoundError:
            return

        trim_data = trim_data_output.range

        x1 = np.array(trim_data.depth / 1e7)  # muon ranges, converted from angstroms to mm.

        y1 = np.array(trim_data.ions)  # SRIM has weird units for y axis

        y1_corrected = self.correct_to_counts(self.total_thickness, y1, n_muons)

        # e1 = list(trim_data.ions)

        return x1, y1_corrected, 0

    def correct_to_counts(self, thickness, y1, total_sim_counts):
        ''' output of SRIM is odd this corrects it to counts'''
        final_bins = thickness / 100.0

        for i in range(len(y1)):
            y1[i] = y1[i] * final_bins * total_sim_counts

        return y1

    def get_layer_boundary_positions(self) -> np.ndarray[float]:
        """
        Calculate the (cumulative) boundary positions for all layers.

        Returns:
            numpy array containing layer boundary positions, includes start point at 0.0
        """

        layer_thicknesses = [float(layer["thickness"]) for layer in self.input_layers]
        # insert 0.0 to start of list
        layer_thicknesses.insert(0, 0.)

        boundaries = np.cumsum(np.array(layer_thicknesses, dtype=float))

        # cast to numpy array and shift
        return boundaries

    def split_layers(self, MomIndex: int) -> list[np.ndarray]:
        """
        Splits up the SRIM result into list of np.ndarrays, one for each layer, containing only the y-values in that
        layer.

        Args:
            MomIndex: which momentum to calculate for

        Returns:
            list of np.ndarrays
        """

        # get data for given index
        y_data = self.result_y[MomIndex, :]
        x_data = self.result_x[MomIndex, :]
        comp = []

        for i in range(len(self.sample_layers)):
            lower_boundary = self.layer_boundary_positions[i]
            upper_boundary = self.layer_boundary_positions[i + 1]

            y_subset = np.array([y_data[j] if lower_boundary < x_data[j] <= upper_boundary else 0.
                                 for j, _ in enumerate(x_data)])

            comp.append(y_subset)

        return comp

    def plot_whole(self, momentum_index: int, momentum: float) -> tuple[plt.Figure, plt.Axes]:
        """
        Plots the whole stopping profile from the srim simulation

        Args:
            momentum_index: the list index
            momentum: momentum value

        Returns:
            matplotlib figure and axes objects with plotted data.
        """
        x_shift = self.stopping_plot_origin_shifts[momentum_index]

        figt, axx = plt.subplots()

        axx.set_xlabel('Depth ($mm$)')
        axx.set_ylabel('Number of muons')
        axx.set_title('SRIM Simulation at ' + str(round(momentum, 4)) + ' MeV/c')

        axx.plot(self.result_x[momentum_index] - x_shift, self.result_y[momentum_index])

        y_lim_upper = axx.get_ylim()[1]

        # Display layer boundaries on plot
        for i in range(len(self.sample_layers)):
            pos = self.layer_boundary_positions[i + 1]

            axx.axvline(x=pos - x_shift, color='k', linestyle='--')
            axx.text(pos - x_shift, y_lim_upper * 0.02, self.sample_names[i], horizontalalignment='left', rotation='vertical')

        return figt, axx

    def plot_components(self, momentum_index: int, momentum: float) -> tuple[plt.Figure, plt.Axes]:
        """
        Plots the whole stopping profile from the srim simulation and shows the profile from each layer separately.

        Args:
            momentum_index: the list index
            momentum: momentum value

        Returns:
            matplotlib figure and axes objects with plotted data.
        """

        x_shift = self.stopping_plot_origin_shifts[momentum_index]

        # plot components
        figt, axx = plt.subplots()
        axx.set_xlabel('Depth ($mm$)')
        axx.set_ylabel('Number of muons')
        axx.set_title('SRIM Simulation at ' + str(round(momentum, 4)) + ' MeV/c')

        # plot overall profile
        axx.plot(self.result_x[momentum_index] - x_shift, self.result_y[momentum_index])

        y_lim_upper = axx.get_ylim()[1]

        for i in range(len(self.sample_layers)):
            # plot profile per layer
            axx.plot(self.result_x[0] - x_shift, self.ydata_per_layer[i, momentum_index], label=self.sample_names[i])

            # display layer boundaries
            pos = self.layer_boundary_positions[i + 1]
            axx.axvline(x=pos - x_shift, color='k', linestyle='--')
            axx.text(pos - x_shift, y_lim_upper * 0.02, self.sample_names[i], horizontalalignment='left', rotation='vertical')

        axx.legend()

        return figt, axx

    def plot_depth_profile(self) -> tuple[plt.Figure, plt.Axes]:
        """
        Plots the whole stopping profile from the srim simulation.

        Returns:
            matplotlib figure and axes objects with plotted data.
        """

        fig, ax = plt.subplots()
        ax.set_xlabel('Muon Momentum (MeV/c)')
        ax.set_ylabel('Proportion')

        boundaries = []
        closest_momenta = []

        # approximate peak centre position for each momentum
        centroids = self.result_x[0, :][np.argmax(self.result_y, axis=1)]

        for i, layer in enumerate(self.sample_layers):
            # layer boundary (lower and upper)
            boundary = (self.layer_boundary_positions[i:i+2])

            # if not any([boundary[0] < peak <= boundary[1] for peak in centroids]):
            #     print(f"Skipping layer {self.sample_names[i]} as no peaks found within it.")
            #     continue  # skip all layers with no peaks within it
            # else:
            #     print(f"Not skipping layer {self.sample_names[i]} as peak(s) found within it.")
            ax.plot(self.momentum, self.proportions_per_layer[i, :], "o-", label=self.sample_names[i], ms=4)

            # find momentum point closest to layer boundary - COULD REPLACE THIS WITH LINEAR INTERPOLATION
            closest_momentum = self.momentum[np.argmin(np.abs(centroids - boundary[1]))]

            # store the values for plotting lines later
            boundaries.append(float(boundary[1]))
            closest_momenta.append(float(closest_momentum))

        # create twin axis to display depth
        ax2 = ax.twiny()
        ax2.set_xticks(closest_momenta)
        ax2.set_xbound(ax.get_xbound())
        ax2.set_xticklabels([f"{(b - self.depth_plot_origin_shift):.3f}" for b in boundaries])

        ax2.set_xlabel("Depth (mm)")
        ax.vlines(closest_momenta, 0, 100, colors="black", linestyles="--")

        y_lim_upper = ax.get_ylim()[1]

        for i, boundary in enumerate(boundaries):
            ix = np.where(self.layer_boundary_positions == boundary)[0][0]
            name = self.sample_names[ix-1]
            ax.text(x=closest_momenta[i], y=0.04*y_lim_upper, s=name, horizontalalignment='left', rotation='vertical')

        ax.set_xlabel("Momentum (MeV/c)")
        ax.set_ylabel("Proportion")

        ax.legend()
        return fig, ax

    def get_default_srim_save_name(self, momentum: float | None = None) -> str:
        if momentum is None:
            momentum = "all"
        else:
            momentum = f"{momentum:.5f}"
        return os.path.join(f"{get_config()["general"]["working_directory"]}", f"SRIM_{momentum}_MeVc.zip")

    def save_sim(self, path: str, rows: list | int | None = None):
        if isinstance(rows, int):
            rows = [rows]

        if rows is None:
            rows = [i for i, _ in enumerate(self.momentum)]

        # prepare header text (will be the same for all files)
        header = [(f"Layer {i}: {self.sample_names[i]} at ({self.layer_boundary_positions[i]}mm, "
                   f"{self.layer_boundary_positions[i + 1]}mm)\n") for i, layer in enumerate(self.sample_layers)]

        header.append("\nDepth (mm), Muon count\n")

        # create zip archive
        with ZipFile(path, "w") as zf:
            for row in rows:
                momentum = self.momentum[row]
                total_curve_filename = f"{momentum:.5f}MeVc_total_profile.dat"

                total_curve_data = [f"{x}, {self.result_y[row][i]}\n" for i, x in enumerate(self.result_x[row])]
                total_curve_str = "".join(header) + "".join(total_curve_data)

                zf.writestr(total_curve_filename, total_curve_str)

                for i, layer_name in enumerate(self.sample_names):
                    layer_filename =  f"{momentum:.5f}MeVc_layer{i}_profile.dat"

                    ydata_per_layer = self.split_layers(row)  # list of arrays containing a y-array for each layer
                    layer_data = [f"{x}, {ydata_per_layer[i][j]}\n" for j, x in enumerate(self.result_x[row])]
                    layer_curve_str = "".join(header) + "".join(layer_data)

                    zf.writestr(layer_filename, layer_curve_str)


    def save_settings(self, sample_name, stats, srim_dir, output_dir, momentum, momentum_spread, sim_type,
                        min_momentum, max_momentum, step_momentum, scan_type, layers, target_dir):

        file2 = open(target_dir, "w")
        file2.writelines('Sample Name\n')
        out = sample_name+'\n'
        file2.writelines(out)
        file2.writelines('SimType\n')
        out = sim_type+'\n'
        file2.writelines(out)
        file2.writelines('Momentum\n')
        out = str(momentum)+'\n'
        file2.writelines(out)
        file2.writelines('Momentum Spread\n')
        out = str(momentum_spread)+'\n'
        file2.writelines(out)
        file2.writelines('Scan Momentum\n')
        out = scan_type+'\n'
        file2.writelines(out)
        file2.writelines('Min Momentum\n')
        out = str(min_momentum)+'\n'
        file2.writelines(out)
        file2.writelines('Max Momentum\n')
        out = str(max_momentum)+'\n'
        file2.writelines(out)
        file2.writelines('Momentum Step\n')
        out = str(step_momentum)+'\n'
        file2.writelines(out)
        file2.writelines('Stats\n')
        out = str(stats)+'\n'
        file2.writelines(out)
        file2.writelines('Sample\n')

        for layer in layers:
            file2.writelines(layer["name"] + "," + str(layer["thickness"]) + "," + str(layer.get("density", "")) + "\n")
        file2.close()

    def load_settings(self, target_dir):
        file2 = open(target_dir, "r")
        ignore = file2.readline()
        sample_name = file2.readline().strip()
        ignore = file2.readline()
        sim_type = file2.readline().strip()
        ignore = file2.readline()
        momentum = file2.readline().strip()
        ignore = file2.readline()
        momentum_spread = file2.readline().strip()
        ignore = file2.readline()
        scan_type = file2.readline().strip()
        ignore = file2.readline()
        min_momentum = file2.readline().strip()
        ignore = file2.readline()
        max_momentum = file2.readline().strip()
        ignore = file2.readline()
        step_momentum = file2.readline().strip()
        ignore = file2.readline()
        stats = file2.readline().strip()
        ignore = file2.readline()

        form_data = {
            "sample_name": sample_name,
            "stats": float(stats),
            "srim_dir": get_config()["SRIM"]["installation_directory"],
            "output_dir": get_config()["SRIM"]["output_directory"],
            "momentum": float(momentum),
            "sim_type": sim_type,
            "momentum_spread": float(momentum_spread),
            "min_momentum": float(min_momentum),
            "max_momentum": float(max_momentum),
            "step_momentum": float(step_momentum),
            "scan_type": scan_type
        }

        layers = []
        while True:
            line = file2.readline().strip().split(',')

            if line == [""]:
                break

            name, thickness, density = line

            if density != "":
                layer = {"name": name, "thickness": thickness, "density": density}
            else:
                layer = {"name": name, "thickness": thickness}

            layers.append(layer)
        file2.close()

        return form_data, layers

    @staticmethod
    def is_valid_path(path):
        return os.path.exists(path)

    def estimate_time_left(self, current: int, total: int) -> str:
        """
        Estimates the time remaining to finish the simulation

        Args:
            current: current simulation number
            total: total number of simulations to be done

        Returns:
            Formatted time string H:M:S
        """
        seconds = (np.sum(self.simulation_times) / current) * (total - current)

        if seconds > 86400:
            return f"More than {int(seconds // 86400)} days. Please reconsider."

        return time.strftime('%H:%M:%S', time.gmtime(seconds))

    @staticmethod
    def close_figure(fig):
        plt.close(fig)