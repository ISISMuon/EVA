import logging
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QErrorMessage, QCheckBox, QSpacerItem, QHBoxLayout
)

from EVA.gui.base.base_view import BaseView
from EVA.gui.widgets.plot.plot_widget import PlotWidget
logger = logging.getLogger(__name__)

class MultiPlotView(BaseView):
    """
        This window is the GUI for the multiplot window

    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle("Multi-Plot Window ")
        self.setMinimumSize(1100, 600)

        # set up containers and layouts
        layout = QGridLayout()
        self.side_panel = QWidget()
        side_panel_layout = QVBoxLayout()

        self.plot_container = QWidget()
        self.plot_container_layout = QVBoxLayout()

        self.settings_form = QWidget()
        settings_form_layout = QFormLayout()

        # set size constraints
        self.side_panel.setMaximumWidth(400)

        # create empty plot widget as placeholder
        self.plot = PlotWidget()

        # sets up button
        self.plot_multi = QPushButton('Load and Plot Multi Spectra')

        # label for offset
        self.lab_multi_offset = QLabel('Offset')

        # input for the value of the y-axis offset
        self.val_multi_offset = QLineEdit('0.0')

        spacer = QSpacerItem(0, 20)

        # checkboxes to select which detectors to plot for (not saved in config)
        self.detector_selections = QWidget()
        detector_select_layout = QHBoxLayout()

        self.ge1_checkbox = QCheckBox("2099 (GE1)")
        self.ge2_checkbox = QCheckBox("3099 (GE2)")
        self.ge3_checkbox = QCheckBox("4099 (GE3)")
        self.ge4_checkbox = QCheckBox("5099 (GE4)")

        self.ge1_checkbox.setChecked(True)
        self.ge3_checkbox.setChecked(True)


        self.detector_selections.setLayout(detector_select_layout)
        detector_select_layout.addWidget(self.ge1_checkbox)
        detector_select_layout.addWidget(self.ge2_checkbox)
        detector_select_layout.addWidget(self.ge3_checkbox)
        detector_select_layout.addWidget(self.ge4_checkbox)

        # makes the table for the list of run numbers to plot
        self.RunListTable = QTableWidget()
        self.RunListTable.setColumnCount(3)
        self.RunListTable.setRowCount(50)
        self.RunListTable.setMinimumWidth(380)
        self.RunListTable.setHorizontalHeaderLabels(['Start', 'End', 'Step'])

        # sets each point in the table to a blank
        for i in range(3):
            for j in range(50):
                self.RunListTable.setItem(j, i, QTableWidgetItem(''))

        # add all components to layouts
        self.settings_form.setLayout(settings_form_layout)
        settings_form_layout.addRow(self.lab_multi_offset, self.val_multi_offset)
        settings_form_layout.addRow(self.plot_multi)

        self.side_panel.setLayout(side_panel_layout)

        side_panel_layout.addWidget(self.settings_form)
        side_panel_layout.addWidget(self.detector_selections)
        side_panel_layout.addWidget(self.RunListTable)

        self.setLayout(layout)
        layout.addWidget(self.side_panel, 0, 0)
        layout.addWidget(self.plot, 0, 1, -1, 1)

    def get_form_data(self):
        plot_detectors = {
            "GE1": self.ge1_checkbox.isChecked(),
            "GE2": self.ge2_checkbox.isChecked(),
            "GE3": self.ge3_checkbox.isChecked(),
            "GE4": self.ge4_checkbox.isChecked(),
        }

        offset = float(self.val_multi_offset.text())

        table_data = []

        #read table from GUI
        for i in range(50):
            try:
                start = int(self.RunListTable.item(i,0).text())
            except:
                start = 0
            #print('start', start)
            try:
                end = int(self.RunListTable.item(i,1).text())
                #print('end',end)
            except:
                end = 0
            #print('end', end)
            try:
                step = int(self.RunListTable.item(i,2).text())
            except:
                step = 0

            table_data.append([start,end,step])

        return offset, table_data, plot_detectors