from EVA.core.data_structures.run import Run
from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.peakfit.model_fit_model import ModelFitModel
from EVA.gui.windows.peakfit.peakfit_model import PeakFitModel
from EVA.gui.windows.peakfit.peakfit_presenter import PeakFitPresenter
from EVA.gui.windows.peakfit.peakfit_view import PeakFitView
from EVA.gui.windows.workspace.workspace_view import WorkspaceView


class PeakFitWindow(BaseWindow):
    """Coordinator class to string together the MVP components of the peak fit window"""

    def __init__(self, run: Run, detector: str, parent: WorkspaceView | None = None):
        """
        Args:
            run: run object to plot for
            detector: detector to plot for
            parent: Reference to parent widget
        """
        self.parent = parent

        view = PeakFitView()
        model = PeakFitModel(run, detector)
        mf_model = ModelFitModel(run, detector)
        presenter = PeakFitPresenter(view, model, mf_model)

        super().__init__(view, model, presenter)

        # connect signals
        model.run.corrections_updated_s.connect(presenter.on_replot_needed)

        if parent is not None:
            self.parent.replot_spectra_s.connect(presenter.on_replot_needed)
