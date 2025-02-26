import logging

from EVA.core.data_searching.get_match import search_muxrays_single_element, search_gammas_single_isotope
from EVA.util.transition_utils import is_primary

logger = logging.getLogger(__name__)

from matplotlib.backend_bases import MouseButton

class PlotAnalysisPresenter(object):
    def __init__(self, view, model):
        super().__init__()
        self.view = view
        self.model = model

        # plot data and connect PlotWidget
        self.view.plot.update_plot(self.model.fig, self.model.axs)
        self.view.plot.canvas.mpl_connect('button_press_event', self.on_plot_clicked)

        # load form data from model
        self.view.mu_xray_search_width_line_edit.setText(str(self.model.mu_xray_search_width))
        self.view.gamma_search_width_line_edit.setText(str(self.model.gamma_search_width))

        self.view.height_line_edit.setText(str(self.model.default_height))
        self.view.threshold_line_edit.setText(str(self.model.default_threshold))
        self.view.distance_line_edit.setText(str(self.model.default_distance))
        self.view.routine_select_combo.addItems(self.model.peakfind_functions)
        self.view.routine_select_combo.setCurrentText(self.model.peakfind_selected_function)

        # set up all connections:
        self.view.mu_xray_search_width_line_edit.textEdited.connect(self.set_mu_xray_search_width)
        self.view.gamma_search_width_line_edit.textEdited.connect(self.set_gamma_search_width)

        # connect cellClicked event for all tables
        self.view.gamma_table.cellClicked.connect(self.on_gamma_table_cell_clicked)
        self.view.muonic_xray_table_all.cellClicked.connect(
            lambda x, y: self.on_muonic_xray_table_cell_clicked(x, y, self.view.muonic_xray_table_all))

        self.view.muonic_xray_table_prim.cellClicked.connect(
            lambda x, y: self.on_muonic_xray_table_cell_clicked(x, y, self.view.muonic_xray_table_prim))

        self.view.muonic_xray_table_sec.cellClicked.connect(
            lambda x, y: self.on_muonic_xray_table_cell_clicked(x, y, self.view.muonic_xray_table_sec))

        # connect line removal tables
        self.view.plotted_gammas_table.cellClicked.connect(self.remove_gamma_line)
        self.view.plotted_mu_xrays_table.cellClicked.connect(self.remove_mu_xray_line)

        self.view.use_default_checkbox.checkStateChanged.connect(self.view.toggle_peak_find_settings)
        self.view.find_peaks_button.clicked.connect(self.start_peak_find)
        self.view.reset_button.clicked.connect(self.reset_peak_find)

        self.view.muon_search_button.clicked.connect(self.search_muonic_xrays)
        self.view.gamma_search_button.clicked.connect(self.search_gammas)

    def search_muonic_xrays(self):
        try:
            element = self.view.muon_search_line_edit.text()
            res = search_muxrays_single_element(element)

            # if no matches
            if len(res) == 0:
                self.view.display_no_match_table(self.view.muonic_xray_table_all)
                self.view.display_no_match_table(self.view.muonic_xray_table_prim)
                self.view.display_no_match_table(self.view.muonic_xray_table_sec)
                return

            pretty_res = [[r["element"], r["energy"], r["transition"], ""] for r in res]
            self.view.muonic_xray_table_all.update_contents(pretty_res)

            prim_res = [[r["element"], r["energy"], r["transition"], ""] for r in res
                        if is_primary(r["transition"], notation="spec")]
            sec_res = [[r["element"], r["energy"], r["transition"], ""] for r in res
                       if not is_primary(r["transition"], notation="spec")]

            if len(prim_res) == 0:
                self.view.display_no_match_table(self.view.muonic_xray_table_prim)
            else:
                self.view.muonic_xray_table_prim.update_contents(prim_res)

            if len(sec_res) == 0:
                self.view.display_no_match_table(self.view.muonic_xray_table_sec)
            else:
                self.view.muonic_xray_table_sec.update_contents(sec_res)

        except (ValueError, AttributeError) as e:
            self.view.display_error_message(message="Invalid data in muonic xray search.")
            raise e


    def search_gammas(self):
        try:
            isotope = self.view.gamma_search_line_edit.text().strip()
            res = search_gammas_single_isotope(isotope)

            # if no matches
            if len(res) == 0:
                self.view.display_no_match_table(self.view.gamma_table)
                return

            pretty_res = [[r["isotope"].strip(), r["energy"], "", r["intensity"], r["lifetime"]] for r in res]
            self.view.gamma_table.update_contents(pretty_res)

        except (ValueError, AttributeError) as e:
            self.view.display_error_message(message="Invalid data in gamma search.")
            raise e

    def set_mu_xray_search_width(self, width):
        try:
            self.model.mu_xray_search_width = float(width)
        except (ValueError, AttributeError):
            self.view.display_error_message(message="Invalid muonic xray search range.")

    def set_gamma_search_width(self, width):
        try:
            self.model.gamma_search_width = float(width)
        except (ValueError, AttributeError):
            self.view.display_error_message(message="Invalid muonic xray search range.")

    def on_plot_clicked(self, event):
        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata
        logger.debug("Figure clicked at (%s, %s).", round(x, 2), round(y, 2))

        # Searching gammas
        if event.button is MouseButton.RIGHT:
            self.view.gamma_table_label.setText(f"Possible Gamma Transitions at {x:.1f} +/- "
                                                                f"{self.model.gamma_search_width}")
            res = self.model.search_gammas(x)

            if not res:
                self.view.display_no_match_table(self.view.gamma_table)
                return

            else:
                res_subset = [[row['isotope'].strip(), row['energy'], row['diff'],
                               row['intensity']*100, row['lifetime']] for row in res]

                self.view.update_table(self.view.gamma_table, res_subset)

        # searching muonic xrays
        if event.button is MouseButton.LEFT:
            self.view.muonic_xray_table_label.setText(f"Possible Muonic X-ray Transitions at {x:.1f} +/- "
                                                                      f"{self.model.mu_xray_search_width}")
            all_res, prim_res, sec_res = self.model.search_mu_xrays(x)

            if not all_res:
                self.view.display_no_match_table(self.view.muonic_xray_table_all)
            else:
                all_res_subset = [[row["element"], float(row["energy"]), row["transition"], row["diff"]] for row in
                                  all_res]
                self.view.update_table(self.view.muonic_xray_table_all, all_res_subset)


            if not prim_res:
                self.view.display_no_match_table(self.view.muonic_xray_table_prim)
            else:
                prim_res_subset = [[row["element"], float(row["energy"]), row["transition"], row["diff"]] for row in
                                   prim_res]
                self.view.update_table(self.view.muonic_xray_table_prim, prim_res_subset)

            if not sec_res:
                self.view.display_no_match_table(self.view.muonic_xray_table_sec)
            else:
                sec_res_subset = [[row["element"], float(row["energy"]), row["transition"], row["diff"]] for row in
                                  sec_res]
                self.view.update_table(self.view.muonic_xray_table_sec, sec_res_subset)

    def on_gamma_table_cell_clicked(self, row, col):
        table = self.view.gamma_table

        element = table.item(row, 0).text()
        energy = table.item(row, 1).text()

        # plot all transitions for the clicked element
        if col == 0:
            name = self.model.plot_vlines_all_gammas(element)

        # plot only one line for the clicked energy
        elif col == 1:
            name = self.model.plot_vlines_single_gammas(element, energy)
        else:
            return

        self.model.update_legend()
        self.view.plot.canvas.draw()

        self.view.update_plotted_lines_table(self.view.plotted_gammas_table, self.model.plotted_gamma_lines)


    def on_muonic_xray_table_cell_clicked(self, row, col, table):
        element = table.item(row, 0).text()
        transition = table.item(row, 2).text()

        # plot all transitions for the clicked element
        if col == 0:
            self.model.plot_vlines_all_mu_xrays(element)

        # plot only one line for the clicked transition or energy
        if col == 1 or col == 2:
            self.model.plot_vlines_single_mu_xrays(element, transition)

        self.model.update_legend()
        self.view.plot.canvas.draw()
        self.view.update_plotted_lines_table(self.view.plotted_mu_xrays_table, self.model.plotted_mu_xray_lines)

    def remove_mu_xray_line(self, row: int, col: int):
        cell_contents = self.view.plotted_mu_xrays_table.item(row, col)
        name = cell_contents.text()
        self.model.remove_mu_xray_line(name)

        self.view.update_plotted_lines_table(self.view.plotted_mu_xrays_table, self.model.plotted_mu_xray_lines)
        self.model.update_legend()
        self.view.plot.canvas.draw()

    def remove_gamma_line(self, row: int, col: int):
        cell_contents = self.view.plotted_gammas_table.item(row, col)
        name = cell_contents.text()
        self.model.remove_gamma_line(name)

        self.view.update_plotted_lines_table(self.view.plotted_gammas_table, self.model.plotted_gamma_lines)
        self.model.update_legend()
        self.view.plot.canvas.draw()

    def start_peak_find(self):
        self.model.remove_plot_markers()
        if not self.view.use_default_checkbox.isChecked():
            try:
                # get form settings if custom settings have been specified
                self.model.default_height = float(self.view.height_line_edit.text())
                self.model.default_threshold = float(self.view.threshold_line_edit.text())
                self.model.default_distance = float(self.view.distance_line_edit.text())
            except (ValueError, AttributeError) as e:
                self.view.display_error_message(message="Invalid peak find settings.")
                return

        self.model.peakfind_selected_function = self.view.routine_select_combo.currentText()
        self.model.find_peaks()

        # update view
        self.view.update_peakfind_tree(self.model.peakfind_result)
        self.view.update_table(self.view.peakfind_results_table, self.model.peakfind_simplified_result)
        self.view.plot.canvas.draw()

    def reset_peak_find(self):
        self.model.remove_plot_markers()
        self.model.peakfind_result = []
        self.model.peakfind_simplified_result = []

        self.view.peakfind_results_tree.clear()
        self.view.peakfind_results_table.setRowCount(0)
        self.view.plot.canvas.draw()
