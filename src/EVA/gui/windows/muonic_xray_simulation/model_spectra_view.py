import logging
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QGridLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QComboBox, QLineEdit, QHBoxLayout, QCheckBox,
    QMessageBox, QScrollArea
)

from EVA.gui.base.base_view import BaseView
from EVA.gui.windows.muonic_xray_simulation.element_selector_widget import ElementSelectorWidget
from EVA.gui.widgets.plot.plot_widget import PlotWidget
from EVA.gui.windows.muonic_xray_simulation.model_spectra_presenter import ModelSpectraPresenter

logger = logging.getLogger(__name__)


class ModelSpectraView(BaseView):
    on_simulation_start_s = pyqtSignal()
    on_gui_initialised_s = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Muonic X-ray Simulations - EVA")
        self.init_gui()

        self.layout().setContentsMargins(0, 0, 0, 0)

    def init_gui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.side_panel_scroll = QScrollArea()
        self.side_panel_scroll.setWidgetResizable(True)
        self.side_panel = QWidget(self.side_panel_scroll)
        self.side_panel_scroll.setWidget(self.side_panel)

        self.side_panel_layout = QVBoxLayout()
        self.side_panel.setLayout(self.side_panel_layout)

        self.element_list = []
        self.element_selector = ElementSelectorWidget()

        # Energy range selection
        self.e_range_form = QWidget()
        self.e_range_form_layout = QHBoxLayout()
        self.e_range_form.setLayout(self.e_range_form_layout)
        self.e_range_form_layout.setContentsMargins(0, 0, 0, 0)

        self.e_min = QLineEdit()
        self.e_max = QLineEdit()
        self.e_range_auto = QCheckBox("Auto")
        self.e_range_auto.setChecked(True)

        self.e_range_form_layout.addWidget(QLabel("Start"))
        self.e_range_form_layout.addWidget(self.e_min)
        self.e_range_form_layout.addWidget(QLabel("Stop"))
        self.e_range_form_layout.addWidget(self.e_max)
        self.e_range_form_layout.addWidget(self.e_range_auto)

        # Plot settings
        self.plot_settings_layout = QGridLayout()
        self.plot_settings = QWidget()
        self.plot_settings.setLayout(self.plot_settings_layout)
        self.plot_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.step_label = QLabel("Step size")
        self.step_line_edit = QLineEdit("1")
        self.show_components_box = QCheckBox("Show components")
        self.show_components_box.clicked.connect(self.on_show_components)
        self.show_primary = QCheckBox("Show primary transitions")
        self.show_secondary = QCheckBox("Show secondary transitions")
        self.show_primary.setChecked(True)
        self.show_secondary.setChecked(True)

        self.select_notation_label = QLabel("Select notation")
        self.select_notation = QComboBox()
        self.select_notation.addItems(["Siegbahn (only major lines)", "Spectroscopic", "IUPAC"])

        self.select_notation_label.hide()
        self.select_notation.hide()

        self.plot_settings_layout.addWidget(self.step_label, 0, 0, 1, 1)
        self.plot_settings_layout.addWidget(self.step_line_edit, 0, 1, 1, 3)
        self.plot_settings_layout.addWidget(self.show_components_box, 1, 0, 1, -1)
        self.plot_settings_layout.addWidget(self.show_primary, 2, 0, 1, -1)
        self.plot_settings_layout.addWidget(self.show_secondary, 3, 0, 1, -1)
        self.plot_settings_layout.addWidget(self.select_notation_label, 4, 0, 1, -1)

        self.plot_settings_layout.addWidget(self.select_notation, 5, 0, 1, -1)
        self.detectors = [QCheckBox("GE1"), QCheckBox("GE2"), QCheckBox("GE3"), QCheckBox("GE4")]
        self.detector_names = ["GE1", "GE2", "GE3", "GE4"]
        self.plot_settings_layout.addWidget(QLabel("Select detectors"), 6, 0, 1, -1)
        self.detectors[0].setChecked(True)

        for i, detector in enumerate(self.detectors):
            self.plot_settings_layout.addWidget(detector, 7, i)

        # start button
        self.start_button = QPushButton("Simulate Spectrum")
        self.start_button.clicked.connect(self.simulate)

        # add everything to side panel
        self.side_panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.side_panel_layout.addWidget(QLabel("Select energy range"))
        self.side_panel_layout.addWidget(self.e_range_form)
        self.side_panel_layout.addSpacing(25)

        self.side_panel_layout.addWidget(QLabel("Select elements"))
        self.side_panel_layout.addWidget(self.element_selector)
        self.side_panel_layout.addSpacing(25)

        self.side_panel_layout.addWidget(QLabel("Plot settings"))
        self.side_panel_layout.addWidget(self.plot_settings)
        self.side_panel_layout.addSpacing(50)

        self.side_panel_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.plot = PlotWidget()

        # add side panel and plot to main gui
        self.side_panel_scroll.setMaximumWidth(300)
        layout.addWidget(self.side_panel_scroll)
        layout.addWidget(self.plot)

    def populate_gui(self, element_list):
        self.element_list = element_list
        self.element_selector.set_elements(element_list)
        self.element_selector.add_element()

    def on_auto_e_range_click(self):
        check = self.e_range_auto.isChecked()
        self.e_min.setText("")
        self.e_max.setText("")

    def on_show_components(self):
        check = self.show_components_box.isChecked()
        self.select_notation.setVisible(check)
        self.select_notation_label.setVisible(check)

    def get_form_data(self):
        try:
            detector_buttons_checked = [button.isChecked() for button in self.detectors]
            detectors = [detector for i, detector in enumerate(self.detector_names) if detector_buttons_checked[i]]

            data = {
                "elements": self.element_selector.get_elements(),
                "proportions": self.element_selector.get_ratios(),
                "detectors": detectors,
                "show_components": self.show_components_box.isChecked(),
                "dx": float(self.step_line_edit.text()),
                "show_primary": self.show_primary.isChecked(),
                "show_secondary": self.show_secondary.isChecked()
            }

            if not self.show_primary.isChecked() and not self.show_secondary.isChecked():
                _ = QMessageBox.critical(self, "Error",
                                         "No transitions selected. Please select at least one transition type "
                                         "to simulate.")
                logger.error("No transitions selected - simulation aborted.")
                return

            if len(data["elements"]) == 0:
                _ = QMessageBox.critical(self, "Error",
                                         "No elements added. Please add at least one element "
                                         "to simulate for.")
                logger.error("No elements selected - simulation aborted.")
                return

            if len(data["detectors"]) == 0:
                _ = QMessageBox.critical(self, "Error",
                                         "No detectors selected. Please select at least one detector "
                                         "to simulate for.")
                logger.error("No detectors selected - simulation aborted.")
                return

            if self.show_components_box.isChecked():
                data["notation"] = self.select_notation.currentIndex()

            if not self.e_range_auto.isChecked():
                data["e_range"] = [float(self.e_min.text()), float(self.e_max.text())]

                # Avoid having to run more than 1M points
                if data["e_range"][1] * data["dx"] - data["e_range"][0] * data["dx"] > 1e6:
                    _ = QMessageBox.critical(self, "Error",
                                             "Please select a larger step size or a narrower energy range.")
                    logger.error("No transitions selected - simulation aborted.")
                    return
            else:
                # Don't allow auto range with step size of less than 0.01
                if data["dx"] < 0.01:
                    _ = QMessageBox.critical(self, "Error",
                                             "Please select a larger step size or a narrower energy range.")
                    logger.error("Step size to small for auto range - simulation aborted.")
                    return
            return data

        except ValueError:
            _ = QMessageBox.critical(self, "Error",
                                     "Invalid form data.")
            logger.error("Invalid for data - simulation aborted.")

    def set_form_data(self, data):
        # Add all elements and ratios
        element_selector = self.element_selector
        element_selector.element_selector_items = []

        for i, element in enumerate(data["elements"]):
            element_selector.add_element()

            element_cbox = element_selector.element_selector_items[-1].element_selection_cbox
            ratio_line_edit = element_selector.element_selector_items[-1].ratio_line_edit

            element_cbox.setCurrentText(element)
            ratio_line_edit.setText(str(data["proportions"][i]))

        # Set energy range
        e_range = data.get("e_range", None)
        if e_range is not None:
            self.e_min.setText(str(e_range[0]))
            self.e_min.setText(str(e_range[1]))
            self.e_range_auto.setChecked(False)

        # Set up plot settings
        show_primary = data.get("show_primary", None)
        show_secondary = data.get("show_secondary", None)
        show_components = data.get("show_components", None)
        detectors = data.get("detectors", None)
        notation = data.get("notation", None)
        dx = data.get("dx", None)

        if show_primary is not None:
            self.show_primary.setChecked(show_primary)

        if show_secondary is not None:
            self.show_secondary.setChecked(show_secondary)

        if show_components is not None:
            self.show_components_box.setChecked(show_components)

        if detectors is not None:
            for i, det in enumerate(self.detectors):
                if self.detector_names[i] in detectors:
                    det.setChecked(True)
                else:
                    det.setChecked(False)

        if dx is not None:
            self.step_line_edit.setText(str(dx))

        if notation is not None:
            self.select_notation.setCurrentIndex(notation)

    def simulate(self):
        self.on_simulation_start_s.emit()

    def update_plot(self, fig, axs):
        self.plot.update_plot(fig, axs)
