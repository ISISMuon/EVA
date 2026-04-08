import subprocess
import numpy as np
from pathlib import Path
from g4bl.core.input_writer import InputWriter

class G4BL(object):
    def __init__(self, sim_type, target, muon_num, momentum, mom_err, total_thickness, verbosity, instance=""):
        self.sim_type = sim_type
        self.total_thickness = total_thickness
        self.verbosity = verbosity
        self.instance = instance
        self.writer = InputWriter(targets=target, muon_num=muon_num, momentum=momentum, mom_err=mom_err, beam_off=False, instance=instance)

    def run(self, g4bl_exe_dir, output_dir, vis_mode=False):
        log_file = Path(output_dir) / f"g4bl_terminal{self.instance}.txt"
        input_file = Path(output_dir) / f"input_file{self.instance}.g4bl"
        with open(input_file, "w") as f:
            f.write(self.writer.input_string)
        exe_path = Path(g4bl_exe_dir) / "g4bl"
        cmd = [str(exe_path), f"input_file{self.instance}.g4bl"]
        if vis_mode:
            cmd.append("viewer=best")
        
        with open(log_file, "w", encoding="utf-8") as f:
            process = subprocess.Popen(
                cmd,
                cwd=output_dir,
                stdout=f,
                stderr=subprocess.STDOUT,
            )
        process.wait()
        if self.sim_type == "Stack":
            data = self.process_stack_data(file_path=Path(output_dir) / f"out_file{self.instance}.txt")
        return data

    def filter_data_array(self, data):
        if self.verbosity==1:
            z = data[:, 2]
            return z[(z >= 0) & (z <= self.total_thickness)]
        elif self.verbosity==2:
            x = data[:, 0]
            y = data[:, 1]
            z = data[:, 2]

            mask = (
                (x >= 0) & (x <= self.total_thickness) &
                (y >= 0) & (y <= self.total_thickness) &
                (z >= 0) & (z <= self.total_thickness)
            )

            return x[mask], y[mask], z[mask]

    def process_stack_data(self, file_path):
        data = np.genfromtxt(file_path, comments ="#")
        filtered_data = self.filter_data_array(data)
        return filtered_data