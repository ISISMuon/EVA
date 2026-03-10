import time
import logging

from copy import copy
from idlelib.configdialog import font_sample_text

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QWidget
from matplotlib import pyplot as plt

from EVA.util.path_handler import get_path
from EVA.util.worker import Worker

logger = logging.getLogger(__name__)

from EVA.core.app import get_config, get_app


class G4blPresenter(QWidget):
    def __init__(self, view, model, parent=None):
        super().__init__(parent)
        self.view = view
        self.model = model

        self.view.sample_name_linedit.setText("Sample")
        self.view.momentum_linedit.setText(str(self.model.momentum[0]))
        self.view.momentum_spread_linedit.setText(str(self.model.momentum_spread))
        self.view.min_momentum_linedit.setText(str(self.model.min_momentum))
        self.view.max_momentum_linedit.setText(str(self.model.max_momentum))
        self.view.momentum_step_linedit.setText(str(self.model.step_momentum))
        # self.view.g4bl_exe_dir_linedit.setText(str(self.model.g4bl_exe_dir))
        # self.view.g4bl_out_dir_linedit.setText(str(self.model.g4bl_out_dir))
        self.view.stats_linedit.setText(str(self.model.stats))
        self.view.visualisation_checkbox.setChecked(False)
        # set momentum scam params to only be visible if momentum scan is selected
        self.on_scan_type_changed(self.view.scan_momentum_combo.currentText())
        self.view.scan_momentum_combo.currentTextChanged.connect(self.on_scan_type_changed)

        # set momentum bite param to only be visible is momentum spread simulation is selected
        self.on_sim_type_changed(self.view.sim_type_combo.currentText())
        self.view.sim_type_combo.currentTextChanged.connect(self.on_sim_type_changed)

        # Connect layer option checkboxes, set default layer method to simple stack and hide custom place_sample sample table
        self.view.mode_group.buttonToggled.connect(self.on_mode_changed)
        self.view.stack_layer_radio.setChecked(True)

        # add an empty row to the end of the layer table after every time the contents are updated
        self.view.stack_layer_setup_table.contents_updated_s.connect(self.view.stack_layer_setup_table.append_row)
        self.view.stack_layer_setup_table.cellClicked.connect(self.append_row_in_stack_layer_table_if_last_row_clicked)

        self.view.stack_layer_setup_table.update_contents(self.format_model_layers(), round_to=4)

        self.view.place_sample_implantation_collapse_checkbox.checkStateChanged.connect(self.view.collapse_expand_implantation)
        self.view.stack_implantation_collapse_checkbox.checkStateChanged.connect(lambda state: self.collapse_expand_tree(self.view.stack_results_tree, state))
        self.view.place_sample_implantation_collapse_checkbox.checkStateChanged.connect(lambda state: self.collapse_expand_tree(self.view.place_sample_results_tree, state))
        self.view.run_sim_button.clicked.connect(self.start_sim)
        self.view.cancel_sim_button.clicked.connect(self.cancel_sim)
        self.view.stopping_shift_plot_origin_s.connect(self.stopping_shift_plot_origin)
        self.view.stopping_reset_plot_origin_s.connect(self.stopping_reset_plot_origin)

        self.view.depth_shift_plot_origin_s.connect(self.depth_shift_plot_origin)
        self.view.depth_reset_plot_origin_s.connect(self.depth_reset_plot_origin)

        self.view.save_s.connect(self.on_save_sim_result)
        self.view.save_all_sims_button.clicked.connect(self.on_save_all_sim_results)
        self.view.show_plot_s.connect(self.show_plot)
        self.view.momentum_slider.valueChanged.connect(self.on_slider_moved)

        self.view.load_settings_btn.clicked.connect(self.load_settings)
        self.view.save_settings_btn.clicked.connect(self.save_settings)

        # set up simulation worker to run simulation on separate thread
        self.simulation_worker = None

        self.time_last_swapped = time.time_ns()

        self.view.window_closed_s.connect(self.close_figures)

    def close_figures(self):
        for plot_stack in self.view.plot_stacks:
            self.model.close_figure(plot_stack.widget(0).canvas.figure)
            self.model.close_figure(plot_stack.widget(1).canvas.figure)


    def on_scan_type_changed(self, scan_type: str):
        """
        Shows the min, max and momentum step part of the form if scan type is "Yes", hides if scan type is "No".
        Is called every time scan type is updated

        Args:
            scan_type: whether form should be visible or not

        """
        visibility = scan_type == "Yes"

        self.view.min_momentum_linedit.setVisible(visibility)
        self.view.min_momentum_label.setVisible(visibility)
        self.view.max_momentum_linedit.setVisible(visibility)
        self.view.max_momentum_label.setVisible(visibility)
        self.view.momentum_step_linedit.setVisible(visibility)
        self.view.momentum_step_label.setVisible(visibility)

    def on_sim_type_changed(self, sim_type: str):
        """
        Is called every time simulation type is selected to toggle the visibility of the momentum bite part of the form

        Args:
            sim_type: "Mono" or "Momentum Spread"
        """

        visibility = sim_type == "Momentum Spread"

        self.view.momentum_spread_label.setVisible(visibility)
        self.view.momentum_spread_linedit.setVisible(visibility)

    def append_row_in_stack_layer_table_if_last_row_clicked(self, row):
        if row == (self.view.stack_layer_setup_table.rowCount()-1):
            self.view.stack_layer_setup_table.append_row()

    def enable_stack_layer_table(self):
        if self.view.stack_checkbox.isChecked():
            self.view.manual_place_sample_checkbox.setChecked(False)
            self.view.stack_layer_setup_table.show()
            self.view.place_sample_setup_table.hide()
        else:
            self.view.stack_checkbox.setChecked(False)
            self.view.stack_layer_setup_table.hide()
            self.view.place_sample_setup_table.show()

    def on_mode_changed(self, button, checked):
        if not checked:   # ignore the button that was turned off
            return

        if button is self.view.stack_layer_radio:
            self.view.place_sample_tabWidget.hide()
            self.view.stack_tabWidget.show()
            self.model.sim_method = "Stack"

        elif button is self.view.manual_place_sample_radio:
            self.view.stack_tabWidget.hide()
            self.view.place_sample_tabWidget.show()
            self.model.sim_method = "Manual Placement"

    def append_row_in_stack_layer_table_if_last_row_clicked(self, row):
        if row == (self.view.stack_layer_setup_table.rowCount()-1):
            self.view.stack_layer_setup_table.append_row()

    def format_model_layers(self, layers: list | None = None) -> list[list[str | float]]:
        """
        Formats the layers in TrimFitModel to a format compatible with the BaseTable's update_contents() method.

        Returns:
            Formatted array containing the layer data in TrimFitModel.
        """
        if layers is None:
            layers = self.model.input_layers

        return [[layer["name"], layer["thickness"], layer.get("density", " ")] for layer in layers]

    def start_sim(self):
        if self.model.sim_method == "Stack":
            self.start_stack_layer_sim()
        elif self.model.sim_method == "Manual Placement":
            self.start_place_sample_sim()
        else:
            logger.error(f"Invalid simulation method {self.model.sim_method}")

    def start_stack_layer_sim(self):
        pass

    def start_place_sample_sim(self):
        pass
    def cancel_sim(self):
        pass
    def stopping_shift_plot_origin(self):
        pass
    def stopping_reset_plot_origin(self):
        pass
    def depth_shift_plot_origin(self):
        pass
    def depth_reset_plot_origin(self):
        pass
    def on_save_sim_result(self):
        pass
    def on_save_all_sim_results(self):
        pass
    def show_plot(self):
        pass
    def on_slider_moved(self):
        pass    
    def load_settings(self):
        pass
    def save_settings(self):
        pass