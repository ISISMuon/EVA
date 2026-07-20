from PyQt6.QtWidgets import QWidget

from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.g4bl.g4bl_model import G4blModel
from EVA.gui.windows.g4bl.g4bl_presenter import G4blPresenter
from EVA.gui.windows.g4bl.g4bl_view import G4blView


class G4blWindow(BaseWindow):
    """ Coordinator class to string together the MVP components of the TRIM window """
    def __init__(self, parent: QWidget | None = None):
        """
        Args:
            parent: Reference to parent widget
        """

        view = G4blView()
        model = G4blModel()
        presenter = G4blPresenter(view, model)

        super().__init__(view, model, presenter)