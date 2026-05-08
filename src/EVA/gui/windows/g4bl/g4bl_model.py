import os
import time
from zipfile import ZipFile
import subprocess
from pathlib import Path
import io
import numpy as np
from PyQt6.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt

from EVA.util.path_handler import get_path
from EVA.core.app import get_config
from g4bl import G4BL, Shape, Material
from EVA.core.physics import rebin

class G4blModel(QObject):
    simulation_error_s = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Default layers to display in stack layer table
        self.stack_input = [{
                "name": "Beamline_Window",
                "thickness": 0.05,
                "density": 1.4,
            },
            {
                "name": "Compressed_Air",
                "thickness": 0.067,
                "density": round(1500 * 1.20479e-3, 4), # air layer compressed from 150mm to 0.1mm to optimise bins
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
        self.stats = 5000
        self.bin_resolution = 200
        self.g4bl_exe_dir = get_config()["g4bl"]["installation_directory"]
        self.g4bl_out_dir = get_config()["g4bl"]["output_directory"]
        self.verbosity = 1
        self.sim_type = "Mono"
        self.momentum = [27.]
        self.momentum_spread = 4.
        self.min_momentum = 21.
        self.max_momentum = 30.
        self.step_momentum = 1.
        self.sim_method = "Stack"
        self.scan_type = "No"
        self.g4bl_elements, self.g4bl_compounds, self.g4bl_materials = self.load_material_database()
        ####################

        # simulation results
        self.result_x = None # raw results
        self.result_y = None

        self.ydata_per_layer = None
        self.counts_per_layer = None
        self.counts_per_layer_err = None
        self.proportions_per_layer = None
        self.proportions_per_layer_err = None
        self.figs = {}

        # for storing an x-axis shift for each momentum plot (one for each momentum)
        self.default_origin_position = 0
        self.stopping_plot_origin_shifts = []
        self.depth_plot_origin_shift = 0
        self.cancel_sim = False
        self.simulation_times = None # to store the time taken for each simulation

    def create_sample_shape_objects(self, layers: list[dict]):
        self.sample_layers = []
        self.sample_names = []
        if self.sim_method == "Stack":
            for i, layer in enumerate(layers):
                sample_name = layer.get("name")
                density = layer.get("density")
                if sample_name == "Compressed_Air":
                    sample_material = Material(mat_name="Compressed_Air", elements={}, density=1500 * 1.20479e-3)
                    layer['thickness'] = 0.067
                elif sample_name == "Beamline_Window":
                    sample_material = Material(mat_name="Beamline_Window", elements={}, density=1.4)
                    layer['thickness'] = 0.05
                else:
                    if sample_name in self.g4bl_compounds:
                        sample_material = Material(mat_name=f"{sample_name}_{i}", elements={}, density=density, phase=0)
                        Material.flag = "compound"
                    else:
                        sample_material = Material.from_formula(mat_name=f"{sample_name}_{i}", chemical_formula=sample_name, density=density, phase=0)
                        Material.flag = "undefined"
                        if sample_name in self.g4bl_elements:
                            Material.flag = "element"

                layer_thickness = layer.get("thickness")
                position = self.total_thickness + layer_thickness / 2
                self.total_thickness += layer_thickness
                this_slab = Shape.create(shape_type="slab", shape_name = f"slab{i}", color="0,0,1", material=sample_material, thickness=layer_thickness)
                this_slab.z = position
                self.sample_layers.append(this_slab)
                formatted_sample_name = sample_name.replace("_", " ").capitalize()
                self.sample_names.append(formatted_sample_name)

    def start_g4bl_simulation(self, progress_callback: pyqtSignal) -> dict:
        """
        Runs the g4bl simulation using parameters set in the model.
        """
        # Calculate momentum array if momentum scan is wanted
        if self.scan_type == 'Yes':
            self.momentum = np.round(np.arange(start=self.min_momentum, stop=self.max_momentum, step=self.step_momentum), 5)

        if self.sim_type == "Mono":
            momentum_spread = 0
        else:
            momentum_spread = self.momentum_spread
        # Caulculate number of sims 
        total_sims = len(self.momentum)
        self.simulation_times = np.zeros_like(self.momentum)

        # (re)-initialise empty data arrays and zero variables
        self.result_x = np.zeros(shape=(len(self.momentum), self.bin_resolution))
        self.result_y = np.zeros_like(self.result_x)
        self.total_thickness = 0
        # create shape objects using parameters in sample setup table
        self.create_sample_shape_objects(self.stack_input)
        simulation_count = 0
        for momentum_index, mom in enumerate(self.momentum):
            t0 = time.time_ns()
            progress_callback.emit({
                "type": "sim_start",
                "completed_sims": simulation_count,  # sims fully done before this one
                "muons_per_sim": int(self.stats),
                "total_muons": int(total_sims * self.stats),
            })
            x, y, cancel_flag = self.run_G4BL(momentum=mom, momentum_spread=momentum_spread, progress_callback=progress_callback)
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
            estimated_time_left = self.estimate_time_left(simulation_count, len(self.momentum))
            # report progress to gui
            progress_callback.emit(
                {"type": "iteration_end", "estimated_time_left": estimated_time_left})

        # calculate the layer boundary positions as a cumulative sum of layer thicknesses
        self.layer_boundary_positions = self.get_layer_boundary_positions()

        self.ydata_per_layer = np.zeros(shape=(len(self.sample_layers), len(self.momentum), self.bin_resolution))
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
            with np.errstate(divide='ignore', invalid='ignore'):
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

        # after sucessful run, update g4bl installation directory in config
        get_config()["g4bl"]["installation_directory"] = self.g4bl_exe_dir
        get_config()["g4bl"]["output_directory"] = self.g4bl_out_dir

        return {"status": "success"}
    
    def run_G4BL(self, momentum: float, momentum_spread: float, progress_callback: pyqtSignal) -> tuple[list | None, list | None, int,]:
        """
        Runs G4BL simulation for a single momentum.

        Args:
            target: sample target
            muon: muon object
            n_muons: number of muons to simulate for

        Returns: xdata, ydata, cancel_flag - 1 is simulation stop was requested while simulating, 0 if all good
        """

        if self.cancel_sim:
            return None, None, 1
        if self.sim_method == "Stack":
            verbosity = 1
            g4bl_sim = G4BL(sim_type="Stack", target=self.sample_layers, muon_num=self.stats,
                            momentum=momentum, mom_err=momentum_spread / 100,
                            total_thickness=self.total_thickness, verbosity=verbosity)
            muon_final_z_position = g4bl_sim.run(
                self.g4bl_exe_dir, self.g4bl_out_dir, progress_callback=progress_callback
            )
            bin_center, counts = rebin.nxs_rebin(x_data=muon_final_z_position, bin_num=self.bin_resolution, bin_range=(0, self.total_thickness))
            return bin_center, counts, 0

        elif self.sim_method == "Manual Placement":
            verbosity = 2



    def extract_geometry_error_descriptions(self, log_path):
        descriptions = []
        with open(log_path, encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if "G4Exception: Geometry Error" in line:
                desc_index = i + 3

                if desc_index < len(lines):
                    desc_line = lines[desc_index].strip()
                    if "description:" in desc_line:
                        desc_line = desc_line.split("description:", 1)[1].strip()

                    descriptions.append(desc_line)
        return descriptions[::2]

        
    def get_layer_boundary_positions(self) -> np.ndarray[float]:
        """
        Calculate the (cumulative) boundary positions for all layers.

        Returns:
            numpy array containing layer boundary positions, includes start point at 0.0
        """

        layer_thicknesses = [float(layer["thickness"]) for layer in self.stack_input]
        # insert 0.0 to start of list
        layer_thicknesses.insert(0, 0.)

        boundaries = np.cumsum(np.array(layer_thicknesses, dtype=float))

        # cast to numpy array and shift
        return boundaries

    def split_layers(self, MomIndex: int) -> list[np.ndarray]:
        """
        Splits up the G4BL result into list of np.ndarrays, one for each layer, containing only the y-values in that
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
        Plots the whole stopping profile from the g4bl simulation

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
        axx.set_title(f'G4BL Simulation at {momentum:.2f} MeV/c')

        axx.plot(self.result_x[momentum_index] - x_shift, self.result_y[momentum_index])

        y_lim_upper = axx.get_ylim()[1]

        # Display layer boundaries on plot
        for i in range(len(self.sample_layers)):
            pos = self.layer_boundary_positions[i + 1]

            axx.axvline(x=pos - x_shift, color='k', linestyle='--')
            axx.text(pos - x_shift, y_lim_upper * 0.02, self.sample_names[i], horizontalalignment='right', rotation='vertical')

        return figt, axx

    def plot_components(self, momentum_index: int, momentum: float) -> tuple[plt.Figure, plt.Axes]:
        """
        Plots the whole stopping profile from the g4bl simulation and shows the profile from each layer separately.

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
        axx.set_title(f'G4BL Simulation at {momentum:.2f} MeV/c')

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
        self.figs[momentum_index] = axx
        return figt, axx

    def plot_depth_profile(self) -> tuple[plt.Figure, plt.Axes]:
        """
        Plots the whole stopping profile from the g4bl simulation.

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

        # boundaries 
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

    def load_material_database(self):
        # Read elements
        with open(get_path("src/EVA/databases/NIST_dataset/g4bl_predefined_elements.txt"), "r") as f:
            elements = [line.strip() for line in f if line.strip()]
        
        # Read compounds
        with open(get_path("src/EVA/databases/NIST_dataset/g4bl_predefined_compounds.txt"), "r") as f:
            compounds = [line.strip() for line in f if line.strip()]
        
        # Combine both and sort by length then lexicographically
        combined = sorted(elements + compounds, key=lambda x: (len(x), x))
        
        return elements, compounds, combined
        
    def get_default_g4bl_plot_save_name(self, momentum: float | None = None) -> str:
        if momentum is None:
            return os.path.join(f"{get_config()['general']['working_directory']}", "G4BL_stopping_profile_plots.zip")
        else:
            momentum = f"{momentum:.1f}"
        return os.path.join(f"{get_config()['general']['working_directory']}", f"G4BL_{momentum}_stopping_profile.png")

    def get_default_g4bl_save_name(self, momentum: float | None = None) -> str:
        if momentum is None:
            momentum = "all"
        else:
            momentum = f"{momentum:.5f}"
        return os.path.join(
            f"{get_config()['general']['working_directory']}",
            f"G4BL_{momentum}_MeVc.zip",
        )

    
    def save_plot(self, path: str, rows: list | int | None = None):
        if isinstance(rows, int):
            fig = self.figs[rows].figure  # get the matplotlib Figure object from the Axes
            fig.savefig(path, bbox_inches='tight')  # save the figure

        if rows is None:
            with ZipFile(path, 'w') as zipf:
                for i, momentum_value in enumerate(self.momentum):
                    if i not in self.figs:
                        continue  # skip rows with no plot

                    fig = self.figs[i].figure

                    # Save figure to a bytes buffer
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight')
                    buf.seek(0)

                    # Use a descriptive filename inside the zip
                    filename = f"SRIM_plot_momentum_{momentum_value:.1f}.png"
                    zipf.writestr(filename, buf.read())
                    buf.close()

    def save_sim(self, path: str, rows: list | int | None = None):
        if isinstance(rows, int):
            rows = [rows]

        if rows is None:
            rows = [i for i, _ in enumerate(self.momentum)]

        # prepare header text (will be the same for all files)
        header = [
            (
                f"Layer {i}: {self.sample_names[i]} at ({self.layer_boundary_positions[i]}mm, "
                f"{self.layer_boundary_positions[i + 1]}mm)\n"
            )
            for i, layer in enumerate(self.sample_layers)
        ]

        header.append("\nDepth (mm), Muon count\n")

        # create zip archive
        with ZipFile(path, "w") as zf:
            for row in rows:
                momentum = self.momentum[row]
                total_curve_filename = f"{momentum:.5f}MeVc_total_profile.dat"

                total_curve_data = [
                    f"{x}, {self.result_y[row][i]}\n"
                    for i, x in enumerate(self.result_x[row])
                ]
                total_curve_str = "".join(header) + "".join(total_curve_data)

                zf.writestr(total_curve_filename, total_curve_str)

                for i, layer_name in enumerate(self.sample_names):
                    layer_filename = f"{momentum:.5f}MeVc_layer{i}_profile.dat"

                    ydata_per_layer = self.split_layers(
                        row
                    )  # list of arrays containing a y-array for each layer
                    layer_data = [
                        f"{x}, {ydata_per_layer[i][j]}\n"
                        for j, x in enumerate(self.result_x[row])
                    ]
                    layer_curve_str = "".join(header) + "".join(layer_data)

                    zf.writestr(layer_filename, layer_curve_str)
                    
    @staticmethod
    def is_valid_path(path):
        return os.path.exists(path)

    @staticmethod
    def close_figure(fig):
        plt.close(fig)