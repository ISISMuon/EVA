from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QTextEdit, QPushButton, QTableWidget, QComboBox, QWidget, QHBoxLayout, QLineEdit, QVBoxLayout, QScrollArea,
    QCheckBox, QTabWidget, QFormLayout, QSizePolicy, QDialogButtonBox, QTableWidgetItem, QMessageBox
)

class ParameterConstraintWidget(QScrollArea):
    def __init__(self, parameter_names):
        super().__init__()
        self.setWidgetResizable(True)
        self.content = QWidget(self)
        self.description = QLabel()

        # See https://lmfit.github.io/lmfit-py/constraints.html#supported-operators-functions-and-constants
        self.description.setText("Constrain a parameter with a function expression. \nExample: p0_sigma = 2*p1_sigma")
        self.description.setMaximumHeight(50)

        self.parameter_name_labels = []
        self.parameter_constraint_line_edits = []

        self.content_layout = QGridLayout(self.content)
        self.content_layout.addWidget(self.description, 0, 0, 1, -1)
        self.content.setLayout(self.content_layout)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self.content)

        for i, name in enumerate(parameter_names):
            label = QLabel(f"{name} = ")
            line_edit = QLineEdit()
            line_edit.setFixedHeight(25)
            label.setFixedHeight(25)

            self.parameter_constraint_line_edits.append(line_edit)
            self.parameter_name_labels.append(label)

            self.content_layout.addWidget(label, i+2, 0)
            self.content_layout.addWidget(line_edit, i+2, 1)

        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

class ParametersBoundsWidget(QWidget):
    def __init__(self, param_names):
        super().__init__()
        self.param_names = param_names

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.description = QLabel("Set upper and lower bounds on parameters.")

        self.table = QTableWidget()
        self.table.showGrid()
        self.table.setRowCount(len(param_names))
        self.table.setColumnCount(2)

        self.table.setHorizontalHeaderLabels(["Min", "Max"])
        self.table.setVerticalHeaderLabels(param_names)

        self.layout.addWidget(self.description)
        self.layout.addWidget(self.table)

class ParameterFixedWidget(QWidget):
    def __init__(self, available_params):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.checkboxes = []

        self.description = QLabel("Ticked parameters will NOT be optimised and will remain at initial values.")
        self.description.setFixedHeight(25)
        self.layout.addWidget(self.description, 0, 0)

        for i, param in enumerate(available_params):
            #row, col = divmod(i, 2)
            self.checkboxes.append(QCheckBox(param))
            self.layout.addWidget(self.checkboxes[i], i+1, 0)

        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

