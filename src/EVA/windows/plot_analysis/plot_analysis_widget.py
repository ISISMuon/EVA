from PyQt6.QtWidgets import QWidget, QHBoxLayout

from EVA.windows.plot_analysis.plot_analysis_model import PlotAnalysisModel
from EVA.windows.plot_analysis.plot_analysis_presenter import PlotAnalysisPresenter
from EVA.windows.plot_analysis.plot_analysis_view import PlotAnalysisView


class PlotAnalysisWidget(QWidget):
    def __init__(self, run, parent=None):
        super().__init__()


        self.view = PlotAnalysisView()
        self.model = PlotAnalysisModel(run)
        self.presenter = PlotAnalysisPresenter(self.view, self.model)

        layout = QHBoxLayout()
        layout.addWidget(self.view)

        self.setLayout(layout)

