from EVA.gui.trim_fit_gui import Ui_trim_fit
from EVA.widgets.base.base_view import BaseView


class TrimFitView(BaseView, Ui_trim_fit):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.layer_table.stretch_horizontal_header()
        self.setMinimumSize(800, 600)