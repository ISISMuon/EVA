from PyQt6.QtCore import pyqtEnum, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QWidget


class BaseWindow(object):
    def __init__(self, view, model, presenter, **kwargs):
        self._view = view
        self._model = model
        self._presenter = presenter

        self._view.window = self

    def show(self):
        self._view.show()

    def showMaximized(self):
        self._view.showMaximized()

    def widget(self):
        return self._view

    def layout(self):
        return self._view.layout()
