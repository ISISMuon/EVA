import os
import sys
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QTextBrowser,
    QWidget,
)

from PyQt6.QtCore import Qt, pyqtSignal

from EVA.gui.base.base_view import BaseView
from EVA.util.path_handler import get_path

class ManualWindow(BaseView):
    def __init__(self, parent=None):
        super(ManualWindow, self).__init__(parent)
        self.setWindowTitle("Manual - EVA")
        self.setMinimumSize(850, 700)

        self.page = QTextBrowser(self)
        self.page.setOpenLinks(True)
        self.page.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.page)

        self.path = get_path("./src/EVA/resources/manual/manual.html")

        try:
            self.htmlstr = self.load_manual()
            self.page.setHtml(self.htmlstr)

        except FileNotFoundError:
            self.page.setText("Oops! Failed to load manual!")

    def load_manual(self):
        with open(self.path, "r", encoding="utf-8") as file:
            manual = "".join(file.readlines())

        # check if EVA is running in executable or from source
        if hasattr(sys, "_MEIPASS"):
            bundle_dir = getattr(sys, '_MEIPASS')
            manual = manual.replace("./", f"{bundle_dir}/")

        return manual
