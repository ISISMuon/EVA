import logging
from PyQt6.QtWidgets import QVBoxLayout, QTableWidgetItem
from PyQt6.QtCore import Qt

from EVA.gui.base.base_view import BaseView
from EVA.gui.ui_files.multiplot_gui import Ui_MultiPlotView  # this is the generated .py from .ui
from EVA.gui.widgets.plot.plot_widget import PlotWidget

logger = logging.getLogger(__name__)


class MultiPlotView(BaseView, Ui_MultiPlotView):
    """
    GUI for the Multi-Run Plot window.
    Loads widgets from multi_plot_view.ui and sets up dynamic elements.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Multi-Run Plot - EVA")
        self.setMinimumSize(1100, 600)

        # --- Setup PlotWidget dynamically ---
        self.plot = PlotWidget()
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.plot)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_container.setLayout(plot_layout)

        # --- Initialize checkboxes visibility ---
        self.apply_run_settings_button.setEnabled(False)

        self.det1_checkbox.hide()
        self.det2_checkbox.hide()
        self.det3_checkbox.hide()
        self.det4_checkbox.hide()

        # --- Initialize RunListTable ---
        self.RunListTable.setRowCount(50)
        self.RunListTable.setColumnCount(3)
        self.RunListTable.setHorizontalHeaderLabels(['Start', 'End', 'Step'])
        self.RunListTable.stretch_horizontal_header()

        # Initialize cells as empty
        for i in range(50):
            for j in range(3):
                self.RunListTable.setItem(i, j, QTableWidgetItem(""))

        self.binning_spin_box.setSuffix("x")

    # --- Methods to extract data from GUI ---
    def get_form_data(self):
        offset = float(self.val_multi_offset.text() or 0.0)

        table_data = []
        for i in range(50):
            try:
                start = int(self.RunListTable.item(i, 0).text())
            except Exception:
                start = 0
            try:
                end = int(self.RunListTable.item(i, 1).text())
            except Exception:
                end = 0
            try:
                step = int(self.RunListTable.item(i, 2).text())
            except Exception:
                step = 0

            table_data.append([start, end, step])

        return offset, table_data

    def get_checked_detectors(self):
        return {
            self.det1_checkbox.text(): self.det1_checkbox.isChecked(),
            self.det2_checkbox.text(): self.det2_checkbox.isChecked(),
            self.det3_checkbox.text(): self.det3_checkbox.isChecked(),
            self.det4_checkbox.text(): self.det4_checkbox.isChecked(),
        }

    def show_detector_checkboxes(self):
        """Make detector checkboxes visible after runs are loaded."""
        self.det1_checkbox.show()
        self.det2_checkbox.show()
        self.det3_checkbox.show()
        self.det4_checkbox.show()
