from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QWidget, QHeaderView, QMessageBox, QTableWidgetItem, QErrorMessage
from matplotlib import pyplot as plt


class BaseView(QWidget):
    """
    All EVA widgets should inherit from this view - it just provides some useful pre-defined methods to
    avoid code-duplication.

    """
    window_closed_s = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

    def display_error_message(self, title="Error", message="", buttons=QMessageBox.StandardButton.Ok):
        _ = QMessageBox.critical(self, title, message, buttons)

    def display_message(self, title="Message", message="", buttons=QMessageBox.StandardButton.Ok):
        _ = QMessageBox.information(self, title, message, buttons)

    def display_question(self,
                         title: str = "Question",
                         message: str = "",
                         buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes |
                                    QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                         default_button: QMessageBox.standardButton = QMessageBox.StandardButton.Yes) \
            -> QMessageBox.StandardButton:

        return QMessageBox.question(self, title, message, buttons, default_button)

    @staticmethod
    def update_table(table, data, resize_columns=True, resize_rows=True):
        input_n_rows = len(data)

        if input_n_rows != 0:
            input_n_cols = len(data[0])
        else:
            input_n_cols = table.columnCount()

        # resize table to fit new data if requested
        if resize_rows:
            table.setRowCount(input_n_rows)

        if resize_columns:
            table.setColumnCount(input_n_cols)

        # some lovely, probably very slow, table printing
        for row in range(input_n_rows):
            row_data = data[row]

            for col in range(input_n_cols):
                input_item = list(row_data)[col]

                if isinstance(input_item, float):
                    table_item = QTableWidgetItem(f"{input_item:.2f}")
                else:
                    table_item = QTableWidgetItem(str(input_item))

                table.setItem(row, col, QTableWidgetItem(table_item))

    def closeEvent(self, event: QCloseEvent):
        """ Handles closing windows"""
        self.window_closed_s.emit(event)

        event.accept()