import logging

from PyQt6.QtCore import pyqtSignal

from EVA.gui.dialogs.energy_corrections.energy_corrections_model import EnergyCorrectionsModel
from EVA.gui.dialogs.energy_corrections.energy_corrections_view import EnergyCorrectionsView

logger = logging.getLogger(__name__)

class EnergyCorrectionsPresenter:
    def __init__(self, view: EnergyCorrectionsView, model: EnergyCorrectionsModel):
        self.view = view
        self.model = model

        self.populate_table()
        self.view.apply_button.clicked.connect(self.on_apply)

    def populate_table(self):
        current_corrections = self.model.corrections
        table_contents = [[detector, *settings["e_corr_coeffs"]] for detector, settings in current_corrections.items()]
        use_corrections = [settings["use_e_corr"] for settings in current_corrections.values()]

        self.view.correction_table.update_contents(table_contents)
        self.view.setup_table_checkboxes(use_corrections)

    def on_apply(self):
        try:
            self.model.corrections = self.view.get_energy_correction_selections()
            self.model.apply_corrections()
            self.view.energy_corrections_applied_s.emit(self.model.corrections)

        except (ValueError, AttributeError):
            self.view.display_error_message(title="Form error", message="Invalid energy corrections in table!")
