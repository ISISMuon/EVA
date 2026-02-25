import os
import re
import time
from zipfile import ZipFile
import subprocess
from pathlib import Path
import numpy as np
from PyQt6.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt
from EVA.core.app import get_config
from g4bl.core.shapes import Shape

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
        # self.g4bl_exe_dir = get_config()["g4bl"]["installation_directory"]
        # self.g4bl_out_dir = get_config()["g4bl"]["output_directory"]

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

    def run_g4bl(self, input_file, mypath, vis_mode=False, log_name="a_g4bl_terminal.txt"):
        cmd = ["g4bl", input_file]
        if vis_mode:
            cmd.append("viewer=best")
        log_path = Path(mypath) / log_name
        
        with open(log_path, "w", encoding="utf-8") as f:
            process = subprocess.Popen(
                cmd,
                cwd=mypath,
                stdout=f,
                stderr=subprocess.STDOUT,
            )
        return process, log_path

    def stack_layer_boundaries(self, layers: list[Shape]):
        self.layer_boundary_positions = [0]
        cumulative_thickness = 0.01
        for layer in layers:
            layer.z = cumulative_thickness + layer.thickness / 2
            cumulative_thickness += layer.thickness
            self.layer_boundary_positions.append(cumulative_thickness)
        self.total_thickness = cumulative_thickness

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

    def fetch_sample_file_for_material(self, materials = list[Shape]):
        #TODO: revert this to config after demo
        outdir = Path(r"C:\Users\chend\Desktop\Projects\g4beamline\demo_outputs")
        for material in materials:
            prefix = f"{material.name}_"
            pattern = re.compile(rf"^{re.escape(prefix)}sample(\d+)\.txt$")

            # Collect matching files with their sample number for this material
            matching_files = []
            for file in outdir.iterdir():
                if file.is_file():
                    match = pattern.match(file.name)
                    if match:
                        sample_index = int(match.group(1))
                        matching_files.append((sample_index, file))

            # Sort by sample number
            matching_files.sort(key=lambda x: x[0])

            # Yield files one by one
            for sample_index, file_path in matching_files:
                yield (material, sample_index, file_path)

    def process_sample_files(self, materials: list[Shape]):
        self.final_results = {}

        for material in materials:
            per_material_penetration_results = []
            per_material_absorption_results = []
            # iterate all files for this material
            for mat, sample_index, file_path in self.fetch_sample_file_for_material([material]):
                with open(file_path, "r", encoding="utf-8") as f:
                    # example: count number of lines in file
                    line_count = sum(1 for _ in f) - 2
                    try:
                        per_material_absorption_results.append(previous_line_count - line_count)
                    except UnboundLocalError:
                        per_material_absorption_results.append(0)
                    per_material_penetration_results.append(line_count)
                    previous_line_count = line_count

            self.final_results[material.name] = [material.sample_positions, per_material_absorption_results]
    
    def clear_output_directory(self):
        outdir = Path(r"C:\Users\chend\Desktop\Projects\g4beamline\demo_outputs")
        for file in outdir.iterdir():
            if file.is_file():
                file.unlink()