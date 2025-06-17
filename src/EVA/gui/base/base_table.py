from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal

from EVA.core.app import get_app

class BaseTable(QTableWidget):
    contents_updated_s = pyqtSignal()
    user_edited_cell_s = pyqtSignal(int, int)
    table_widget_clicked = pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.block_updates = False

        self.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, col):
        if not self.block_updates:
            self.user_edited_cell_s.emit(row, col)

    def stretch_horizontal_header(self, skip:list=None):
        n_cols = self.columnCount()
        for i in range(n_cols):
            if skip is None or i not in skip:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)


    def update_contents(self, data, resize_rows=True, resize_columns=False, round_to=2):
        self.block_updates = True # temporarily block updates
        input_n_rows = len(data)

        if input_n_rows != 0:
            input_n_cols = len(data[0])
        else:
            input_n_cols = self.columnCount()

        # resize table to fit new data if requested
        if resize_rows:
            self.setRowCount(input_n_rows)

        if resize_columns:
            self.setColumnCount(input_n_cols)

        # some lovely, probably very slow, table printing
        for row in range(input_n_rows):
            row_data = data[row]

            for col in range(input_n_cols):
                input_item = list(row_data)[col]

                if isinstance(input_item, float):
                    table_item = QTableWidgetItem(f"{round(input_item, round_to)}")
                else:
                    table_item = QTableWidgetItem(str(input_item))

                self.setItem(row, col, QTableWidgetItem(table_item))

        self.block_updates = False
        self.contents_updated_s.emit()

    def get_contents(self):
        n_rows = self.rowCount()
        n_cols = self.columnCount()

        data = []
        # some lovely, probably very slow, table printing
        for row in range(n_rows):
            row_data = []
            for col in range(n_cols):
                item = self.item(row, col)

                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")

            data.append(row_data)

        return data

    def get_row_contents(self):
        pass

    def get_column_contents(self):
        pass

    def append_row(self):
        """
        Adds a row to the bottom of the table.
        """
        n_rows = self.rowCount()
        self.setRowCount(n_rows + 1)

    def remove_last_row(self):
        """
        Removes the last row at the bottom of the table.
        """
        n_rows = self.rowCount()
        self.setRowCount(n_rows - 1)

    def copy_selection(self):
        copied_cells = sorted(self.selectedIndexes())

        copy_text = ''
        max_column = copied_cells[-1].column()
        for c in copied_cells:
            cell_item = self.item(c.row(), c.column())

            if cell_item is None:
                copy_text += ""
            else:
                copy_text += cell_item.text()

            if c.column() == max_column:
                copy_text += '\n'
            else:
                copy_text += '\t'

        get_app().clipboard().setText(copy_text)

    def paste_selection(self):
        copied_cells = sorted(self.selectedIndexes())

        # Paste clipboard contents from the first cell that was selected, and expand down and right
        first_row = copied_cells[0].row()
        first_column = copied_cells[0].column()

        clipboard_text = get_app().clipboard().text()

        rows = clipboard_text.split("\n")

        # sometimes the clipboard adds an extra newline at the end of copy, if so, remove it
        if rows[-1] == "":
            rows.pop(-1)

        if len(rows) + first_row > self.rowCount():  # add rows to table if pasted selection will "spill"
            self.setRowCount(first_row + len(rows))

        for row_ix, row in enumerate(rows):
            rowdata = row.split('\t')
            if rowdata == "":
                continue

            if len(rowdata) + first_column > self.columnCount():  # add columns if needed
                self.setColumnCount(first_column + len(rowdata))

            for col_ix, text in enumerate(rowdata):
                self.setItem(row_ix + first_row, col_ix + first_column, QTableWidgetItem(text))

    def delete_selection(self):
        copied_cells = sorted(self.selectedIndexes())
        for cell in copied_cells:
            # set all cells to be a blank QTableWidgetItem
            self.setItem(cell.row(), cell.column(), QTableWidgetItem())


    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        # Copying
        if event.key() == Qt.Key.Key_C and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.copy_selection()

        # Pasting
        if event.key() == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.paste_selection()

        # Cutting
        if event.key() == Qt.Key.Key_X and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.copy_selection()
            self.delete_selection()

        # Deleting
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selection()

    def stretch_horizontal_headers(self):
        n_cols = self.columnCount()
        for i in range(n_cols):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

