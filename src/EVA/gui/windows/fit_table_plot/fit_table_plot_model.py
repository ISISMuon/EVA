from PyQt6.QtCore import QObject
import logging
import csv
import matplotlib.pyplot as plt
from EVA.core.app import get_config
logger = logging.getLogger(__name__)

parameter_units = {"center": "KeV", "amplitude": "Counts", "sigma": "KeV"}

class FitTablePlotModel(QObject):
    def __init__(self, parent=None):
        super().__init__()
        self.fig, self.axs = plt.subplots(1)

    def load_fit_table_data(self, file_path: str):
        self.fit_table_data = []
        flag = 0
        try:
            with open(file_path, "r", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convert numeric fields immediately
                    self.fit_table_data.append({
                        "momentum": float(row["momentum"]),
                        "run_num": row["run_number"],
                        "center": {
                            "value": float(row["center_val"]),
                            "stderr": float(row["center_err"]),
                        },
                        "amplitude": {
                            "value": float(row["amplitude_val"]),
                            "stderr": float(row["amplitude_err"]),
                        },
                        "sigma": {
                            "value": float(row["sigma_val"]),
                            "stderr": float(row["sigma_err"]),
                        },
                    })
            flag = 1
            return flag
        except Exception as e:
            logger.error("Failed to load fit table CSV from %s: %s", file_path, e)
            return flag
    def filter_data_by_param(self, momentum_range: tuple[float, float], energy_range: tuple[float, float], plot_parameter: str):
            
        min_mom, max_mom = momentum_range
        min_energy, max_energy = energy_range
        
        filtered_data = []
        seen_runs = set()  # prevent multiple peaks per run

        for row in self.fit_table_data:
            momentum = row["momentum"]
            run_num = row["run_num"]

            if not (min_mom <= momentum <= max_mom):
                continue

            center_val = row["center"]["value"]

            if not (min_energy <= center_val <= max_energy):
                continue

            if run_num in seen_runs:
                logger.warning(
                    "Multiple peaks found within given constraints for run %s. Using first valid peak.",
                    run_num
                )
                continue

            seen_runs.add(run_num)

            filtered_data.append({
                "run_num": run_num,
                "momentum": momentum,
                plot_parameter: row[plot_parameter]["value"],
                "stderr": row[plot_parameter]["stderr"],
            })
        self.plot_parameter = plot_parameter
        return filtered_data
        
    def plot_fit_table_data(self, momentum_range: tuple[float, float], energy_range: tuple[float, float], plot_parameter: str):
        self.fig, self.axs = plt.subplots(1)
        filtered_data = self.filter_data_by_param(momentum_range, energy_range, plot_parameter)
        self.run_num_list = [row["run_num"] for row in filtered_data]
        self.momentum_list = [row["momentum"] for row in filtered_data]
        self.parameter_list = [row[plot_parameter] for row in filtered_data]
        self.stderr_list = [row["stderr"] for row in filtered_data]

        # Sort all lists by momentum
        combined = sorted(zip(self.momentum_list,
                            self.run_num_list,
                            self.parameter_list,
                            self.stderr_list),
                        key=lambda x: x[0])

        self.momentum_list, self.run_num_list, self.parameter_list, self.stderr_list = map(list, zip(*combined))

        for run_num, x, y, err in zip(self.run_num_list, self.momentum_list, self.parameter_list, self.stderr_list):
            self.axs.errorbar(
                x, y,
                yerr=err,
                fmt='o',             # circle marker (scatter-like)
                capsize=3,
                label=f"Run {run_num}"
            )
        self.axs.plot(self.momentum_list, self.parameter_list, linestyle='--', color='gray', alpha=0.5)
        self.axs.legend()
        self.axs.grid(True)
        
        self.axs.set_title(f"{plot_parameter.capitalize()} vs Momentum")
        self.axs.set_xlabel("Momentum (MeV/c)")
        self.axs.set_ylabel(plot_parameter.capitalize() + f" ({parameter_units.get(plot_parameter, '')})")

    def save_plot_data(self, file_path: str, file_extension: str, plot_parameter: str):
        if file_extension == "Text Files (*.txt)":
            with open(file_path, "w") as file:
                file.write(f"RunNum Momentum {plot_parameter.capitalize()} Stderr\n")
                for run_num, momentum, param_value, stderr in zip(self.run_num_list, self.momentum_list, self.parameter_list, self.stderr_list):
                    file.write(f"{run_num} {momentum} {param_value} {stderr}\n")
            logger.info("Filtered fit table data saved to %s", file_path)
        
        elif file_extension == "CSV Files (*.csv)":
            import csv
            with open(file_path, "w", newline='') as csvfile:
                fieldnames = ["RunNum", "Momentum", plot_parameter.capitalize(), "Stderr"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for run_num, momentum, param_value, stderr in zip(self.run_num_list, self.momentum_list, self.parameter_list, self.stderr_list):
                    writer.writerow({
                        "RunNum": run_num,
                        "Momentum": momentum,
                        plot_parameter.capitalize(): param_value,
                        "Stderr": stderr
                    })
            logger.info("Fit table data saved to %s", file_path)
