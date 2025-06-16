from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.main.main_model import MainModel
from EVA.gui.windows.main.main_presenter import MainPresenter
from EVA.gui.windows.main.main_view import MainView

class MainWindow(BaseWindow):
    """ Coordinator class to string together the MVP components of the main window. """
    def __init__(self):
        """
        Initialises the MVP components of the main window and connects everything together.
        """
        view = MainView()
        model = MainModel()
        presenter = MainPresenter(view, model)

        super().__init__(view, model, presenter)