class ConstraintsWindow(QDialog):
    param_settings_saved_s = pyqtSignal(dict)

    def __init__(self, parent, params):
        super().__init__(parent)
        self.setWindowTitle("Set Parameter Constraints and Bounds")
        self.setMinimumSize(600, 400)
        self.params = params
        self.parameter_names = self.get_param_names()
        self.parameter_names_and_values = self.get_param_names_and_values()
        self.init_gui()

    def init_gui(self):
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Displays all parameters in model and their initial values
        self.current_param_names = QLabel("Initial values")
        self.current_param_names_text_edit = QTextEdit()
        self.current_param_names_text_edit.setText("\n".join(self.parameter_names_and_values))
        self.current_param_names_text_edit.setReadOnly(True)
        self.current_param_names_text_edit.setMaximumWidth(200)

        # Presets to make it faster to analyse - currently not in use

        """
        self.presets_label = QLabel("Presets")
        self.preset_share_sigma = QPushButton("Share sigma between all peaks")
        self.preset_share_sigma.clicked.connect(lambda: self.share_peak_param_between_all("sigma"))

        self.preset_share_area = QPushButton("Share amplitude between all peaks")
        self.preset_share_area.clicked.connect(lambda: self.share_peak_param_between_all("amplitude"))
        """

        # Set up tabs
        self.constraints_menu = ParameterConstraintWidget(self.parameter_names)
        self.bounds_menu = ParametersBoundsWidget(self.parameter_names)
        self.set_fixed_menu = ParameterFixedWidget(self.parameter_names)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.constraints_menu, "Constraints")
        self.tabs.addTab(self.bounds_menu, "Bounds")
        self.tabs.addTab(self.set_fixed_menu, "Fixed parameters")

        # Set up dialogue buttons
        self.button_box = QDialogButtonBox()
        self.button_box.addButton("Apply", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.accepted.connect(self.on_apply)
        self.button_box.rejected.connect(self.on_cancel)

        # Add everything to layout
        self.layout.addWidget(self.current_param_names, 0, 0)
        self.layout.addWidget(self.current_param_names_text_edit, 1, 0, 3, 1)
        #self.layout.addWidget(self.presets_label, 0, 1)
        #self.layout.addWidget(self.preset_share_sigma, 1, 1)
        #self.layout.addWidget(self.preset_share_area, 1, 2)
        self.layout.addWidget(self.tabs, 1, 1, 3, -1)
        self.layout.addWidget(self.button_box, 4, 1, 1, -1)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.load_current_settings()

    def get_param_names_and_values(self):
        names_and_values = []
        for p in self.params:
            for var in self.params[p]:
                names_and_values.append(f"{p}_{var} = {self.params[p][var]["value"]}")

        return names_and_values

    def get_param_names(self):
        names = []
        for name in self.params:
            for var in self.params[name]:
                names.append(f"{name}_{var}")

        return names

    def load_current_settings(self):
        for i, param in enumerate(self.parameter_names):
            peak_name, var_name = param.split("_")
            obj = self.params[peak_name][var_name]

            # load bounds data
            if obj.get("min", None) is not None:
                self.bounds_menu.table.setItem(i, 0, QTableWidgetItem(f"{obj["min"]:.2f}"))
            else:
                self.bounds_menu.table.setItem(i, 0, QTableWidgetItem())

            if obj.get("max", None) is not None:
                self.bounds_menu.table.setItem(i, 1, QTableWidgetItem(f"{obj["max"]:.2f}"))
            else:
                self.bounds_menu.table.setItem(i, 0, QTableWidgetItem())

            # load fixed parameters
            if not obj.get("vary", None):
                self.set_fixed_menu.checkboxes[i].setChecked(True)
            else:
                self.set_fixed_menu.checkboxes[i].setChecked(False)

            # load constraints
            if obj.get("expr", None) is not None:
                self.constraints_menu.parameter_constraint_line_edits[i].setText(obj["expr"])
            else:
                self.constraints_menu.parameter_constraint_line_edits[i].setText("")

    # loads only constraints
    def load_current_constraints(self):
        for i, param in enumerate(self.parameter_names):
            peak_name, var_name = param.split("_")
            obj = self.params[peak_name][var_name]

            # load constraints
            if obj.get("expr", None) is not None:
                self.constraints_menu.parameter_constraint_line_edits[i].setText(obj["expr"])
            else:
                self.constraints_menu.parameter_constraint_line_edits[i].setText("")


    def save_current_settings(self):
        for i, param in enumerate(self.parameter_names):
            peak_name, var_name = param.split("_")
            obj = self.params[peak_name][var_name]

            lower_bound = self.bounds_menu.table.item(i, 0)
            upper_bound = self.bounds_menu.table.item(i, 1)

            constraint = self.constraints_menu.parameter_constraint_line_edits[i].text().strip()

            is_fixed = self.set_fixed_menu.checkboxes[i].isChecked()

            if lower_bound is not None:
                if lower_bound.text().strip() != "":
                    obj["min"] = float(lower_bound.text())

                elif obj.get("min", False):
                    obj.pop("min")

            if upper_bound is not None:
                if upper_bound.text().strip() != "":
                    obj["max"] = float(upper_bound.text())

                elif obj.get("max", False):
                    obj.pop("max")

            if constraint:
                obj["expr"] = constraint

            elif obj.get("expr", False):
                obj.pop("expr")

            obj["vary"] = not is_fixed

    def share_peak_param_between_all(self, param_name):
        # NOTE: WILL BREAK IF ID SYSTEM IS CHANGED
        constraint = f"p0_{param_name}"
        for i, name in enumerate(self.constraints_menu.parameter_name_labels):
            prefix, text = name.text().split("_") # get text from label and get prefix
            var = text.split(" = ")[0] # get parameter name

            if prefix != "background" and prefix != "p0" and var == param_name:
                self.constraints_menu.parameter_constraint_line_edits[i].setText(constraint)

    def on_apply(self):
        # save settings
        try:
            self.save_current_settings()
        except ValueError:
            _ = QMessageBox.critical(self, "Constraint error", "Invalid bounds specified.")
            return
        self.param_settings_saved_s.emit(self.params)
        self.close()

    def on_cancel(self):
        # prompt user to double-check if they want to close
        self.close()
