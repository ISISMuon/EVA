import logging

from EVA.core.app import get_config

logger = logging.getLogger(__name__)


class SettingsPresenter:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.load_current_settings()

        self.view.plot_fill_colour_button.clicked.connect(self.view.open_colour_dialog)
        self.view.colour_dialog.currentColorChanged.connect(
            lambda: self.view.set_fill_colour_preview(
                self.view.colour_dialog.currentColor().name()
            )
        )
        self.view.apply_button.clicked.connect(self.on_apply)

        self.view.working_dir_browse_button.clicked.connect(self.on_wdir_btn_click)
        self.view.srim_exe_dir_button.clicked.connect(self.on_srim_exe_dir_btn_click)
        self.view.srim_output_directory_button.clicked.connect(
            self.on_srim_out_dir_btn_click
        )

    def on_wdir_btn_click(self):
        dir = self.view.get_directory()

        if dir is not None:
            self.view.working_dir_label.setText(dir)

    def on_srim_exe_dir_btn_click(self):
        dir = self.view.get_directory()

        if dir is not None:
            self.view.srim_exe_dir_label.setText(dir)

    def on_srim_out_dir_btn_click(self):
        dir = self.view.get_directory()

        if dir is not None:
            self.view.srim_out_dir_label.setText(dir)

    def load_current_settings(self):
        config = get_config()

        settings = {
            "working_dir": config["general"]["working_directory"],
            "srim_exe_dir": config["SRIM"]["installation_directory"],
            "srim_out_dir": config["SRIM"]["output_directory"],
            "fill_colour": config["plot"]["fill_colour"],
        }

        self.view.set_settings(settings)

    def on_apply(self):
        settings = self.view.get_settings()

        restructured_settings = {
            "general": {"working_directory": settings["working_dir"]},
            "SRIM": {
                "installation_directory": settings["srim_exe_dir"],
                "output_directory": settings["srim_out_dir"],
            },
            "plot": {"fill_colour": settings["fill_colour"]},
        }

        self.model.apply_settings(restructured_settings)
        self.view.settings_applied_s.emit(restructured_settings)

        self.view.display_message(
            title="Success", message="Settings were successfully applied."
        )
