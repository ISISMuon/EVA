from EVA.core.data_structures.run import Run
from EVA.gui.base.base_dialog import BaseDialog
from EVA.gui.dialogs.energy_corrections.energy_corrections_model import EnergyCorrectionsModel
from EVA.gui.dialogs.energy_corrections.energy_corrections_presenter import EnergyCorrectionsPresenter
from EVA.gui.dialogs.energy_corrections.energy_corrections_view import EnergyCorrectionsView

class EnergyCorrectionsDialog(BaseDialog):
    def __init__(self, run: Run):
        view = EnergyCorrectionsView()
        model = EnergyCorrectionsModel(run)
        presenter = EnergyCorrectionsPresenter(view, model)

        super().__init__(view, model, presenter)