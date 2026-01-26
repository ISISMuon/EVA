import logging
import os
from EVA.core.app import get_config
from EVA.gui.windows.fit_table_plot.fit_table_plot_model import FitTablePlotModel
from EVA.gui.windows.fit_table_plot.fit_table_plot_view import FitTablePlotView

logger = logging.getLogger(__name__)


class FitTablePlotPresenter(object):
    def __init__(self, view, model):
        self.view = view
        self.model = model

        if get_config()["general"]["fit_table_plot_file"]:
            self.fit_table_path = get_config()["general"]["fit_table_plot_file"]

        self.view.fit_table_select_button.clicked.connect(self.browse_fit_table_file)
        self.view.plot_data_button.clicked.connect(self.plot_fit_table_data)
        self.view.save_output_button.clicked.connect(self.save_plot_data)

    def browse_fit_table_file(self):
        def_dir = get_config()["general"]["working_directory"]
        path = self.view.load_fit_table_file(
            default_dir=def_dir, file_filter="CSV files (*.csv)"
        )
        if path:
            self.fit_table_path = path
            get_config()["general"]["fit_table_plot_file"] = path
            logger.info("Selected fit table file: %s", path)

    def plot_fit_table_data(self):
        # Check if user has specified a fit table file path to read from
        # If yes, try to load the data
        if hasattr(self, "fit_table_path"):
            load_flag = self.model.load_fit_table_data(self.fit_table_path)
        else:
            logger.warning("No fit selected to load from.")
            self.view.display_error_message(message="No valid fit table loaded.")
            return
        # Get filtering parameters
        momentum_range = self.view.get_momentum_range()
        energy_range = self.view.get_energy_range()
        plot_parameter = self.view.get_plot_parameter()
        if momentum_range is None or energy_range is None:
            logger.warning("")
            return
        # If valid data was loaded, filter using user inputs and plot
        if hasattr(self.model, "fit_table_data") and load_flag == 1:
            self.model.plot_fit_table_data(momentum_range, energy_range, plot_parameter)
            self.view.plot.update_plot(self.model.fig, self.model.axs)
            self.view.update_table(self.model)
            self.view.save_output_button.setEnabled(True)
            self.plot_parameter = plot_parameter
        else:
            logger.warning(f"Fit table plotting using {self.fit_table_path} failed.")
            self.view.display_error_message(message="File not recognized.")
            return

    def save_plot_data(self):
        # If user specifies a valid .txt or .csv file path, save according the respective format
        filters = "Text Files (*.txt);;CSV Files (*.csv)"
        def_dir = get_config()["general"]["working_directory"]
        path, file_extension = self.view.get_save_file_path(
            default_dir=def_dir, file_filter=filters
        )
        if path:
            self.model.save_plot_data(path, file_extension, self.plot_parameter)
