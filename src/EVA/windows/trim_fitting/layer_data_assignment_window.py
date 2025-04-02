import os.path

import numpy as np
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QPushButton, QTableWidgetItem, QComboBox, QVBoxLayout, QLabel, QFileDialog, \
    QGridLayout, QSpinBox, QSpacerItem, QSizePolicy

from EVA.core.app import get_config
from EVA.widgets.base.base_table import BaseTable
from EVA.widgets.base.base_view import BaseView


class LayerDataAssignmentWidget(BaseView):
    data_loaded_s = pyqtSignal(dict, list)

    def __init__(self, layer_names=None, form_data=None, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.form_data = form_data

        self.init_gui()

        self.column_selectors = [self.momentum_column_selector]
        self.column_selector_items = ["Don't include"]


        if self.form_data is not None:
            self.file_path = form_data["file_path"]
            self.n_cols = form_data["n_cols"]
            self.skiprows = form_data["skiprows"]
            self.selected_indices = form_data["selected_indices"]

            self.setup_table(layer_names)

            self.update_form()
            self.toggle_column_selection_area(True)

            try:
                self.data = np.loadtxt(self.file_path, delimiter=",", dtype="float", skiprows=self.skiprows)
            except Exception as e:
                self.display_error_message(message=f"An error occurred while loading the file: {e}")
                return

        else:
            self.file_path = None
            self.n_cols = None
            self.skiprows = 0
            self.data = None
            self.selected_indices = None

            self.toggle_column_selection_area(False)
            self.setup_table(layer_names)

    def toggle_column_selection_area(self, visibility: bool):
        self.momentum_label.setEnabled(visibility)
        self.momentum_column_selector.setEnabled(visibility)
        self.layer_table.setEnabled(visibility)
        self.apply_button.setEnabled(visibility)

    def setup_table(self, layer_names):
        n_layers = len(layer_names)

        self.layer_table.setRowCount(n_layers)

        for i, layer_name in enumerate(layer_names):
            column_selector = QComboBox()
            column_selector.addItems(self.column_selector_items)
            column_selector.setCurrentIndex(0)

            self.column_selectors.append(column_selector)

            self.layer_table.setItem(i, 0, QTableWidgetItem(layer_name))
            self.layer_table.setCellWidget(i, 1, column_selector)

    def default_column_selections(self):
        selections = [1, 0, 0]

        for i, selector in enumerate(self.column_selectors[3:]):
            if i <= self.n_cols-2:
                selections.append(i+2)
            else:
                selections.append(0)

        return selections

    def on_load_file(self):
        default_dir = get_config()["general"]["working_directory"]
        file_filter = "CSV file (*.csv)"

        file = QFileDialog.getOpenFileName(self, 'Load File', directory=default_dir, filter=file_filter)
        if not file[0]:
            return

        self.file_path = file[0]
        self.skiprows = self.skip_rows_spin_box.value()

        try:
            self.data = np.loadtxt(self.file_path, delimiter=",", dtype="float", skiprows=self.skiprows)

        except Exception as e:
            self.display_error_message(message=f"An error occurred while loading the file: {e}")
            return

        self.n_cols = np.shape(self.data)[1]
        self.selected_indices = self.default_column_selections()

        self.update_form()
        self.toggle_column_selection_area(True)

    def get_column_selections(self) -> np.ndarray | None:
        layer_data = []
        selected_columns = []

        for i, selector in enumerate(self.column_selectors):
            selector_index = selector.currentIndex()

            # ignore if no column is assigned
            if selector_index == 0:
                layer_data.append([])
                continue

            # if column has already been assigned (cannot assign multiple layers to same column)
            if selector_index not in selected_columns:
                selected_columns.append(selector_index)
            else:
                self.display_error_message(
                    message="Invalid column selection. Cannot assign multiple layers to same data column.")
                return None

            layer_data.append(self.data[:, selector_index-1])

        # Clean up and convert to numpy array and check that all columns have the same length
        try:
            selections = np.array([layer if any(layer) else np.zeros_like(layer_data[0]) for layer in layer_data])
            print("sel", selections)
        except Exception as e:
            self.display_error_message(message="All data columns must be of equal length!")
            raise e
            return None

        return selections


    def on_apply(self):
        selected_data = self.get_column_selections()
        selected_indices = [selector.currentIndex() for selector in self.column_selectors]

        if selected_data is None:
            return

        form_data = {
            "file_path": self.file_path,
            "skiprows": self.skiprows,
            "n_cols": self.n_cols,
            "selected_indices": selected_indices
        }

        if self.data is None: # if you try to exit without data loaded (somehow)
            self.display_error_message(message="Please load a valid .csv file.")

        self.data_loaded_s.emit(form_data, selected_data)
        self.close()

    def update_form(self):
        name = os.path.basename(self.file_path)
        self.file_path_label.setText(f"Filename: {str(name)}")

        self.skip_rows_spin_box.setValue(self.skiprows)
        self.num_cols_label.setText(f"Found {self.n_cols} columns in data. Select which layers to include.")

        self.column_selector_items = [f"Column {col}" for col in range(self.n_cols)]
        self.column_selector_items.insert(0, "Don't include")

        for i, selector in enumerate(self.column_selectors):
            selector.clear()
            selector.addItems(self.column_selector_items)

            if i > len(self.selected_indices)-1:
                selector.setCurrentIndex(0)
            else:
                selector.setCurrentIndex(self.selected_indices[i])

    def init_gui(self):
        self.setMinimumSize(600, 400)

        self.momentum_column_selector = QComboBox()
        self.num_cols_label = QLabel()

        self.file_path_label = QLabel("Filename:")
        self.skip_rows_label = QLabel("Number of rows in header:")
        self.skip_rows_spin_box = QSpinBox()
        self.skip_rows_spin_box.setValue(1)

        self.momentum_label = QLabel("Momentum")

        self.layer_table = BaseTable()
        self.layer_table.setColumnCount(2)
        self.layer_table.setHorizontalHeaderLabels(["Layer name", "Assign column"])
        self.layer_table.stretch_horizontal_header()

        self.file_select_button = QPushButton("Load file...")
        self.apply_button = QPushButton("Apply")

        self.file_select_button.clicked.connect(self.on_load_file)
        self.apply_button.clicked.connect(self.on_apply)

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.skip_rows_label, 0, 0, 1, -1)
        layout.addWidget(self.skip_rows_spin_box, 0, 1, 1, 1)
        layout.addWidget(self.file_path_label, 1, 0, 1, 1)
        layout.addWidget(self.file_select_button, 1, 1, 1, 1)

        layout.addWidget(self.num_cols_label, 4, 0, 1, -1)
        layout.addWidget(self.momentum_label, 5, 0, 1, 1)
        layout.addWidget(self.momentum_column_selector, 5, 1, 1, 1)
        layout.addWidget(self.layer_table, 6, 0, 1, -1)
        layout.addWidget(self.apply_button, 7, 0, 1, -1)
