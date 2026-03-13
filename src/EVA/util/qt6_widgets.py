from PyQt6.QtWidgets import QTableWidgetItem


class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text):
        super().__init__(text)
        try:
            self.value = float(text)
        except ValueError:
            self.value = float("-inf")  # Sort non-numeric items last

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)
