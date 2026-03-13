from PyQt6.QtWidgets import QWidget

from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.srim.trim_model import TrimModel
from EVA.gui.windows.srim.trim_presenter import TrimPresenter
from EVA.gui.windows.srim.trim_view import TrimView


class TrimWindow(BaseWindow):
    """Coordinator class to string together the MVP components of the TRIM window"""

    def __init__(self, parent: QWidget | None = None):
        """
        Args:
            parent: Reference to parent widget
        """

        view = TrimView()
        model = TrimModel()
        presenter = TrimPresenter(view, model)

        super().__init__(view, model, presenter)
