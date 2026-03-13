from matplotlib import pyplot as plt
from PyQt6.QtCore import pyqtSignal, Qt

from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QLineEdit,
    QGridLayout,
    QTableWidgetItem,
    QFileDialog,
    QVBoxLayout,
    QTreeWidgetItem,
    QCheckBox,
    QStackedWidget,
    QHBoxLayout,
    QFrame,
    QMenuBar,
    QSizePolicy,
)

from EVA.gui.ui_files.trim_gui import Ui_trim
from EVA.gui.base.base_view import BaseView
from EVA.gui.widgets.plot.plot_widget import PlotWidget
from EVA.gui.windows.srim.trim_presenter import TrimPresenter


class TrimView(BaseView, Ui_trim):
    remove_layer_requested_s = pyqtSignal(int)
    save_plot_requested_s = pyqtSignal(int, str)

    show_plot_s = pyqtSignal(int, str)
    save_s = pyqtSignal(int)
    depth_shift_plot_origin_s = pyqtSignal()
    depth_reset_plot_origin_s = pyqtSignal()
    stopping_shift_plot_origin_s = pyqtSignal(int)
    stopping_reset_plot_origin_s = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setupUi(self)

        self.setWindowTitle("TRIM Simulations - EVA")
        self.setMinimumSize(1100, 600)
        self.plot_stacks = []
        self.stopping_origin_shift_line_edits = []

        self.layer_setup_table.stretch_horizontal_header()

        self.results_table.setColumnWidth(0, 150)
        self.results_table.stretch_horizontal_header(skip=[0])

        self.results_tree.resizeColumnToContents(0)
        self.results_tree.resizeColumnToContents(1)
        self.results_tree.resizeColumnToContents(2)
        self.results_tree.resizeColumnToContents(3)

        self.menubar = QMenuBar()
        self.menubar.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum
        )

        file = self.menubar.addMenu("File")
        self.menubar.setContentsMargins(0, 0, 0, 0)

        self.file_load = file.addAction("Load SRIM Settings")
        self.file_save = file.addAction("Save SRIM Settings")
        self.file_reset = file.addAction("Restore default SRIM Settings")

        self.simulation_progress_widget.hide()
        self.cancel_sim_button.hide()
        self.slider_container.hide()
        self.depth_profile_plot.hide()

    # display results to table and set up connections
    def setup_results_table(self, momenta):
        table = self.results_table
        n_rows = len(momenta)

        self.results_table.setRowCount(n_rows)

        for row, momentum in enumerate(momenta):
            momentumstr = str(round(momentum, 4))

            table.setItem(row, 0, QTableWidgetItem(momentumstr))

            options_container = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            options_container.setLayout(layout)

            plot_whole_btn = QPushButton()
            plot_whole_btn.setText("Show plot")

            save_btn = QPushButton()
            save_btn.setText("Save plot data")

            layout.addWidget(plot_whole_btn)
            layout.addWidget(save_btn)

            table.setCellWidget(row, 1, options_container)

            plot_whole_btn.clicked.connect(
                lambda _, r=row, m=momentumstr: self.show_plot_s.emit(r, m)
            )

            save_btn.clicked.connect(lambda _, r=row: self.save_s.emit(r))

    def update_results_tree(
        self, momenta, layer_names, proportions, proportions_errs, counts, counts_errs
    ):
        self.results_tree.clear()

        # build all tree items and add to tree widget
        items = []
        for i, mom in enumerate(momenta):
            momentum_item = QTreeWidgetItem([str(round(mom, 4))])

            for j, layer_name in enumerate(layer_names):
                layer_item = QTreeWidgetItem()
                layer_item.setText(1, layer_name)
                layer_item.setText(2, f"{proportions[j, i]} ± {proportions_errs[j, i]}")
                # layer_item.setText(3, str(round(comp[1], 4)))
                layer_item.setText(3, f"{counts[j, i]} ± {counts_errs[j, i]}")
                # layer_item.setText(5, str(comp[3]))
                momentum_item.addChild(layer_item)

            items.append(momentum_item)
        self.results_tree.addTopLevelItems(items)

        # expand all items
        for item in items:
            item.setExpanded(True)

        # lastly, resize all columns
        self.results_tree.resizeColumnToContents(0)
        self.results_tree.resizeColumnToContents(1)
        self.results_tree.resizeColumnToContents(2)
        self.results_tree.resizeColumnToContents(3)

    def collapse_expand_implantation(self, checkstate):
        if checkstate == Qt.CheckState.Checked:
            self.results_tree.expandAll()

        else:
            self.results_tree.collapseAll()

    def get_form_data(self):
        form_data = {
            "sample_name": self.sample_name_linedit.text(),
            "stats": float(self.stats_linedit.text()),
            "srim_dir": self.srim_exe_dir_linedit.text(),
            "output_dir": self.trim_out_dir_linedit.text(),
            "momentum": float(self.momentum_linedit.text()),
            "sim_type": self.sim_type_combo.currentText(),
            "momentum_spread": float(self.momentum_spread_linedit.text()),
            "min_momentum": float(self.min_momentum_linedit.text()),
            "max_momentum": float(self.max_momentum_linedit.text()),
            "step_momentum": float(self.momentum_step_linedit.text()),
            "scan_type": self.scan_momentum_combo.currentText(),
        }

        return form_data

    def enable_depth_profile_tab(self, fig, ax):
        # hide text saying more momentum is needed for depth profile
        self.not_enough_momentum_label.hide()

        container = self.depth_settings_widget
        settings_container = QFrame()
        settings_layout = QGridLayout()

        settings_container.setLayout(settings_layout)

        shift_origin_label = QLabel("Shift plot origin to: (mm)")
        self.depth_shift_origin_linedit = QLineEdit("0")

        depth_shift_button = QPushButton("Shift")
        depth_reset_button = QPushButton("Reset origin")
        settings_layout.addWidget(shift_origin_label, 1, 0)
        settings_layout.addWidget(self.depth_shift_origin_linedit, 1, 1)
        settings_layout.addWidget(depth_shift_button, 1, 2)
        settings_layout.addWidget(depth_reset_button, 1, 3)
        layout = QVBoxLayout()
        layout.addWidget(settings_container)

        container.setLayout(layout)
        depth_shift_button.clicked.connect(self.depth_shift_plot_origin_s.emit)
        depth_reset_button.clicked.connect(self.depth_reset_plot_origin_s.emit)
        self.depth_profile_plot.show()
        self.depth_profile_plot.update_plot(fig, ax)

    def reset(self):
        # set up results table
        self.stopping_origin_shift_line_edits = []
        self.plot_stacks = []

        self.slider_container.hide()
        self.stopping_profiles_tab_widget.clear()
        self.not_enough_momentum_label.show()
        self.depth_profile_plot.hide()

    def generate_plot_tab(
        self, momentum, index, fig_whole, ax_whole, fig_comp, ax_comp
    ):
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

        stopping_shift_origin_label = QLabel("Shift plot origin to: (mm)")
        stopping_shift_origin_linedit = QLineEdit("0")

        stopping_shift_button = QPushButton("Shift")
        stopping_reset_button = QPushButton("Reset origin")

        settings_layout.addWidget(show_comp, 0, 0, 1, -1)
        settings_layout.addWidget(stopping_shift_origin_label, 1, 0)
        settings_layout.addWidget(stopping_shift_origin_linedit, 1, 1)
        settings_layout.addWidget(stopping_shift_button, 1, 2)
        settings_layout.addWidget(stopping_reset_button, 1, 3)

        layout = QVBoxLayout()
        layout.addWidget(plot_stack)
        layout.addWidget(settings_container)

        container.setLayout(layout)

        # connect all buttons
        show_comp.checkStateChanged.connect(
            lambda check_state, i=index: self.swap_plot_stack(check_state, i)
        )
        stopping_shift_button.clicked.connect(
            lambda x, i=index: self.stopping_shift_plot_origin_s.emit(i)
        )
        stopping_reset_button.clicked.connect(
            lambda x, i=index: self.stopping_reset_plot_origin_s.emit(i)
        )

        self.plot_stacks.append(plot_stack)
        self.stopping_origin_shift_line_edits.append(stopping_shift_origin_linedit)
        self.stopping_profiles_tab_widget.addTab(container, str(round(momentum, 4)))

    def swap_plot_stack(self, check_state, index):
        stack = self.plot_stacks[index]

        if check_state == Qt.CheckState.Checked:
            stack.setCurrentIndex(1)
        else:
            stack.setCurrentIndex(0)

    def set_form_data(self, form_data):
        (self.sample_name_linedit.setText(form_data["sample_name"]),)
        (self.stats_linedit.setText(str(form_data["stats"])),)
        (self.srim_exe_dir_linedit.setText(form_data["srim_dir"]),)
        (self.trim_out_dir_linedit.setText(form_data["output_dir"]),)
        (self.momentum_linedit.setText(str(form_data["momentum"])),)
        (self.sim_type_combo.setCurrentText(form_data["sim_type"]),)
        (self.momentum_spread_linedit.setText(str(form_data["momentum_spread"])),)
        (self.min_momentum_linedit.setText(str(form_data["min_momentum"])),)
        (self.max_momentum_linedit.setText(str(form_data["max_momentum"])),)
        (self.momentum_step_linedit.setText(str(form_data["step_momentum"])),)
        self.scan_momentum_combo.setCurrentText(form_data["scan_type"])

    def get_save_file_path(self, default_dir: str, file_filter: str) -> str:
        file = QFileDialog.getSaveFileName(
            self, "Save File", directory=default_dir, filter=file_filter
        )
        if file:
            return file[0]

    def get_load_file_path(self, default_dir: str, file_filter: str) -> str:
        file = QFileDialog.getOpenFileName(
            self, "Load File", directory=default_dir, filter=file_filter
        )
        if file:
            return file[0]

    def get_directory(self, default_dir):
        file_dir = QFileDialog.getExistingDirectory(
            self, "Select folder", directory=default_dir
        )
        if file_dir:
            return file_dir

    def file_save(
        self,
        SampleName,
        SimType,
        Momentum,
        MomentumSpread,
        ScanType,
        MinMomentum,
        MaxMomentum,
        StepMomentum,
        SRIMdir,
        TRIMOutDir,
        Stats,
    ):
        save_file = QFileDialog.getSaveFileName(self, caption="Save TRIM/SRIM Settings")
        print(save_file[0])
        file2 = open(save_file[0], "w")
        file2.writelines("Sample Name\n")
        out = SampleName.text() + "\n"
        file2.writelines(out)
        file2.writelines("SimType\n")
        out = SimType.currentText() + "\n"
        file2.writelines(out)
        file2.writelines("Momentum\n")
        out = Momentum.text() + "\n"
        file2.writelines(out)
        file2.writelines("Momentum Spread\n")
        out = MomentumSpread.text() + "\n"
        file2.writelines(out)
        file2.writelines("Scan Momentum\n")
        out = ScanType.currentText() + "\n"
        file2.writelines(out)
        file2.writelines("Min Momentum\n")
        out = MinMomentum.text() + "\n"
        file2.writelines(out)
        file2.writelines("Max Momentum\n")
        out = MaxMomentum.text() + "\n"
        file2.writelines(out)
        file2.writelines("Momentum Step\n")
        out = StepMomentum.text() + "\n"
        file2.writelines(out)
        file2.writelines("SRIM.exe dir\n")
        out = SRIMdir.text() + "\n"
        file2.writelines(out)
        file2.writelines("Output dir\n")
        out = TRIMOutDir.text() + "\n"
        file2.writelines(out)
        file2.writelines("Stats\n")
        out = Stats.text() + "\n"
        file2.writelines(out)
        file2.writelines("Sample\n")

        for j in range(10):
            line = ""
            for i in range(5):
                print(j, i)
                try:
                    line += self.tab1.table_TRIMsetup.item(j, i).text() + ","
                except:
                    line += ","

            file2.writelines(line + "\n")
        file2.close()

    def file_load(
        self,
        SampleName,
        SimType,
        Momentum,
        MomentumSpread,
        ScanType,
        MinMomentum,
        MaxMomentum,
        StepMomentum,
        SRIMdir,
        TRIMOutDir,
        Stats,
    ):
        print("in load file")
        load_file = QFileDialog.getOpenFileName(self, caption="Load TRIM/SRIM Settings")
        print(load_file[0])
        file2 = open(load_file[0], "r")
        ignore = file2.readline()
        SampleName.setText(file2.readline().strip())
        ignore = file2.readline()
        SimType.setCurrentText(file2.readline().strip())
        ignore = file2.readline()
        Momentum.setText(file2.readline().strip())
        ignore = file2.readline()
        MomentumSpread.setText(file2.readline().strip())
        ignore = file2.readline()
        ScanType.setCurrentText(file2.readline().strip())
        ignore = file2.readline()
        MinMomentum.setText(file2.readline().strip())
        ignore = file2.readline()
        MaxMomentum.setText(file2.readline().strip())
        ignore = file2.readline()
        StepMomentum.setText(file2.readline().strip())
        ignore = file2.readline()
        SRIMdir.setText(file2.readline().strip())
        ignore = file2.readline()
        TRIMOutDir.setText(file2.readline().strip())
        ignore = file2.readline()
        Stats.setText(file2.readline().strip())
        ignore = file2.readline()

        line = []

        for j in range(10):
            line = file2.readline().split(",")
            print(line)
            for i in range(5):
                print(j, i)
                try:
                    self.tab1.table_TRIMsetup.setItem(j, i, QTableWidgetItem(line[i]))
                except:
                    print("load finished")

        file2.close()
