from PyQt6.QtWidgets import QWidget

from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.multiplot.multi_plot_model import MultiPlotModel
from EVA.gui.windows.multiplot.multi_plot_presenter import MultiPlotPresenter
from EVA.gui.windows.multiplot.multi_plot_view import MultiPlotView


class MultiPlotWindow(BaseWindow):
    """ Coordinator class to string together the MVP components of the multi plot window """
    def __init__(self, parent: QWidget | None = None):
        """
        Args:
            parent: Reference to parent widget
        """
        self.parent = parent

        view = MultiPlotView()
        model = MultiPlotModel()
        presenter = MultiPlotPresenter(view, model)

        super().__init__(view, model, presenter)