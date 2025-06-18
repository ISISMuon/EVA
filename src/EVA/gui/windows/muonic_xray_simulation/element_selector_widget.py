from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QComboBox, QGridLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton


class ElementSelectorItem(QWidget):
    remove_button_clicked_s = pyqtSignal(int)

    def __init__(self, elements, item_id):
        super().__init__()
        self.element_list = elements
        self.id = item_id

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.element_selection_cbox = QComboBox()
        self.element_selection_cbox.addItems(elements)
        self.ratio_line_edit = QLineEdit("1")

        self.remove_button = QPushButton("X")
        self.remove_button.setFixedWidth(25)
        self.remove_button.clicked.connect(self.on_remove)

        self.layout.addWidget(self.element_selection_cbox, stretch=4)
        self.layout.addWidget(self.ratio_line_edit, stretch=1)
        self.layout.addWidget(self.remove_button)

    def set_element(self, element):
        self.element_selection_cbox.setCurrentText(element)

    def get_element(self):
        return self.element_selection_cbox.currentText()

    def set_ratio(self, ratio):
        self.ratio_line_edit.setText(str(ratio))

    def get_ratio(self):
        return float(self.ratio_line_edit.text())

    def on_remove(self):
        self.remove_button_clicked_s.emit(self.id)


class ElementSelectorWidget(QWidget):
    def __init__(self, elements=None):
        super().__init__()
        self.element_list = elements
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.element_label = QLabel("Element")
        self.ratio_label = QLabel("Ratio")
        self.add_element_button = QPushButton("Add element")
        self.add_element_button.clicked.connect(self.add_element)
        self._ids = 0

        self.element_selector_items = []

        self.layout.addWidget(self.element_label, 0, 0)
        self.layout.addWidget(self.ratio_label, 0, 2)


    def add_element(self):
        item_id = self._ids

        element_selector_item = ElementSelectorItem(self.element_list, item_id)
        element_selector_item.remove_button_clicked_s.connect(self.remove_element)

        self.element_selector_items.append(element_selector_item)
        self._ids += 1
        self.recalculate_layout()

    def remove_element(self, item_id):
        item = self.get_item(item_id)

        self.layout.removeWidget(item)
        self.element_selector_items.remove(item)

        self.recalculate_layout()

    def set_elements(self, element_list):
        self.element_list = element_list

    def get_item(self, item_id):
        return [item for item in self.element_selector_items if item.id == item_id][0]


    def recalculate_layout(self):
        # add all element selector items to layout
        for i, item in enumerate(self.element_selector_items):
            self.layout.addWidget(item, 1+i, 0, 1, -1)

        # add button to the end of layout
        self.layout.addWidget(self.add_element_button, 2+len(self.element_selector_items), 0, 1, -1)

    def get_elements(self):
        return [item.get_element() for item in self.element_selector_items]

    def get_ratios(self):
        return [item.get_ratio() for item in self.element_selector_items]

