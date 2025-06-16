import pytest
from PyQt6.QtCore import Qt
from pytestqt.plugin import qtbot
from matplotlib.backend_bases import MouseButton

from EVA.gui.windows.elemental_analysis.plot_analysis_widget import PlotAnalysisWidget
from EVA.core.data_loading import load_data
from EVA.core.app import get_app, get_config

import tests.gui.test_util_gui as util

muon_plot_lines_tests = [[551.8, 48], [189.9, 30], [44.4, 22]]
gamma_plot_lines_tests = [[189.9, 124], [551.8, 626], [44.4, 198]]

class TestPlotWindow:
    # will be executed once before tests are run
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        # loading database and sample data
        app = get_app()
        app.use_mudirac_muon_db()

        get_config()["GE1"]["show_plot"] = "yes"
        get_config()["GE2"]["show_plot"] = "no"
        get_config()["GE3"]["show_plot"] = "yes"
        get_config()["GE4"]["show_plot"] = "no"

        run, _ = load_data.load_run("2630", get_config())

        self.window = PlotAnalysisWidget(run)
        qtbot.addWidget(self.window)

        self.window.showMaximized()

    # test if the expected data is displayed in gamma table when clicking a specific peak in the figure
    def test_clickpeaks_gammas(self, qtbot):
        tests = [("44Sc", 189.9), ("93Zr", 65.6)]
        for test in tests:
            event = util.trigger_figure_click_event(self.window.view.plot.canvas, xdata=test[1], ydata=0,
                                          ax=self.window.view.plot.canvas.axs[1], button=MouseButton.RIGHT)
            # call on_click
            self.window.presenter.on_plot_clicked(event)
            qtbot.wait(500)

            table_res = self.window.view.gamma_table.item(0, 0).text()
            assert table_res is not None, "gamma table empty on click"
            assert table_res == test[0], \
                "data displayed at position 0,0 in gamma table did not match the expected value"

    # test if the expected data is displayed in muon table when clicking a specific peak in the figure
    def test_clickpeaks_muon(self, qtbot):
        tests = [("Cl", 193.4), ("Ti", 932.0)]
        for test in tests:
            # simulate click event
            event = util.trigger_figure_click_event(self.window.view.plot.canvas, xdata=test[1], ydata=0,
                                          ax=self.window.view.plot.canvas.axs[1], button=MouseButton.LEFT)
            # call on_click
            self.window.presenter.on_plot_clicked(event)
            qtbot.wait(500)

            table_res = self.window.view.muonic_xray_table_all.item(0, 0).text()
            assert table_res == test[0], \
                "data displayed at position 0,0 in muon table on figure click did not match the expected value"

    @pytest.mark.parametrize("tests", gamma_plot_lines_tests)
    def test_plot_and_remove_lines_gammas(self, qtbot, tests):

        # first element in tuple is which energy to search, second element in tuple is how many lines will be plotted
        # when clicking the first element in the table after searching that energy.

        # simulate click event
        event = util.trigger_figure_click_event(self.window.view.plot.canvas, xdata=tests[0], ydata=0,
                                                ax=self.window.view.plot.canvas.axs[1], button=MouseButton.RIGHT)

        self.window.presenter.on_plot_clicked(event)
        qtbot.wait(250)

        # Click on source in gamma table to plot vertical lines on figure
        gamma_table_item = self.window.view.gamma_table.item(0, 0)
        gamma_table_rect = self.window.view.gamma_table.visualItemRect(gamma_table_item)

        qtbot.mouseClick(self.window.view.gamma_table.viewport(), Qt.MouseButton.LeftButton,
                     pos=gamma_table_rect.center())
        qtbot.wait(250)

        # check that lines were plotted
        assert len(list(self.window.view.plot.canvas.axs[1].lines)) > 1, "no lines were plotted"
        assert len(list(self.window.view.plot.canvas.axs[1].lines)) == tests[1], "not all lines were plotted"

        # Click on source in remove plot lines table to remove vertical line
        remove_table_item = self.window.view.plotted_gammas_table.item(0, 0)
        remove_table_rect = self.window.view.plotted_gammas_table.visualItemRect(remove_table_item)

        qtbot.mouseClick(self.window.view.plotted_gammas_table.viewport(), Qt.MouseButton.LeftButton,
                     pos=remove_table_rect.center())
        qtbot.wait(500)

        assert len(list(self.window.view.plot.canvas.axs[1].lines)) == 1, "Failed to remove all plot lines"

    @pytest.mark.parametrize("tests", muon_plot_lines_tests)
    def test_plot_and_remove_lines_muonic_xrays(self, qtbot, tests):
        # first element in tuple is which energy to search, second element in tuple is how many lines will be plotted
        # when clicking the first element in the table after searching that energy.
        table = self.window.view.muonic_xray_table_all

        # simulate left click on figure
        event = util.trigger_figure_click_event(self.window.view.plot.canvas, xdata=tests[0], ydata=0,
                                                ax=self.window.view.plot.canvas.axs[1], button=MouseButton.LEFT)

        self.window.presenter.on_plot_clicked(event)
        qtbot.wait(250)
        # Click on source in table to plot vertical lines on figure
        table_item = table.item(0, 0)
        table_rect = table.visualItemRect(table_item)
        qtbot.mouseClick(table.viewport(), Qt.MouseButton.LeftButton,
                         pos=table_rect.center())
        qtbot.wait(250)

        # check that lines were plotted
        print(f"number of lines plotted for energy {tests[0]} - {len(list(self.window.view.plot.canvas.axs[1].lines))}")
        assert len(list(self.window.view.plot.canvas.axs[1].lines)) > 1, "no lines were plotted"
        assert len(list(self.window.view.plot.canvas.axs[1].lines)) == tests[1], "not all lines were plotted"

        # Click on source in remove plot lines table to remove vertical line
        remove_table_item = self.window.view.plotted_mu_xrays_table.item(0, 0)
        remove_table_rect = self.window.view.plotted_mu_xrays_table.visualItemRect(remove_table_item)

        qtbot.mouseClick(self.window.view.plotted_mu_xrays_table.viewport(), Qt.MouseButton.LeftButton,
                         pos=remove_table_rect.center())
        qtbot.wait(250)

        assert len(list(self.window.view.plot.canvas.axs[1].lines)) == 1, "Failed to remove all plot lines"

    def test_find_peaks_plotting_on_button_click(self, qtbot):
        # TODO: Use a test database and test data so that we know exactly which points should be plotted
        # for now just check that *some points* were plotted - this will let us know if anything is broken at least

        # collections is an array of mpl "collections" which should only contain PolyCollection prior to peak find,
        # and should contain PolyCollection and PathCollection after peak find
        init_data_ax0 = list(self.window.view.plot.canvas.axs[0].collections)
        init_data_ax1 = list(self.window.view.plot.canvas.axs[1].collections)

        # click on peak fitting button - ONLY TESTS SCIPY FIND PEAKS METHOD
        qtbot.mouseClick(self.window.view.find_peaks_button, Qt.MouseButton.LeftButton)

        # data_ax0 = self.window.plot.canvas.axs[0].collections[1].get_offsets().data - HOW TO GET THE POINT POSITIONS
        data_ax0 = list(self.window.view.plot.canvas.axs[0].collections)
        data_ax1 = list(self.window.view.plot.canvas.axs[1].collections)

        print(data_ax0)
        """
        # check that the axes have 2 collections
        assert len(data_ax0) == 2
        assert len(data_ax1) == 2

        # check that the last collection is a PathCollection
        assert isinstance(data_ax0[-1], matplotlib.collections.PathCollection)
        assert isinstance(data_ax0[-1], matplotlib.collections.PathCollection)
        """

        """
        assert all([elem[0] == peaks_ax0[i][0] for i, elem in enumerate(data_ax0)]), \
            "Marker positions on figure after peakfit did not match expected results"
        assert all([elem[0] == peaks_ax1[i][0] for i, elem in enumerate(data_ax1)]), \
            "Marker positions on figure after peakfit did not match expected results"
        """