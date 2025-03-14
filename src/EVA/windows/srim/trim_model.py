import os
import shutil
from zipfile import ZipFile

import numpy as np
from PyQt6.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from scipy.stats import moment

from EVA.core.app import get_config
from srim import TRIM, Ion, Layer, Target


class TrimModel(QObject):
    simulation_error_s = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # SRIM result
        self.result_x = []
        self.result_y = []

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
                "density": 6.7
            }]

        # initialising layer variables
        self.sample_layers = None
        self.sample_names = []
        self.total_thickness = 0
        self.layer_boundary_positions = []

        self.components = []

        ### Default SRIM settings ###
        self.stats = 100
        self.srim_exe_dir = get_config()["SRIM"]["installation_directory"]
        self.srim_out_dir = get_config()["SRIM"]["output_directory"]

        self.sim_type = "Mono"
        self.momentum = 27.
        self.momentum_spread = 4.

        self.min_momentum = 21.
        self.max_momentum = 30.
        self.step_momentum = 1.

        self.scan_type = "No"

        # for storing an x-axis shift for each momentum plot (one for each momentum)
        self.default_origin_position = 0
        self.plot_origin_shifts = []

    def remove_layer(self, index: int):
        self.input_layers.pop(index)

    def start_trim_simulation(self):
        """
        Runs the srim simulation using parameters set in the model.
        """
        # Set up sample from layers
        self.setup_sample(self.input_layers)
        target_sample = Target(self.sample_layers)

        # Calculate momentum array if momentum scan is wanted
        if self.scan_type == 'Yes':
            self.momentum = np.arange(start=self.min_momentum, stop=self.max_momentum, step=self.step_momentum)
        else:
            self.momentum = [self.momentum]

        self.result_x = np.zeros((len(self.momentum), 100))
        self.result_y = np.zeros_like(self.result_x)
        self.components = []

        # Run TRIM for each momentum
        for momentum_index, mom in enumerate(self.momentum):
            if self.sim_type == 'Mono':
                # get muon information
                muon_ion = self.get_muon(mom)
                x, y = self.run_TRIM(target=target_sample, muon=muon_ion)

            elif self.sim_type == 'Momentum Spread':
                x, y = self.CalcProfileWithMomBite(target_sample, mom)
            else:
                raise ValueError("Invalid simulation type specified")

            # insert results into results arrays
            self.result_x[momentum_index, :] = x
            self.result_y[momentum_index, :] = y

        # calculate the
        self.layer_boundary_positions = self.get_layer_boundary_positions()

        # set default origin position to be at end of aluminium layer
        self.default_origin_position = self.layer_boundary_positions[3]

        self.components = []

        for momentum_index, mom in enumerate(self.momentum):
            comp = self.split_components(momentum_index)
            perlayer = self.get_muons_per_layer(comp)

            self.components.append(perlayer)

        # set all default plot origin shifts to the aluminium layer
        self.plot_origin_shifts = np.full(shape=len(self.momentum), fill_value=self.default_origin_position)

        # after sucessful run, update srim installation directory in config
        get_config()["SRIM"]["installation_directory"] = self.srim_exe_dir
        get_config()["SRIM"]["output_directory"] = self.srim_out_dir


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
                print('done air')
                print(sample_layers)
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

    def run_TRIM(self, target: Target, muon: Ion) -> tuple[list, list] | None:
        """
        Runs TRIM simulation for a single momentum.

        Args:
            target: sample target
            muon: muon object

        Returns: xdata, ydata
        """

        trim_sim = TRIM(target, muon, number_ions= self.stats, calculation=1)

        try:
            trim_data_output = trim_sim.run(self.srim_exe_dir)  # Simulation run by executing SRIM.exe in directory

            # output files from SRIM copied to desired output directory
            TRIM.copy_output_files(self.srim_exe_dir, self.srim_out_dir)

        except FileNotFoundError:
            return

        trim_data = trim_data_output.range

        x1 = np.array(trim_data.depth / 1e7)  # muon ranges, converted from angstroms to mm.

        y1 = np.array(trim_data.ions)  # SRIM has weird units for y axis

        y1_corrected = self.correct_to_counts(self.total_thickness, y1, self.stats)

        # e1 = list(trim_data.ions)

        return x1, y1_corrected

    def correct_to_counts(self, thickness, y1, total_sim_counts):
        ''' output of SRIM is odd this corrects it to counts'''
        final_bins = thickness / 100.0

        for i in range(len(y1)):
            y1[i] = y1[i] * final_bins * total_sim_counts

        return y1

    def CalcProfileWithMomBite(self, target_sample: Target, momentum: float) \
            -> tuple[np.ndarray[float], np.ndarray[float]]:
        """
        Calculate muon stopping profile for a nominal momentum with a % momentum bite defined

        Args:
            target_sample: SRIM target object
            momentum: muon momentum

        Returns:
            x and y numpy arrays containing simulation result.
        """

        sigmastep = 12  # 12 runs per momentum
        MomSigma = 0.01 * self.momentum_spread * momentum

        xres = []
        yres = []

        for i in range(sigmastep + 1):
            P = momentum - 3 * MomSigma + i * 0.5 * MomSigma  # momentum for each iteration

            # Number of simulated muons dependent on Gaussian distribution of muon momentum
            # get muon information
            muon_ion = self.get_muon(P)

            NE = int(self.stats * (1.0 / (np.sqrt(2.0 * np.pi) * MomSigma)) * np.exp(
                -0.5 * (P - momentum) ** 2 / (MomSigma ** 2)))

            x1, y1  = self.run_TRIM(target_sample, muon_ion)

            if i == 0:
                yres = y1
                xres = x1
            else:
                for index in range(0, len(y1)):
                    yres[index] = yres[index] + y1[index]

        return xres, yres

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

    def split_components(self, MomIndex: int) -> list[np.ndarray]:
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

    def get_muons_per_layer(self, comp):
        ''' gets the number of muons in a layer (normalised)'''

        counts_per_layer = [np.sum(comp[i]) for i, _ in enumerate(self.sample_layers)]

        total_count = np.sum(counts_per_layer)
        total_count_err = np.sqrt(total_count)

        res = []
        for i, layer_count in enumerate(counts_per_layer):
            layer_count_err = np.sqrt(layer_count)

            frac = layer_count / total_count

            # only calculate error for layers with counts
            if frac == 0:
                frac_err = 0
            else:
                # error propagation
                frac_err = np.sqrt((total_count_err/total_count)**2 + (layer_count_err/layer_count)**2) * frac

            res.append((round(frac, 3)*100, round(frac_err, 3)*100, round(layer_count, 3), round(layer_count_err, 3)))

        return res

    def plot_whole(self, momentum_index: int, momentum: float) -> tuple[plt.Figure, plt.Axes]:
        """
        Plots the whole stopping profile from the srim simulation

        Args:
            momentum_index: the list index
            momentum: momentum value

        Returns:
            matplotlib figure and axes objects with plotted data.
        """
        x_shift = self.plot_origin_shifts[momentum_index]

        figt, axx = plt.subplots()

        axx.plot(self.result_x[momentum_index] - x_shift, self.result_y[momentum_index])
        axx.set_xlabel('Depth ($mm$)')
        axx.set_ylabel('Number of muons')
        axx.set_title('SRIM Simulation at ' + str(round(momentum, 4)) + ' MeV/c')

        # Display layer boundaries on plot
        for i in range(len(self.sample_layers)):
            pos = self.layer_boundary_positions[i + 1]

            axx.axvline(x=pos - x_shift, color='k', linestyle='--')
            axx.text(pos - x_shift, 5, self.sample_names[i], horizontalalignment='left', rotation='vertical')

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

        x_shift = self.plot_origin_shifts[momentum_index]

        # plot components
        figt, axx = plt.subplots()
        axx.plot(self.result_x[momentum_index] - x_shift, self.result_y[momentum_index])
        axx.set_xlabel('Depth ($mm$)')
        axx.set_ylabel('Number of muons')
        axx.set_title('SRIM Simulation at ' + str(round(momentum, 4)) + ' MeV/c')

        # plot layers out plot
        for i in range(len(self.sample_layers)):
            pos = self.layer_boundary_positions[i + 1]

            axx.axvline(x=pos - x_shift, color='k', linestyle='--')
            axx.text(pos - x_shift, 5, self.sample_names[i], horizontalalignment='left', rotation='vertical')

        # break output down to components
        comp = self.split_components(momentum_index)

        # plot layers
        for i in range(len(self.sample_layers)):
            axx.plot(self.result_x[0] - x_shift, comp[i], label=self.sample_names[i])

        axx.legend()
        return figt, axx

    def get_default_srim_save_name(self, momentum: float | None = None) -> str:
        if momentum is None:
            momentum = "all"
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
                total_curve_filename = f"{momentum}MeVc_total_profile.dat"

                total_curve_data = [f"{x}, {self.result_y[row][i]}\n" for i, x in enumerate(self.result_x[row])]
                total_curve_str = "".join(header) + "".join(total_curve_data)

                zf.writestr(total_curve_filename, total_curve_str)

                for i, layer_name in enumerate(self.sample_names):
                    layer_filename =  f"{momentum}MeVc_layer{i}_profile.dat"

                    ydata_per_layer = self.split_components(row)  # list of arrays containing a y-array for each layer
                    layer_data = [f"{x}, {ydata_per_layer[i][j]}\n" for j, x in enumerate(self.result_x[row])]
                    layer_curve_str = "".join(header) + "".join(layer_data)

                    zf.writestr(layer_filename, layer_curve_str)


    def save_settings(self, sample_name, stats, srim_dir, output_dir, momentum, momentum_spread, sim_type,
                        min_momentum, max_momentum, step_momentum, scan_type, layers, target_dir):
        print('in save file')

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
            print(layer)
            file2.writelines(layer["name"] + "," + str(layer["thickness"]) + "," + str(layer.get("density", "")) + "\n")
        file2.close()

    def load_settings(self, target_dir):
        file2 = open(target_dir, "r")
        ignore = file2.readline()
        print(ignore)
        sample_name = file2.readline().strip()
        print(sample_name)
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
            print(line)

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