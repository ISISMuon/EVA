from EVA.core.data_structures.run import Run

class EnergyCorrectionsModel:
    def __init__(self, run: Run):
        self.run = run
        self.corrections = self.run.energy_corrections

    def apply_corrections(self):
        self.run.set_corrections(self.corrections)