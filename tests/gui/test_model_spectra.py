import pytest
from pytestqt.plugin import qtbot
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

from EVA.gui.windows.muonic_xray_simulation.model_spectra_view import ModelSpectraView

base_test = {
    "elements": ["Ag", "Hg"],
    "proportions": [1.0, 2.0],
    "detectors": ["GE1", "GE3"],
    "show_primary": True,
    "show_secondary": True,
    "show_components": False,
    "dx": 0.1
}

class TestModelSpectrumWindow:
    # this will run once before all other tests in the class
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.widget = QWidget()
        self.window = ModelSpectraView(self.widget)
        qtbot.addWidget(self.window)

    @pytest.fixture()
    def add_and_remove_elements(self, qtbot):
        element_selector = self.window.element_selector
        # add 8 element selectors to get a total of 9 (remember there already exists one element selector on start)
        for i in range(8):
            qtbot.mouseClick(element_selector.add_element_button, Qt.MouseButton.LeftButton)

        # remove items (remember that positions change every time an item is removed from the list)
        qtbot.mouseClick(element_selector.element_selector_items[0].remove_button, Qt.MouseButton.LeftButton)
        qtbot.mouseClick(element_selector.element_selector_items[3].remove_button, Qt.MouseButton.LeftButton)
        qtbot.mouseClick(element_selector.element_selector_items[5].remove_button, Qt.MouseButton.LeftButton)
        qtbot.mouseClick(element_selector.element_selector_items[0].remove_button, Qt.MouseButton.LeftButton)

        # add another item (at end)
        qtbot.mouseClick(element_selector.add_element_button, Qt.MouseButton.LeftButton)

    def test_add_and_remove_element_selection(self, qtbot, add_and_remove_elements):
        order = [2,3,5,6,8,9] # expected order of items
        actual_order = [item.id for item in self.window.view.element_selector.element_selector_items]

        # check that the element selector ids are in the expected order
        assert actual_order == order

    def test_simulation_start_on_button_click(self, qtbot):
        axes = self.window.view.plot.canvas.axs
        qtbot.mouseClick(self.window.view.start_button, Qt.MouseButton.LeftButton)
        new_axes = self.window.view.plot.canvas.axs

        # check that there was a change in the axes
        assert new_axes != axes

    def test_set_and_get_form_data(self, qtbot):
        self.window.view.set_form_data(base_test)
        form_data = self.window.view.get_form_data()

        assert form_data == base_test



