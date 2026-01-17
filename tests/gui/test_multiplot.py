import numpy as np
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QMessageBox
from pytestqt.plugin import qtbot


from EVA.gui.windows.multiplot.multi_plot_window import MultiPlotWindow
from EVA.core.app import get_config, get_app

channels = {
    "GE1": "2099",
    "GE2": "3099",
    "GE3": "4099",
    "GE4": "5099"
}


TIME_DELAY = 1000

class TestMultiPlotWindow:
    # this will run once before all other tests in the class
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        config = get_config()

        self.window = MultiPlotWindow()
        self.view = self.window._view

        # set up test conditions
        config["default_corrections"]["normalisation"] = "none"
        self.view.det1_checkbox.setChecked(True)
        self.view.det3_checkbox.setChecked(True)

        qtbot.addWidget(self.view)
        self.window.show()

    # utility function to load data manually to compare with loaded data
    def get_data(self, run_list, detectors):
        data = []
        for i, run in enumerate(run_list):
            dets = []
            for detector in detectors:
                try:
                    file = f"./test_data/ral0{run}.rooth{channels[detector]}.dat"
                    dets.append(np.loadtxt(file, delimiter=" "))
                except FileNotFoundError:
                    print("f")
                    pass
            data.append(dets)
        return data

    def test_multiplot_single_run(self, qtbot):
        # test plotting a single run
        self.view.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))
        qtbot.wait(TIME_DELAY)

        qtbot.mouseClick(self.view.load_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))
        self.view.det2_checkbox.setChecked(False)
        self.view.det4_checkbox.setChecked(False)
        qtbot.mouseClick(self.view.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))
        # load data manually and assert that plotted data matches the expected
        run_list = ["3063"]
        target_data = self.get_data(run_list, ["GE1", "GE3"])

        get_app().reset()
        for i in range(len(run_list)):
            assert all(self.view.plot.canvas.axs[0].lines[i].get_ydata() == target_data[i][0][:, 1]), \
                "incorrect data was loaded"
            assert all(self.view.plot.canvas.axs[1].lines[i].get_ydata() == target_data[i][1][:, 1]), \
                "incorrect data was loaded"

    def test_multiplot_multiple_runs(self, qtbot):
        # test plotting two non-consecutive runs
        self.view.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))
        self.view.RunListTable.setItem(1, 0, QTableWidgetItem("3050"))
        qtbot.wait(TIME_DELAY)

        qtbot.mouseClick(self.view.load_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))
        self.view.det2_checkbox.setChecked(False)
        self.view.det4_checkbox.setChecked(False)
        qtbot.mouseClick(self.view.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        assert len(self.view.plot.canvas.axs[0].lines) == 2, "incorrect number of runs were plotted"
        assert len(self.view.plot.canvas.axs[1].lines) == 2, "incorrect number of runs were plotted"

        # load data manually and assert that plotted data matches the expected
        run_list = ["3063", "3050"]

        target_data = self.get_data(run_list, ["GE1", "GE3"])

        get_app().reset()
        for i in range(len(run_list)):
            assert all(self.view.plot.canvas.axs[0].lines[i].get_ydata() == target_data[i][0][:, 1]), \
                "incorrect data was loaded"
            assert all(self.view.plot.canvas.axs[1].lines[i].get_ydata() == target_data[i][1][:, 1]), \
                "incorrect data was loaded"


    def test_multiplot_with_simple_step(self, qtbot):
        self.view.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))  # start
        self.view.RunListTable.setItem(0, 1, QTableWidgetItem("3068"))  # stop
        self.view.RunListTable.setItem(0, 2, QTableWidgetItem("1"))  # step

        self.view.RunListTable.setItem(1, 0, QTableWidgetItem("3070"))  # start
        self.view.RunListTable.setItem(1, 1, QTableWidgetItem("3074"))  # stop
        self.view.RunListTable.setItem(1, 2, QTableWidgetItem("1"))  # step
        qtbot.wait(TIME_DELAY)

        # click button to load multi run
        qtbot.mouseClick(self.view.load_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))
        self.view.det2_checkbox.setChecked(False)
        self.view.det4_checkbox.setChecked(False)
        qtbot.mouseClick(self.view.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        ax0_lines = self.view.plot.canvas.axs[0].lines
        ax1_lines = self.view.plot.canvas.axs[1].lines

        # check that both subplots contain 11 lines: 3063-3074 excluding 3069 because it is missing from testdata
        assert len(self.view.plot.canvas.axs[0].lines) == 11, \
            "incorrect number of runs were plotted"
        assert len(self.view.plot.canvas.axs[1].lines) == 11, \
            "incorrect number of runs were plotted"

        # load data manually and assert that plotted data matches the expected
        run_list = ["3063", "3064", "3065", "3066", "3067", "3068", "3070", "3071", "3072", "3073", "3074"]

        target_data = self.get_data(run_list, ["GE1", "GE3"])

        for i in range(len(run_list)):
            assert all(ax0_lines[i].get_ydata() == target_data[i][0][:, 1]), \
                "incorrect data was loaded"
            assert all(ax1_lines[i].get_ydata() == target_data[i][1][:, 1]), \
                "incorrect data was loaded"

    def test_multiplot_with_step_overflow(self, qtbot):
        self.view.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))  # start
        self.view.RunListTable.setItem(0, 1, QTableWidgetItem("3068"))  # stop
        self.view.RunListTable.setItem(0, 2, QTableWidgetItem("2"))  # step
        qtbot.wait(TIME_DELAY)

        # click button to load multi run
        qtbot.mouseClick(self.view.load_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))
        self.view.det2_checkbox.setChecked(False)
        self.view.det4_checkbox.setChecked(False)
        qtbot.mouseClick(self.view.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        # check that both axes contain 3 lines (3063, 3065, 3067)
        assert len(self.view.plot.canvas.axs[0].lines) == 3, \
            "incorrect number of runs were plotted"
        assert len(self.view.plot.canvas.axs[1].lines) == 3, \
            "incorrect number of runs were plotted"

        # load data manually and assert that plotted data matches the expected
        run_list = ["3063", "3065", "3067"]

        target_data = self.get_data(run_list, ["GE1", "GE3"])

        for i in range(len(run_list)):
            assert all(self.view.plot.canvas.axs[0].lines[i].get_ydata() == target_data[i][0][:, 1]), \
                "incorrect data was loaded"
            assert all(self.view.plot.canvas.axs[1].lines[i].get_ydata() == target_data[i][1][:, 1]), \
                "incorrect data was loaded"


    def test_multiplot_no_runs_entered(self, qtbot, mocker):
        # mock answer from user to avoid dialog box (magic)
        mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.StandardButton.Ok)

        # click load without any data
        qtbot.mouseClick(self.view.load_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))
        self.view.det2_checkbox.setChecked(False)
        self.view.det4_checkbox.setChecked(False)
        qtbot.mouseClick(self.view.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        assert self.view.plot.canvas.axs is None, "incorrect number of runs were loaded"

    def test_multiplot_invalid_run_entered(self, qtbot, mocker):
        # mock answer from user to avoid dialog box (magic)
        mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.StandardButton.Ok)

        # try to load invalid run number 'A'
        self.view.RunListTable.setItem(0, 0, QTableWidgetItem("A"))
        qtbot.wait(TIME_DELAY)
        qtbot.mouseClick(self.view.load_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))
        self.view.det2_checkbox.setChecked(False)
        self.view.det4_checkbox.setChecked(False)
        qtbot.mouseClick(self.view.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        assert self.view.plot.canvas.axs is None, "incorrect number of runs were loaded"