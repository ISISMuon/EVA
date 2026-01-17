from EVA.core.data_structures.run import Run
from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.workspace.workspace_model import WorkspaceModel
from EVA.gui.windows.workspace.workspace_presenter import WorkspacePresenter
from EVA.gui.windows.workspace.workspace_view import WorkspaceView

class WorkspaceWindow(BaseWindow):
    """ Coordinator class to string together the MVP components of the workspaces. """
    def __init__(self, run: Run):
        """
        Args:
            run: Run object
        """
        view = WorkspaceView(run)
        model = WorkspaceModel(run)
        presenter = WorkspacePresenter(view, model)

        super().__init__(view, model, presenter)