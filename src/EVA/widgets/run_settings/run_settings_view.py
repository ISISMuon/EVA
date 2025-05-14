from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QTreeView, QToolBox, QLabel, QSpinBox

from EVA.gui.run_settings_widget_gui import Ui_run_settings


class RunSettingsWidget(Ui_run_settings, QToolBox):
    settings_updated_s = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)









