import logging
import os
import matplotlib.backend_bases
from matplotlib.backend_bases import MouseButton

from EVA.core.app import get_config
from EVA.gui.windows.peakfit.constraints_window import ConstraintsWindow
from EVA.gui.windows.peakfit.model_fit_model import ModelFitModel
from EVA.gui.windows.peakfit.peakfit_model import PeakFitModel

logger = logging.getLogger(__name__)

class PeakFitPresenter(object):
    def __init__(self, view, model, mf_model, parent=None):
        self.view = view
        self.model = model
        self.mf_model = mf_model

        # connect all buttons to functions
        self.view.add_peak_button.clicked.connect(lambda: self.set_add_peak_mode(True))
        self.view.cancel_add_peak_button.clicked.connect(lambda: self.set_add_peak_mode(False))
        self.view.constraints_button.clicked.connect(self.launch_constraints_menu)

        self.view.save_initial_params_button.clicked.connect(self.save_init_params)
        self.view.load_initial_params_button.clicked.connect(self.load_init_params)
        self.view.save_fit_report_button.clicked.connect(self.save_fit_report)
        self.view.save_fitted_model_button.clicked.connect(self.save_fitted_model)
        self.view.fit_table_select_button.clicked.connect(self.browse_fit_table_file)

        self.view.add_model_button.clicked.connect(self.add_model)
        self.view.fit_model_button.clicked.connect(self.start_model_fit)

        self.view.fit_initial_params_button.clicked.connect(self.start_peakfit)
        self.view.plot_initial_params_button.clicked.connect(self.plot_initial)
        # display figure from model in the PlotWidget
        self.view.plot.update_plot(self.model.fig, self.model.axs)
        self.view.model_plot.update_plot(self.mf_model.fig, self.mf_model.axs)
        self.view.plot.canvas.mpl_connect('button_press_event', self.on_plot_click)

        # setting up connections for tables
        self.view.peak_removal_requested_s.connect(self.remove_peak)
        self.view.model_removal_requested_s.connect(self.remove_model)

        # generate option buttons for these tables every time their contents are updated
        self.view.initial_model_params_table.contents_updated_s.connect(
            lambda: self.view.setup_modelfit_table_options(3, self.mf_model.initial_model_params))

        self.view.initial_peak_params_table.contents_updated_s.connect(
            lambda: self.view.setup_peakfit_table_options(4, self.model.initial_peak_params))

        # modify parameter when user edits a cell in these tables
        self.view.initial_peak_params_table.user_edited_cell_s.connect(self.modify_peak_parameter)
        self.view.initial_model_params_table.user_edited_cell_s.connect(self.modify_model_parameter)

        self.view.initial_bg_params_table.user_edited_cell_s.connect(
            lambda r, c: self.modify_bg_parameter(r, c, self.view.initial_bg_params_table, self.model.initial_bg_params))

        self.view.initial_model_bg_params_table.user_edited_cell_s.connect(
            lambda r, c: self.modify_bg_parameter(r, c, self.view.initial_model_bg_params_table, self.mf_model.initial_bg_params))

        self.view.e_range_min_line_edit.textEdited.connect(lambda x: self.view.auto_e_range_checkbox.setChecked(False))
        self.view.e_range_max_line_edit.textEdited.connect(lambda x: self.view.auto_e_range_checkbox.setChecked(False))

        self.view.model_e_range_min_line_edit.textEdited.connect(
            lambda x: self.view.model_auto_e_range_checkbox.setChecked(False))
        self.view.model_e_range_max_line_edit.textEdited.connect(
            lambda x: self.view.model_auto_e_range_checkbox.setChecked(False))

        # swap which figure is on top in the stacked widget when the tab is switched
        self.view.side_panel_tabs.currentChanged.connect(lambda i: self.view.plot_container_widget.setCurrentIndex(i))

        self.view.window_closed_s.connect(self.model.close_figures)
        self.view.window_closed_s.connect(self.mf_model.close_figures)

    def set_add_peak_mode(self, value: bool):
        # Toggles "add peak mode"
        self.view.add_peak_button.setVisible(not value)
        self.view.cancel_add_peak_button.setVisible(value)
        self.view.add_peak_label.setVisible(value)
        self.model.add_peak_mode = value
        self.view.peak_params_tabs.setCurrentIndex(0)
        self.view.bg_params_tabs.setCurrentIndex(0)

    def on_plot_click(self, event: matplotlib.backend_bases.MouseEvent):
        # Ensures that plot was clicked correctly while in add peak mode
        if not (self.model.add_peak_mode and event.button is MouseButton.RIGHT and event.inaxes):
            return

        logger.debug(f"Plot clicked at {event.xdata}, {event.ydata}")

        # Release any zoom rubber band or pan if user right-clicked while using navigation tools
        self.view.plot.release_navigation(event)

        # ask user if they want to add peak
        if not self.view.prompt_add_peak(event.xdata):
            return

        self.model.add_initial_peak_params(event.xdata)
        self.view.initial_peak_params_table.update_contents(self.format_params(self.model.initial_peak_params))
        self.set_add_peak_mode(False)

    def plot_initial(self):
        if len(self.model.initial_peak_params) < 1:
            self.view.display_error_message(message="Please add at least one peak to fit.")
            logger.error("No peaks selected - aborting peakfit.")
            return

        self.model.plot_initial_params()
        self.view.plot.canvas.draw()

    def start_peakfit(self):
        if len(self.model.initial_peak_params) < 1:
            self.view.display_error_message(message="Please add at least one peak to fit.")
            logger.error("No peaks selected - aborting peakfit.")
            return

        if self.view.auto_e_range_checkbox.isChecked():
            self.model.calculate_x_range()
            self.view.update_e_range_form(self.model.x_range)
        else:
            try:
                self.model.x_range = self.get_e_range()
            except ValueError:
                self.view.display_error_message(message="Please specify a valid energy range.")
                logger.error("Invalid energy range - aborting peakfit.")
                return
        try:
            self.model.fit_peaks()

        except TypeError as e:
            if e.args[0] == "Not enough points":
                self.view.display_error_message(message=
                    "Selected fitting range too narrow to fit curve (Not enough data points in range).\n"
                    "Either specify a wider energy range or increase initial peak width of peaks (or increase binning).")

                logger.error("Not enough points to fit - aborting peakfit. \nError message: %s", e.args[0])
                raise e
            else:
                self.view.display_error_message(message=
                    f"An unexpected error occurred. Please ensure your initial parameters are good enough, and"
                    f" that any constraints / bounds are valid, if specified.\n"
                    f"Error message from lmfit: {e.args[0]}")
                # raise e
                logger.error("Unexpected error - aborting peakfit. \nError message from lmfit: %s", e.args[0])
                return

        except RecursionError:
            self.view.display_error_message(message="A recursion error occurred. If parameter constraints have been set, "
                                          "ensure they are not recursive.")
            logger.error("Recusion error, likely due to recursive constraints applied - aborting peakfit.")
            return

        except (ValueError, IndexError) as e:
            self.view.display_error_message(message=f"An unexpected error occurred. Please ensure your initial parameters "
                                          f"are good enough.\nError message from lmfit: {e.args[0]}")
            logger.error("Unexpected error - aborting peakfit. \nError message from lmfit: %s", e.args[0])
            return

        self.model.plot_fit()
        self.view.plot.update_plot()
        self.view.fitted_peak_params_table.update_contents(self.format_params(self.model.fitted_peak_params))
        self.view.fitted_bg_params_table.update_contents(self.format_params(self.model.fitted_bg_params))

        self.view.peak_params_tabs.setCurrentIndex(1)
        self.view.bg_params_tabs.setCurrentIndex(1)

        # Display fit report in text window
        self.view.fit_report_text_browser.setText(self.model.fit_result.fit_report())

        # If errors could not be estimated, notify user
        if not self.model.fit_result.errorbars:
            self.view.display_error_message(message="Could not estimate fit errors. Please adjust your initial parameters "
                                          "and constraints / bounds if specified.")
            logger.warning("Failed to estimate fit errors.")

    def start_model_fit(self):
        if len(self.mf_model.initial_peak_params) < 1:
            self.view.display_error_message(message="Please add at least one peak to fit.")
            logger.error("No peaks selected - aborting peakfit.")
            return

        if self.view.model_auto_e_range_checkbox.isChecked():
            self.mf_model.calculate_x_range()
            self.view.update_model_e_range_form(self.mf_model.x_range)
        else:
            try:
                self.mf_model.x_range = self.get_model_e_range()
            except ValueError:
                self.view.display_error_message(message="Please specify a valid energy range.")
                logger.error("Invalid energy range - aborting peakfit.")
                return

        if self.view.constrain_proportions_checkbox.isChecked():
            try:
                self.mf_model.proportions_constraint = float(self.view.constrain_proportions_lineedit.text())
            except (ValueError, AttributeError):
                self.view.display_error_message(message="Invalid proportions constraint")
                logger.error("Invalid proportion constraint - aborting peakfit.")
                return
        try:
            self.mf_model.fit_model()
            self.mf_model.plot_fit()
            self.view.model_plot.canvas.draw()
            self.view.fitted_model_params_table.update_contents(self.format_params(self.mf_model.fitted_model_params))
            self.view.fitted_model_bg_params_table.update_contents(self.format_params(self.mf_model.fitted_bg_params))

            self.view.model_params_tabs.setCurrentIndex(1)
            self.view.model_bg_params_tabs.setCurrentIndex(1)
            self.view.model_fit_report_text_browser.setText(self.mf_model.fit_result.fit_report())

        except (TypeError, ValueError, Exception) as e:
            self.view.display_error_message(message=f"Unexpected error occurred: {e.args}")
            logger.error("Unexpected error occurred: %s", e.args)
            raise e

    @staticmethod
    def format_params(params: dict) -> list[list]:
        # restructure the data in a params array and convert parameters to strings
        data = []
        for param_id, param in params.items():
            row_data = [param_id] # set parameter ID as first element in row
            for var_name, var in param.items():
                if var.get("stderr", None) is not None:
                    item = f"{var["value"]:.3f} ± {var["stderr"]:.3f}"
                    if len(item) > 18: # if value becomes too large to fit cell, use scientific notation
                        item = f"{var["value"]:.2e} ± {var["stderr"]:.2e}"
                else:
                    item = f"{var["value"]:.3f}"
                    if len(item) > 18:
                        item = f"{var["value"]:.2e}"
                row_data.append(item)
            data.append(row_data)

        return data

    def modify_peak_parameter(self, row: int, col: int):
        key_order = ["center", "sigma", "amplitude"]

        table = self.view.initial_peak_params_table
        params = self.model.initial_peak_params

        # don't allow id changes (it complicates things since the id is the dictionary key (yes this is lazy))
        if col == 0:
            table.update_contents(self.format_params(params))
            return

        edited_cell = table.item(row, col)

        try:
            new_val = float(edited_cell.text())
            peak_id = table.item(row, 0).text()
            var_name = key_order[col - 1]
            params[peak_id][var_name]["value"] = new_val

        except (ValueError, AttributeError, TypeError) as e:
            self.view.display_error_message(message="Invalid value.")
            raise e

    def modify_model_parameter(self, row: int, col: int):
        key_order = ["scale", "x0"]

        table = self.view.initial_model_params_table
        params = self.mf_model.initial_model_params

        # don't allow id changes (it complicates things since the id is the dictionary key (yes this is lazy))
        if col == 0:
            table.update_contents(self.format_params(params))
            return

        edited_cell = table.item(row, col)

        try:
            new_val = float(edited_cell.text())
            peak_id = table.item(row, 0).text()
            var_name = key_order[col-1]
            params[peak_id][var_name]["value"] = new_val

        except (ValueError, AttributeError, TypeError) as e:
            self.view.display_error_message(message="Invalid value.")
            raise e

    def modify_bg_parameter(self, row: int, col: int, table, params):
        key_order = ["a", "b", "c"]

        # don't allow id changes (it complicates things since the id is the dictionary key (yes this is lazy))
        if col == 0:
            table.update_contents(self.format_params(params))
            return

        edited_cell = table.item(row, col)

        try:
            new_val = float(edited_cell.text())
            peak_id = table.item(row, 0).text()
            var_name = key_order[col-1]
            params[peak_id][var_name]["value"] = new_val

        except (ValueError, AttributeError, TypeError) as e:
            self.view.display_error_message(message="Invalid value.")
            raise e

    def launch_constraints_menu(self):
        # Launches dialog to select constraints and bounds

        all_params = {**self.model.initial_peak_params, **self.model.initial_bg_params}
        constraints_dialog = ConstraintsWindow(self.view, all_params)
        constraints_dialog.param_settings_saved_s.connect(self.set_constraints)
        logger.info("Launching constraints window.")
        constraints_dialog.show()
    
    def set_constraints(self, all_params: dict):
        # Updates the initial parameters in the model when signal is received from the constraint dialogue

        # separate the peak and background parameters again before updating model
        bg_params = {"background": all_params["background"]}
        peak_params = {k:v for k,v in all_params.items() if k != "background"}

        self.model.initial_peak_params = peak_params
        self.model.initial_bg_params = bg_params

    def get_e_range(self) -> tuple[float, float]:
        e_min = float(self.view.e_range_min_line_edit.text())
        e_max = float(self.view.e_range_max_line_edit.text())
        return e_min, e_max

    def get_model_e_range(self) -> tuple[float, float]:
        e_min = float(self.view.model_e_range_min_line_edit.text())
        e_max = float(self.view.model_e_range_max_line_edit.text())
        return e_min, e_max

    def browse_fit_table_file(self):
        def_dir = get_config()["general"]["working_directory"]
        path = self.view.get_load_file_path(default_dir=def_dir, file_filter="CSV files (*.csv)")
        if path:
            self.view.set_loaded_file_text(path)
            get_config()["general"]["fit_table_save_file"] = path
            logger.info("Selected fit table file: %s", path)

    def save_init_params(self):
        x_range = None if self.view.auto_e_range_checkbox.isChecked() else self.get_e_range()
        def_dir = get_config()["general"]["working_directory"]
        path = self.view.get_save_file_path(default_dir=def_dir, file_filter="JSON files (*.json)")
        if path:
            self.model.save_params(path, x_range)

    def load_init_params(self):
        def_dir = get_config()["general"]["working_directory"]
        path = self.view.get_load_file_path(default_dir=def_dir, file_filter="JSON files (*.json)")

        if not path:
            return

        self.model.load_params(path)
        self.view.initial_peak_params_table.update_contents(self.format_params(self.model.initial_peak_params))
        self.view.initial_bg_params_table.update_contents(self.format_params(self.model.initial_bg_params))

        if self.model.x_range is not None:
            self.view.update_e_range_form(self.model.x_range)
        else:
            self.view.auto_e_range_checkbox.setChecked(True)
            self.view.e_range_max_line_edit.clear()
            self.view.e_range_min_line_edit.clear()

    def save_fit_report(self):
        def_dir = get_config()["general"]["working_directory"]
        path = self.view.get_save_file_path(default_dir=def_dir, file_filter="Text files (*.txt)")
        if path:
            self.model.save_fit_report(path)

    def save_fitted_model(self):
        path = get_config()["general"]["fit_table_save_file"]
        if not path:
            self.view.display_error_message(message="No fit table file selected.")
            return

        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.isdir(parent_dir):
            self.view.display_error_message(
                message="Selected directory does not exist."
            )
            return
        if not self.model.fit_result:
            self.view.display_error_message(message="Please perform a peak fit to save fitted model.")
            return
        if self.model.run.momentum < 0:
            logger.warning("Run momentum not found, saving with value -100.")
            self.view.display_error_message(
                message="Run momentum not found, please manually replace -100 in fit table or "
                    "place the .nxs_se file in same folder as the .nxs run file and try again."
                
            )

        try:
            self.model.save_fitted_model(path)

        except PermissionError:
            self.view.display_error_message(message="Unable to save data to fit table, ensure it is not open elsewhere.")

    def add_model(self):
        def_dir = get_config()["general"]["working_directory"]
        path = self.view.get_load_file_path(default_dir=def_dir, file_filter="JSON files (*.json)")
        if path:
            self.mf_model.load_and_add_model(path)
            self.view.initial_model_params_table.update_contents(self.format_params(self.mf_model.initial_model_params))

    def remove_model(self, m_id: str):
        logger.debug("Removing model id %s.", m_id)

        self.mf_model.remove_model(m_id)
        self.view.initial_model_params_table.update_contents(self.format_params(self.mf_model.initial_model_params))

    def remove_peak(self, p_id: str):
        logger.debug("Removing peak id %s.", p_id)
        self.model.remove_initial_peak_param(p_id)
        self.view.initial_peak_params_table.update_contents(self.format_params(self.model.initial_peak_params))


    def on_replot_needed(self):
        self.model.replot_spectrum_residual()
        self.view.plot.update_plot()

        self.mf_model.replot_spectrum_residual()
        self.view.model_plot.update_plot()