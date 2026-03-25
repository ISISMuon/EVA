from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem, QStyledItemDelegate, QLineEdit, QCompleter


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
    
class CompleterDelegate(QStyledItemDelegate):
    def __init__(self, words_provider, parent=None):
        super().__init__(parent)
        self.words_provider = words_provider

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)

        # support both static list and dynamic function
        if callable(self.words_provider):
            words = self.words_provider()
        else:
            words = self.words_provider

        completer = QCompleter(list(words), editor)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        editor.setCompleter(completer)
        return editor
