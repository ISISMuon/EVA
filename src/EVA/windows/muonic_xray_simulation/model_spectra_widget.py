from PyQt6.QtWidgets import QWidget, QHBoxLayout

from EVA.windows.muonic_xray_simulation.model_spectra_model import ModelSpectraModel
from EVA.windows.muonic_xray_simulation.model_spectra_presenter import ModelSpectraPresenter
from EVA.windows.muonic_xray_simulation.model_spectra_view import ModelSpectraView


class ModelSpectraWidget(QWidget):
    def __init__(self, parent=None):

        super().__init__(parent)
        self.view = ModelSpectraView(self)
        self.model = ModelSpectraModel()
        self.presenter = ModelSpectraPresenter(self.view, self.model)
        self.setWindowTitle("Muonic X-ray Simulations")

        layout = QHBoxLayout()
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
