from EVA.gui.windows.muonic_xray_simulation.model_spectra_model import ModelSpectraModel

class ModelSpectraPresenter(object):
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.view.on_simulation_start_s.connect(self.start_simulation)
        self.view.e_min.textChanged.connect(lambda: self.view.e_range_auto.setChecked(False))
        self.view.e_max.textChanged.connect(lambda: self.view.e_range_auto.setChecked(False))

        self.view.window_closed_s.connect(self.model.close_figures)
        self.populate_gui()

    def start_simulation(self):
        parameters = self.view.get_form_data()
        if not parameters:
            return

        fig, axs = self.model.model_spectrum(**parameters)
        self.view.plot.update_plot(fig, axs)

    def populate_gui(self):
        element_list = self.model.element_names
        self.view.populate_gui(element_list)