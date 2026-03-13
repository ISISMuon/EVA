from EVA.core.data_structures.run import Run
from EVA.gui.base.base_window import BaseWindow
from PyQt6.QtCore import pyqtSignal

from EVA.gui.windows.fit_table_plot.fit_table_plot_model import FitTablePlotModel
from EVA.gui.windows.fit_table_plot.fit_table_plot_view import FitTablePlotView
from EVA.gui.windows.fit_table_plot.fit_table_plot_presenter import (
    FitTablePlotPresenter,
)


class FitTablePlotWindow(BaseWindow):
    """Coordinator class to string together the MVP components of the peak fit window"""

    window_closed_s = pyqtSignal(object)

    def __init__(self, parent=None):
        """
        Args:

        """

        view = FitTablePlotView()
        model = FitTablePlotModel()
        presenter = FitTablePlotPresenter(view, model)

        super().__init__(view, model, presenter)

    def closeEvent(self, event):
        self.window_closed_s.emit(self)
        super().closeEvent(event)
