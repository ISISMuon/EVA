import logging
from PyQt6.QtCore import pyqtSignal

from PyQt6.QtWidgets import QPushButton, QMessageBox, QFileDialog, QTableWidgetItem

from EVA.gui.ui_files.fit_table_plot_gui import Ui_fit_table_plot
from EVA.gui.base.base_view import BaseView
from EVA.core.app import get_config

logger = logging.getLogger("__main__")

class FitTablePlotView(BaseView, Ui_fit_table_plot):
    plot_requested_s = pyqtSignal(str)
    save_array_requested_s = pyqtSignal(str)
    select_fit_table_s = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setMinimumSize(1000, 700)
        self.setWindowTitle("Fit Table Plotting - EVA")
        self.set_fit_table_file_label(get_config()["general"]["fit_table_plot_file"])
        self.save_output_button.setEnabled(False)
    def set_fit_table_file_label(self, filename: str):
        if filename:
            self.loaded_fit_table_label.setText(filename)
        else:
            self.loaded_fit_table_label.setText("No file loaded.")
    
    def load_fit_table_file(self, default_dir: str = "", file_filter: str = "JSON files (*.json)") -> str:
        """Open a file dialog to select a fit table file."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Fit Table File", default_dir, file_filter)
        if path:
            self.set_fit_table_file_label(path)
            return path
        else:
            None

    def get_momentum_range(self) -> tuple[float, float]:
        try:
            min_momentum = float(self.mom_range_min_line_edit.text())
            max_momentum = float(self.mom_range_max_line_edit.text())
        except ValueError:
            self.display_error_message(message="Invalid momentum range values.")
            return None
        return (min_momentum, max_momentum)
    
    def get_energy_range(self) -> tuple[float, float]:
        try:
            min_energy = float(self.e_range_min_line_edit.text())
            max_energy = float(self.e_range_max_line_edit.text())
        except ValueError:
            self.display_error_message(message="Invalid energy range values.")
            return None
        return (min_energy, max_energy)
    
    def get_plot_parameter(self) -> str:
        return self.plot_parameter_comboBox.currentText().lower()
    
    def get_save_file_path(self, default_dir: str, file_filter: str) -> str:
        # QFileDialog.getSaveFileName returns a tuple (filename, selected_filter)
        filename, selected_filter = QFileDialog.getSaveFileName(self, 'Save File', directory=default_dir, filter=file_filter)
        if filename:
            # Ensure file has correct extension
            if selected_filter.startswith("Text") and not filename.endswith(".txt"):
                filename += ".txt"
            elif selected_filter.startswith("CSV") and not filename.endswith(".csv"):
                filename += ".csv"
            logging.info("Saving fit table data to %s", filename)
            return filename, selected_filter
        return None, None
    
    def update_table(self, model):
        self.fit_table_data_table.clearContents()
        self.fit_table_data_table.setRowCount(0)

        # Set table headers
        self.fit_table_data_table.setColumnCount(4)

        for run_num, momentum, parameter, stderr in zip(model.run_num_list, model.momentum_list, model.parameter_list, model.stderr_list):
            row_position = self.fit_table_data_table.rowCount()
            self.fit_table_data_table.insertRow(row_position)
            self.fit_table_data_table.setItem(row_position, 0, QTableWidgetItem(str(run_num)))
            self.fit_table_data_table.setItem(row_position, 1, QTableWidgetItem(f"{momentum:.2f}"))
            self.fit_table_data_table.setItem(row_position, 2, QTableWidgetItem(f"{parameter:.4f}"))
            self.fit_table_data_table.setItem(row_position, 3, QTableWidgetItem(f"{stderr:.4f}"))