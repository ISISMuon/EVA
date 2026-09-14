import logging
from PyQt6.QtWidgets import QFileDialog, QVBoxLayout, QTableWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal

from EVA.gui.base.base_view import BaseView
from EVA.gui.ui_files.detector_grouping_window_gui import (
    Ui_DetectorGrouping,
)  # this is the generated .py from .ui

logger = logging.getLogger(__name__)


class DetectorGroupingView(BaseView, Ui_DetectorGrouping):
    """
    GUI for the Detector Grouping window.
    Loads widgets from detector_grouping_window_gui.py and sets up dynamic elements.
    """
    profile_changed_s = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Detector Grouping Configuration - EVA")
        self.resize(400,310)
        self.ConfigTable.stretch_horizontal_header()
        
    def get_save_file_path(self, default_dir: str, file_filter: str, caption = "Save File", default_extension: str = None) -> str:
        file_path, _= QFileDialog.getSaveFileName(self, caption, directory=default_dir, filter=file_filter)
        if file_path and default_extension:
            if not file_path.lower().endswith(default_extension.lower()):
                file_path += default_extension
        if file_path:
            return file_path
        return ""

    def get_load_file_path(self, default_dir: str, file_filter: str, caption = "Load File", default_extension: str = None) -> str:
        file_path, _= QFileDialog.getOpenFileName(self, caption, directory=default_dir, filter=file_filter)
        if file_path and default_extension:
            if not file_path.lower().endswith(default_extension.lower()):
                file_path += default_extension
        if file_path:
            return file_path
        return ""
