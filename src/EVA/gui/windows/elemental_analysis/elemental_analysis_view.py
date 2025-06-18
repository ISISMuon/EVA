import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QTableWidgetItem, QTreeWidgetItem, QTableWidget
)

from EVA.gui.base.base_view import BaseView
from EVA.gui.ui_files.elemental_analysis_gui import Ui_elemental_analysis
from EVA.gui.widgets.plot.plot_widget import PlotWidget

logger = logging.getLogger(__name__)


class ElementalAnalysisView(BaseView, Ui_elemental_analysis):
    """ View to provide the user interface of the elemental analysis window. """
    def __init__(self):
        """
        Initialises the gui components
        """
        super().__init__()
        self.setupUi(self)

        # Set up window
        self.setWindowTitle("Plot Window")

        # stretch all the table headers so that they resize to occupy maximum space
        self.muonic_xray_table_all.stretch_horizontal_header()
        self.muonic_xray_table_prim.stretch_horizontal_header()
        self.muonic_xray_table_sec.stretch_horizontal_header()
        self.gamma_table.stretch_horizontal_header()
        self.plotted_gammas_table.stretch_horizontal_header()
        self.plotted_mu_xrays_table.stretch_horizontal_header()
        self.peakfind_results_table.stretch_horizontal_header()

        self.peakfind_results_table.setMaximumHeight(150)

        # hide additional settings in peak find view
        self.custom_settings_container.setVisible(False)

        # set up plotwidget link
        self.plot = PlotWidget()
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.plot)
        plot_layout.setContentsMargins(0,0,0,0)
        self.plot_widget_container.setLayout(plot_layout)

        # configure peakfind results tree
        self.peakfind_results_tree.setColumnCount(5)
        self.peakfind_results_tree.setHeaderLabels(["Detector", "Peak detected", "Element", "Transition", "Error"])
        self.peakfind_results_tree.resizeColumnToContents(0)
        self.peakfind_results_tree.resizeColumnToContents(1)
        self.peakfind_results_tree.resizeColumnToContents(2)

    @staticmethod
    def display_no_match_table(table: QTableWidget):
        """
        Notifies user when no match was found at searched energy.

        Args:
            table: table to display in.
        """
        table.setRowCount(1)
        table.setItem(0,0, QTableWidgetItem("No matches found."))

        for col in range(table.columnCount()-1):
            table.setItem(0, col+1, QTableWidgetItem())

    @staticmethod
    def update_plotted_lines_table(table: QTableWidget, items: list[str]):
        """
        Update list of plotted lines in specified table

        Args:
            table: table to display in
            items: list of currently plotted lines
        """
        table.setRowCount(len(items))

        for i, item in enumerate(items):
            table.setItem(0, i, QTableWidgetItem(item))

    def toggle_peak_find_settings(self, check_state: Qt.CheckState):
        """
        Shows additional peak find settings when checked.

        Args:
            check_state: checkstate from checkbox
        """
        self.custom_settings_container.setVisible(not (check_state == Qt.CheckState.Checked))

    def update_peakfind_tree(self, result: dict):
        """
        Updates results from peak finding in peak find tree.

        Args:
            result: results to display in tree
        """
        self.peakfind_results_tree.clear()

        # iterate through result dictionary
        items = []
        for det, det_items in result.items():
            item = QTreeWidgetItem([det])

            for peak, peak_items in det_items.items():
                p_item = QTreeWidgetItem()
                p_item.setText(1, str(peak) + " keV")
                item.addChild(p_item)

                for energy in peak_items:
                    e_item = QTreeWidgetItem()
                    e_item.setText(2, energy["element"])
                    e_item.setText(3, energy["transition"])
                    e_item.setText(4, f"{energy["diff"]:.3f} keV")
                    p_item.addChild(e_item)

            items.append(item)
        self.peakfind_results_tree.addTopLevelItems(items)
