from EVA.gui.base.base_window import BaseWindow
from EVA.gui.windows.detector_grouping.detector_grouping_model import DetectorGroupingModel
from EVA.gui.windows.detector_grouping.detector_grouping_presenter import DetectorGroupingPresenter
from EVA.gui.windows.detector_grouping.detector_grouping_view import DetectorGroupingView


class DetectorGroupingWindow(BaseWindow):
    """Coordinator class to string together the MVP components of the multi plot window"""

    def __init__(self):
        """
        Args:
            run: run object to plot for
            detector: detector to plot for
            parent: Reference to parent widget
        """

        view = DetectorGroupingView()
        model = DetectorGroupingModel()
        presenter = DetectorGroupingPresenter(view, model)

        super().__init__(view, model, presenter)
