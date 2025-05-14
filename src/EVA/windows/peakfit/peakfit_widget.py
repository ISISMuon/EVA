from PyQt6.QtWidgets import QWidget, QHBoxLayout

from EVA.windows.peakfit.model_fit_model import ModelFitModel
from EVA.windows.peakfit.peakfit_model import PeakFitModel
from EVA.windows.peakfit.peakfit_presenter import PeakFitPresenter
from EVA.windows.peakfit.peakfit_view import PeakFitView


class PeakFitWidget(QWidget):
    def __init__(self, run, detector):
        """ Assemble the view and the presenter for the PeakFit widget."""
        super().__init__()
        self.view = PeakFitView(parent=self)
        self.model = PeakFitModel(run, detector, parent=self)
        self.mf_model = ModelFitModel(run, detector, parent=self)
        self.presenter = PeakFitPresenter(view=self.view, model=self.model, mf_model=self.mf_model, parent=self)
        self.setWindowTitle("Peak Fitting")

        # Using a layout for this is excessive, but for some reason just parenting the view doesn't
        # force the PlotWidget to resize to fit the window, while using a layout does...?

        layout = QHBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        layout.setContentsMargins(0,0,0,0)
