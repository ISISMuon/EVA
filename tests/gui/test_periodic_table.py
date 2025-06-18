from EVA.gui.windows.periodic_table.periodic_table_widget import PeriodicTableWidget, elements, elements_disable
import pytest

atm_nos = range(1, 119)
atm_nos_disable =[1, 36, 43, 54, 61, 84, 85, 86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118]
atm_nos_enable = [x for x in atm_nos if x not in set(atm_nos_disable)]

elements_enable = [x for x in elements if x not in set(elements_disable)]

data = list(zip(elements_enable, atm_nos_enable))

@pytest.mark.parametrize("element, atm_no", data)
def test_text_after_click(element, atm_no, qtbot):
    widget = PeriodicTableWidget()
    widget.show()

    getattr(widget, element+"_button").click()
    text = widget.element_info_text.toPlainText()
    first_line = text.split("\n")[0].startswith(f"Z = {atm_no}")
    assert first_line
    
def test_text_after_find(qtbot):
    pass