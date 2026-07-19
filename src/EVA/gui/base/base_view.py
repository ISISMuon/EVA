from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QWidget,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QErrorMessage,
)
from matplotlib import pyplot as plt


class BaseView(QWidget):
    """
    All EVA widgets should inherit from this view - it just provides some useful pre-defined methods to
    avoid code-duplication.

    """

    window_closed_s = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

    def display_error_message(
        self, title="Error", message="", buttons=QMessageBox.StandardButton.Ok
    ):
        _ = QMessageBox.critical(self, title, message, buttons)

    def display_message(
        self, title="Message", message="", buttons=QMessageBox.StandardButton.Ok
    ):
        _ = QMessageBox.information(self, title, message, buttons)

    def display_question(
        self,
        title: str = "Question",
        message: str = "",
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
        | QMessageBox.StandardButton.Cancel,
        default_button: QMessageBox.standardButton = QMessageBox.StandardButton.Yes,
    ) -> QMessageBox.StandardButton:
        reply = QMessageBox.question(self, title, message, buttons, default_button)

        return reply

    @staticmethod
    def update_table(table, data, resize_columns=True, resize_rows=True):
        sorting_enabled = table.isSortingEnabled()
        sort_column = table.horizontalHeader().sortIndicatorSection()
        sort_order = table.horizontalHeader().sortIndicatorOrder()

        table.setSortingEnabled(False)

        try:
            table.clearContents()

            input_n_rows = len(data)
            input_n_cols = len(data[0]) if data else table.columnCount()

            if resize_rows:
                table.setRowCount(input_n_rows)

            if resize_columns:
                table.setColumnCount(input_n_cols)

            for row, row_data in enumerate(data):
                for col, input_item in enumerate(row_data):
                    if isinstance(input_item, float):
                        text = f"{input_item:.2f}"
                    else:
                        text = str(input_item)

                    table.setItem(row, col, QTableWidgetItem(text))

        finally:
            table.setSortingEnabled(sorting_enabled)

            if sorting_enabled:
                table.sortItems(sort_column, sort_order)

    def closeEvent(self, event: QCloseEvent):
        """Handles closing windows"""
        self.window_closed_s.emit(event)

        event.accept()
