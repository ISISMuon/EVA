from pytestqt.plugin import qtbot
import os

from PyQt6.QtWidgets import QWidget
from EVA.gui.windows.manual import ManualWindow

class TestManual:
    def test_html_load(self, qtbot):
        widget = QWidget()
        window = ManualWindow(widget)
        qtbot.addWidget(window)

        assert os.path.isfile(window.path),  "invalid HTML manual file path"
        assert len(window.page.toHtml()) > 2000, \
            "HTML loaded incorrectly; less than 2000 characters were loaded"