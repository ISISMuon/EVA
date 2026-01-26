from PyQt6.QtWidgets import QWidget

from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.muonic_xray_simulation.model_spectra_model import ModelSpectraModel
from EVA.gui.windows.muonic_xray_simulation.model_spectra_presenter import (
    ModelSpectraPresenter,
)
from EVA.gui.windows.muonic_xray_simulation.model_spectra_view import ModelSpectraView


class ModelSpectraWindow(BaseWindow):
    """Coordinator class to string together the MVP components of the model spectra window"""

    def __init__(self, parent: QWidget | None = None):
        """
        Args:
            parent: Reference to parent widget
        """
        self.parent = parent

        view = ModelSpectraView()
        model = ModelSpectraModel()
        presenter = ModelSpectraPresenter(view, model)

        super().__init__(view, model, presenter)
