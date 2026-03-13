import matplotlib.pyplot as plt

from EVA.gui.windows.srim.trim_model import TrimModel


class TrimFitModel(TrimModel):
    def __init__(self):
        super().__init__()

        self.fig, self.ax = self.plot_initial()

        self.input_layers = [
            {"name": "Beamline Window", "thickness": 0.05},
            {"name": "Air (compressed)", "thickness": 0.067},
            {"name": "AlN", "thickness": 0.1, "density": 2.70},
            {"name": "SiO", "thickness": 0.1, "density": 1.4},
            {"name": "Cu", "thickness": 0.1, "density": 8.96},
        ]

    def plot_initial(self):
        momenta = [16.5, 17, 18, 19, 21, 22, 23, 24, 25]

        cu = [0, 0.02, 0.03, 0.05, 0.06, 0.2, 0.6, 0.9, 1]
        si = [0.3, 0.7, 0.9, 0.95, 1, 0.8, 0.3, 0.1, 0]
        n = [1, 0.4, 0.25, 0.2, 0.1, 0.05, 0, 0, 0]
        al = [1, 0.4, 0.05, 0, 0, 0, 0, 0, 0]

        fig, ax = plt.subplots()

        ax.plot(momenta, cu, "o-", label="Cu")
        ax.plot(momenta, si, "o-", label="Si")
        ax.plot(momenta, n, "o-", label="N")
        ax.plot(momenta, al, "o-", label="Al")

        ax.legend()

        return fig, ax
