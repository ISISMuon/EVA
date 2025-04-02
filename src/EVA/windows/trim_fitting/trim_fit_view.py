from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QStackedWidget, QHBoxLayout, QFrame, QGridLayout, QCheckBox, QLabel, QLineEdit, \
    QPushButton, QVBoxLayout, QAbstractItemView
from matplotlib import pyplot as plt

from EVA.gui.trim_fit_gui import Ui_trim_fit
from EVA.widgets.base.base_view import BaseView
from EVA.widgets.plot.plot_widget import PlotWidget


class TrimFitView(BaseView, Ui_trim_fit):
    def __init__(self):
        super().__init__()
        self.plot_stacks = []
        self.setupUi(self)

        self.layer_table.stretch_horizontal_header()
        self.setMinimumSize(800, 600)

        # set experiment data table to be read-only
        self.experiment_data_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # disable all key controls except copy
        self.experiment_data_table.paste_enabled = False
        self.experiment_data_table.cut_enabled = False
        self.experiment_data_table.del_enabled = False

    def get_form_data(self):
        form_data = {
            "sim_type": self.sim_type_combo.currentText(),
            "momentum_spread": float(self.momentum_spread_line_edit.text()),
            "num_ions": float(self.num_ions_line_edit.text())
        }

        return form_data
    
    def generate_plot_tab(self, momentum, index, fig_whole, ax_whole, fig_comp, ax_comp):
        container = QWidget()

        plot_stack = QStackedWidget()
        plot_stack_layout = QHBoxLayout()
        plot_stack.setLayout(plot_stack_layout)

        plot_whole = PlotWidget(fig_whole, ax_whole)
        plot_comp = PlotWidget(fig_comp, ax_comp)

        plot_stack.addWidget(plot_whole)
        plot_stack.addWidget(plot_comp)

        settings_container = QFrame()
        settings_layout = QGridLayout()

        settings_container.setLayout(settings_layout)

        show_comp = QCheckBox("Show components")

        settings_layout.addWidget(show_comp, 0, 0, 1, -1)

        layout = QVBoxLayout()
        layout.addWidget(plot_stack)
        layout.addWidget(settings_container)

        container.setLayout(layout)

         # connect all buttons
        show_comp.checkStateChanged.connect(lambda check_state, i=index: self.swap_plot_stack(check_state, i))

        self.plot_stacks.append(plot_stack)
        self.stopping_profiles_tab_widget.addTab(container, str(round(momentum, 4)))

    def swap_plot_stack(self, check_state, index):
        stack = self.plot_stacks[index]

        if check_state == Qt.CheckState.Checked:
            stack.setCurrentIndex(1)
        else:
            stack.setCurrentIndex(0)

    def reset_stopping_profiles_tab(self):
        # set up results table
        self.stopping_profiles_tab_widget.clear()

        for plot_stack in self.plot_stacks:
            plt.close(plot_stack.widget(0).canvas.figure)
            plt.close(plot_stack.widget(1).canvas.figure)

        self.plot_stacks = []