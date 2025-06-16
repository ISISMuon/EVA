from PyQt6.QtWidgets import QWidget

from EVA.core.data_structures.run import Run
from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.elemental_analysis.elemental_analysis_model import ElementalAnalysisModel
from EVA.gui.windows.elemental_analysis.elemental_analysis_presenter import ElementalAnalysisPresenter
from EVA.gui.windows.elemental_analysis.elemental_analysis_view import ElementalAnalysisView


class ElementalAnalysisWindow(BaseWindow):
    """ Coordinator class to string together the MVP components of the elemental analysis window """
    def __init__(self, run: Run, parent: QWidget | None = None):
        """
        Args:
            run: run number to plot
            parent: reference to parent workspace
        """

        self.parent = parent

        # Initialise MVP components
        view = ElementalAnalysisView()
        model = ElementalAnalysisModel(run)
        presenter = ElementalAnalysisPresenter(view, model)

        # Connect components
        super().__init__(view, model, presenter)

        # connect settings changed signal to presenter
        if self.parent is not None:
            self.parent.replot_spectra_s.connect(presenter.replot_spectra)
            self.parent.update_detector_plot_selection_s.connect(presenter.on_detector_plot_selection_change)