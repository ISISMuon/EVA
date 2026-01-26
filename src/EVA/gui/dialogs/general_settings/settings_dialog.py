from EVA.gui.base.base_dialog import BaseDialog
from EVA.gui.dialogs.general_settings.settings_model import SettingsModel
from EVA.gui.dialogs.general_settings.settings_presenter import SettingsPresenter
from EVA.gui.dialogs.general_settings.settings_view import SettingsView


class SettingsDialog(BaseDialog):
    def __init__(self):
        view = SettingsView()
        model = SettingsModel()
        presenter = SettingsPresenter(view, model)

        super().__init__(view, model, presenter)
