import logging
from PyQt6.QtCore import pyqtSignal

from PyQt6.QtWidgets import (
    QPushButton,
    QMessageBox,
    QFileDialog
)

from EVA.gui.ui_files.peak_fit_gui import Ui_peak_fit
from EVA.gui.base.base_view import BaseView
from EVA.core.app import get_config
from EVA.gui.windows.peakfit.peakfit_presenter import PeakFitPresenter

logger = logging.getLogger("__main__")

class PeakFitView(BaseView, Ui_peak_fit):
    peak_table_cell_changed_s = pyqtSignal(tuple)
    bckg_table_cell_changed_s = pyqtSignal(tuple)

    save_params_s = pyqtSignal(str)
    load_params_s = pyqtSignal(str)
    save_fit_report_s = pyqtSignal(str)
    peak_removal_requested_s = pyqtSignal(str)
    model_removal_requested_s = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setMinimumSize(1000, 700)
        self.setWindowTitle("Peak Fitting - EVA")

        # resize all table headers to fit screen nicely
        self.initial_bg_params_table.stretch_horizontal_header([0])
        self.initial_bg_params_table.setColumnWidth(0, 80)

        self.fitted_bg_params_table.stretch_horizontal_header([0])
        self.fitted_bg_params_table.setColumnWidth(0, 80)

        self.initial_model_bg_params_table.stretch_horizontal_header([0])
        self.initial_model_bg_params_table.setColumnWidth(0, 80)
        self.initial_model_bg_params_table.verticalHeader().setVisible(False)

        self.fitted_model_bg_params_table.stretch_horizontal_header([0])
        self.fitted_model_bg_params_table.setColumnWidth(0, 80)
        self.fitted_model_bg_params_table.verticalHeader().setVisible(False)

        self.initial_peak_params_table.stretch_horizontal_header([0])
        self.initial_peak_params_table.setColumnWidth(0, 30)
        self.initial_peak_params_table.verticalHeader().setVisible(False)

        self.fitted_peak_params_table.stretch_horizontal_header([0])
        self.fitted_peak_params_table.setColumnWidth(0, 30)
        self.fitted_peak_params_table.verticalHeader().setVisible(False)

        self.initial_model_params_table.stretch_horizontal_header([0])
        self.initial_model_params_table.setColumnWidth(0, 100)
        self.initial_model_params_table.verticalHeader().setVisible(False)

        self.fitted_model_params_table.stretch_horizontal_header([0])
        self.fitted_model_params_table.setColumnWidth(0, 100)
        self.fitted_model_params_table.verticalHeader().setVisible(False)

        self.cancel_add_peak_button.hide()
        self.add_peak_label.hide()

    def update_e_range_form(self, e_range: list):
        # Writes new energy range to energy range form
        self.e_range_min_line_edit.setText(f"{e_range[0]:.2f}")
        self.e_range_max_line_edit.setText(f"{e_range[1]:.2f}")

    def update_model_e_range_form(self, e_range: list):
        # Writes new energy range to energy range form
        self.model_e_range_min_line_edit.setText(f"{e_range[0]:.2f}")
        self.model_e_range_max_line_edit.setText(f"{e_range[1]:.2f}")

    def setup_peakfit_table_options(self, col: int, param_ids: list):
        for row, param_id in enumerate(param_ids):
            btn = QPushButton("Remove")  # TODO make this a nice icon button instead
            btn.clicked.connect(lambda x, p_id=param_id: self.peak_removal_requested_s.emit(p_id))
            self.initial_peak_params_table.setCellWidget(row, col, btn)

    def setup_modelfit_table_options(self, col: int, param_ids: list):
        for row, param_id in enumerate(param_ids):
            btn = QPushButton("Remove")  # TODO make this a nice icon button instead
            btn.clicked.connect(lambda x, p_id=param_id: self.model_removal_requested_s.emit(p_id))
            self.initial_model_params_table.setCellWidget(row, col, btn)

    def get_load_file_path(self, default_dir: str, file_filter: str) -> str:
        file = QFileDialog.getOpenFileName(self, 'Load File', directory=default_dir, filter=file_filter)
        if file:
            return file[0]

    def get_save_file_path(self, default_dir: str, file_filter: str) -> str:
        file = QFileDialog.getSaveFileName(self, 'Save File', directory=default_dir, filter=file_filter)
        if file:
            return file[0]

    def save_fit_report(self) -> str:
        config = get_config()
        file = QFileDialog.getSaveFileName(self, 'Save File', directory=config["general"]["working_directory"])
        if file:
            return file[0]

    def prompt_add_peak(self, pos) -> bool:
        reply = QMessageBox.question(self, 'Add peak', f"Do you wish to add a peak at {pos:.1f} keV?",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                                QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes