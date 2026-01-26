from PyQt6.QtWidgets import QWidget
from EVA.core.data_structures.run import Run
from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.multiplot.multi_plot_model import MultiPlotModel
from EVA.gui.windows.multiplot.multi_plot_presenter import MultiPlotPresenter
from EVA.gui.windows.multiplot.multi_plot_view import MultiPlotView


class MultiPlotWindow(BaseWindow):
    """Coordinator class to string together the MVP components of the multi plot window"""

    def __init__(self):
        """
        Args:
            run: run object to plot for
            detector: detector to plot for
            parent: Reference to parent widget
        """

        view = MultiPlotView()
        model = MultiPlotModel()
        presenter = MultiPlotPresenter(view, model)

        super().__init__(view, model, presenter)
