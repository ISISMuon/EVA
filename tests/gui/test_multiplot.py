import numpy as np
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QTableWidgetItem
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

        # set up test conditions
        config["default_corrections"]["normalisation"] = "none"
        config["plot"]["show_plot"]["GE1"] = True
        config["plot"]["show_plot"]["GE2"] = False
        config["plot"]["show_plot"]["GE3"] = True
        config["plot"]["show_plot"]["GE4"] = False


        self.window = MultiPlotWindow()
        qtbot.addWidget(self.window)

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
                    pass
            data.append(dets)
        return data

    def test_multiplot_single_run(self, qtbot):
        # test plotting a single run
        self.window.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))
        qtbot.wait(TIME_DELAY)

        qtbot.mouseClick(self.window.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        # load data manually and assert that plotted data matches the expected
        run_list = ["3063"]
        target_data = self.get_data(run_list, ["GE1", "GE3"])

        get_app().reset()
        for i in range(len(run_list)):
            assert all(self.window.plot.canvas.axs[0].lines[i].get_ydata() == target_data[i][0][:, 1]), \
                "incorrect data was loaded"
            assert all(self.window.plot.canvas.axs[1].lines[i].get_ydata() == target_data[i][1][:, 1]), \
                "incorrect data was loaded"

    def test_multiplot_multiple_runs(self, qtbot):
        # test plotting two non-consecutive runs
        self.window.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))
        self.window.RunListTable.setItem(1, 0, QTableWidgetItem("3050"))
        qtbot.wait(TIME_DELAY)

        qtbot.mouseClick(self.window.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        assert len(self.window.plot.canvas.axs[0].lines) == 2, "incorrect number of runs were plotted"
        assert len(self.window.plot.canvas.axs[1].lines) == 2, "incorrect number of runs were plotted"

        # load data manually and assert that plotted data matches the expected
        run_list = ["3063", "3050"]

        target_data = self.get_data(run_list, ["GE1", "GE3"])

        get_app().reset()
        for i in range(len(run_list)):
            assert all(self.window.plot.canvas.axs[0].lines[i].get_ydata() == target_data[i][0][:, 1]), \
                "incorrect data was loaded"
            assert all(self.window.plot.canvas.axs[1].lines[i].get_ydata() == target_data[i][1][:, 1]), \
                "incorrect data was loaded"


    def test_multiplot_with_simple_step(self, qtbot):
        self.window.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))  # start
        self.window.RunListTable.setItem(0, 1, QTableWidgetItem("3068"))  # stop
        self.window.RunListTable.setItem(0, 2, QTableWidgetItem("1"))  # step

        self.window.RunListTable.setItem(1, 0, QTableWidgetItem("3070"))  # start
        self.window.RunListTable.setItem(1, 1, QTableWidgetItem("3074"))  # stop
        self.window.RunListTable.setItem(1, 2, QTableWidgetItem("1"))  # step
        qtbot.wait(TIME_DELAY)

        # click button to load multi run
        qtbot.mouseClick(self.window.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        ax0_lines = self.window.plot.canvas.axs[0].lines
        ax1_lines = self.window.plot.canvas.axs[1].lines

        # check that both subplots contain 11 lines: 3063-3074 excluding 3069 because it is missing from testdata
        assert len(self.window.plot.canvas.axs[0].lines) == 11, \
            "incorrect number of runs were plotted"
        assert len(self.window.plot.canvas.axs[1].lines) == 11, \
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
        self.window.RunListTable.setItem(0, 0, QTableWidgetItem("3063"))  # start
        self.window.RunListTable.setItem(0, 1, QTableWidgetItem("3068"))  # stop
        self.window.RunListTable.setItem(0, 2, QTableWidgetItem("2"))  # step
        qtbot.wait(TIME_DELAY)

        # click button to load multi run
        qtbot.mouseClick(self.window.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        # check that both axes contain 3 lines (3063, 3065, 3067)
        assert len(self.window.plot.canvas.axs[0].lines) == 3, \
            "incorrect number of runs were plotted"
        assert len(self.window.plot.canvas.axs[1].lines) == 3, \
            "incorrect number of runs were plotted"

        # load data manually and assert that plotted data matches the expected
        run_list = ["3063", "3065", "3067"]

        target_data = self.get_data(run_list, ["GE1", "GE3"])

        for i in range(len(run_list)):
            assert all(self.window.plot.canvas.axs[0].lines[i].get_ydata() == target_data[i][0][:, 1]), \
                "incorrect data was loaded"
            assert all(self.window.plot.canvas.axs[1].lines[i].get_ydata() == target_data[i][1][:, 1]), \
                "incorrect data was loaded"


    def test_multiplot_no_runs_entered(self, qtbot):
        # click load without any data
        qtbot.mouseClick(self.window.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        assert self.window.plot.canvas.axs is None, "incorrect number of runs were loaded"

    def test_multiplot_invalid_run_entered(self, qtbot):
        # try to load invalid run number 'A'
        self.window.RunListTable.setItem(0, 0, QTableWidgetItem("A"))
        qtbot.wait(TIME_DELAY)
        qtbot.mouseClick(self.window.plot_multi, Qt.MouseButton.LeftButton)
        qtbot.wait(int(TIME_DELAY*1.5))

        assert self.window.plot.canvas.axs is None, "incorrect number of runs were loaded"
