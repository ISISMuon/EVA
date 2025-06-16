from PyQt6.QtWidgets import QWidget, QHBoxLayout

from EVA.gui.windows.trim_fitting.trim_fit_model import TrimFitModel
from EVA.gui.windows.trim_fitting.trim_fit_presenter import TrimFitPresenter
from EVA.gui.windows.trim_fitting.trim_fit_view import TrimFitView


class TrimFitWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.view = TrimFitView()
        self.model = TrimFitModel()

        self.presenter = TrimFitPresenter(self.view, self.model)

        layout = QHBoxLayout()
        layout.addWidget(self.view)

        self.setLayout(layout)
