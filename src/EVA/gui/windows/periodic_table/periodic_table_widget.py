# imports
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QTreeWidgetItem, QTableWidgetItem, QMessageBox, QHeaderView
from functools import partial

from EVA.core.app import get_app, get_config
from EVA.core.data_searching.get_match import search_muxrays, search_muxrays_all_isotopes, search_gammas, search_e_xrays
from EVA.gui.ui_files.periodic_table import Ui_MainWindow
from EVA.util.transition_utils import to_iupac
from EVA.core.data_searching import get_match

# lists
elements = ["H", "He", 
            "Li", "Be", "B", "C", "N", "O", "F", "Ne", 
            "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", 
            "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
            "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
            "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn",
            "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
            ]

elements_disable = ["H", "Kr", "Xe", "Tc", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", 
                    "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og", "Pm", "Pa", "U", "Np", "Pu", "Am",
                    "Cm", "Bk", "Cf", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"]


# class definitions
class PeriodicTableWidget(QMainWindow, Ui_MainWindow):
    window_closed_s = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Periodic Table - EVA")

        # disable buttons for some of the elements for which no muonic X-ray data exist
        for element in elements_disable:
            button = getattr(self, f"{element}_button", None)
            button.setEnabled(False)
            button.setStyleSheet("QPushButton {background-color: transparent}")

        # signal when a button in the periodic table is pressed
        for element in elements:
            button = getattr(self, f"{element}_button", None)
            button.pressed.connect(partial(self.open_element, element))

        # signal when the print button in the "Muonic X-ray search" group box is pressed
        self.print_button.pressed.connect(self.energy_search)

        # the first tab, for muonic X-rays, is set to active when the GUI opens
        self.tabWidget.setCurrentIndex(0)

    def open_element(self, element):
        mu_db = get_app().muon_database

        info = mu_db["Infos"][element]
        isotopes = mu_db["Isotope names"][element]
        abundancies = mu_db["Abundancies"][element]

        self.element_info_text.setPlainText(info)
        self.element_info_text.setReadOnly(True)

        self.element_info_muonic_xray_tree.clear()

        mu_xray_items = []
        for i, isotope_name in enumerate(isotopes):
            isotope_item = QTreeWidgetItem([isotope_name])

            abundancy_item = QTreeWidgetItem()
            abundancy_item.setText(0, "Abundancy")
            abundancy_item.setText(1, abundancies[isotope_name])
            isotope_item.addChild(abundancy_item)

            primary_item = QTreeWidgetItem()
            primary_item.setText(0, "Primary")
            isotope_item.addChild(primary_item)

            secondary_item = QTreeWidgetItem()
            secondary_item.setText(0, "Secondary")
            isotope_item.addChild(secondary_item)

            matches = get_match.search_muxrays_single_element_all_isotopes(isotope_name)

            # sort primary and secondary matches
            prims = [key for key in mu_db["All isotopes"]["Primary energies"][isotope_name].keys()]

            for match in matches:
                match_item = QTreeWidgetItem()
                match_item.setText(1, match["transition"])
                match_item.setText(3, to_iupac(match["transition"]))
                match_item.setText(2, str(round(match["energy"], 4)))

                if match["transition"] in prims:
                    primary_item.addChild(match_item)
                else:
                    secondary_item.addChild(match_item)

            primary_item.setExpanded(True)
            secondary_item.setExpanded(True)
            mu_xray_items.append(isotope_item)

        self.element_info_muonic_xray_tree.insertTopLevelItems(0, mu_xray_items)

        # lastly, resize all columns
        self.element_info_muonic_xray_tree.resizeColumnToContents(0)
        self.element_info_muonic_xray_tree.resizeColumnToContents(1)
        self.element_info_muonic_xray_tree.resizeColumnToContents(2)
        self.element_info_muonic_xray_tree.resizeColumnToContents(3)
        self.element_info_muonic_xray_tree.resizeColumnToContents(4)

        # updating gamma tree
        gamma_data = get_app().gamma_database[element]
        self.treeWidget_2.clear()

        gamma_items = []
        isotopes = []
        isotope_items = []

        for i, gammas in enumerate(gamma_data):
            isotope = gammas[0]

            if isotope not in isotopes:
                isotopes.append(isotope)
                isotope_items.append(QTreeWidgetItem([isotope]))

            match_item = QTreeWidgetItem()
            match_item.setText(1, str(round(float(gammas[1]), 6)))
            match_item.setText(2, str(round(float(gammas[2]), 6)))

            isotope_items[-1].addChild(match_item)

        self.treeWidget_2.insertTopLevelItems(0, isotope_items)

        # Update electronic xray table
        e_xray_data = get_app().e_xray_database[element]
        self.element_info_electronic_xray_table.setRowCount(len(e_xray_data))

        for i, data in enumerate(e_xray_data.items()):
            self.element_info_electronic_xray_table.setItem(i, 0, QTableWidgetItem(data[0]))
            self.element_info_electronic_xray_table.setItem(i, 1, QTableWidgetItem(data[1]))

        self.element_info_electronic_xray_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.element_info_electronic_xray_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def energy_search(self):
        try:
            energy = float(self.energy_input.text())
            error = float(self.uncertainty_input.text())
        except (AttributeError, ValueError):
            _ = QMessageBox.critical(self, "Search error", "Invalid input in energy search.",
                                       QMessageBox.StandardButton.Ok)
            return

        # display mu-xray results
        if self.search_isotopes_checkbox.isChecked():
            muon_res, _, _ = search_muxrays_all_isotopes([[energy, error]])
        else:
            muon_res, _, _ = search_muxrays([[energy, error]])

        # Only get results that are within the search width (get_match will get matches within
        # 1x error, 2x error and 3x error)
        filtered_muon_res = [res for res in muon_res if res["error"] == error]

        if not len(filtered_muon_res):
            self.mu_xray_search_result_table.setRowCount(1)
            self.mu_xray_search_result_table.setItem(0, 0, QTableWidgetItem("No matches."))
            self.mu_xray_search_result_table.setItem(0, 1, QTableWidgetItem())
            self.mu_xray_search_result_table.setItem(0, 2, QTableWidgetItem())
            self.mu_xray_search_result_table.setItem(0, 3, QTableWidgetItem())
            self.mu_xray_search_result_table.setItem(0, 4, QTableWidgetItem())
        else:
            self.mu_xray_search_result_table.setRowCount(len(filtered_muon_res))

            for i, r in enumerate(filtered_muon_res):
                self.mu_xray_search_result_table.setItem(i, 0, QTableWidgetItem(str(r["element"])))
                self.mu_xray_search_result_table.setItem(i, 1, QTableWidgetItem(str(round(float(r["energy"]), 6))))
                self.mu_xray_search_result_table.setItem(i, 2, QTableWidgetItem(str(r["transition"])))
                self.mu_xray_search_result_table.setItem(i, 3, QTableWidgetItem(to_iupac(str(r["transition"]))))
                self.mu_xray_search_result_table.setItem(i, 4, QTableWidgetItem(str(abs(round(r["diff"], 6)))))

        self.mu_xray_search_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mu_xray_search_result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mu_xray_search_result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.mu_xray_search_result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.mu_xray_search_result_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        # display gamma results
        gamma_res = search_gammas([[energy, error]])
        filtered_gammas = [res for res in gamma_res
                           if res["intensity"] >= float(get_config()["database"]["gamma_intensity_threshold"])]

        if not len(filtered_gammas):
            self.gamma_search_result_table.setRowCount(1)
            self.gamma_search_result_table.setItem(0, 0, QTableWidgetItem("No matches."))
            self.gamma_search_result_table.setItem(0, 1, QTableWidgetItem())
            self.gamma_search_result_table.setItem(0, 2, QTableWidgetItem())
            self.gamma_search_result_table.setItem(0, 3, QTableWidgetItem())
        else:
            self.gamma_search_result_table.setRowCount(len(filtered_gammas))

            for i, r in enumerate(filtered_gammas):
                if r["intensity"] < 20:
                    continue

                self.gamma_search_result_table.setItem(i, 0, QTableWidgetItem(str(r["isotope"])))
                self.gamma_search_result_table.setItem(i, 1, QTableWidgetItem(str(round(r["energy"], 6))))
                self.gamma_search_result_table.setItem(i, 2, QTableWidgetItem(str(round((float(r["intensity"])), 6))))
                self.gamma_search_result_table.setItem(i, 3, QTableWidgetItem(str(abs(round(r["diff"], 6)))))

        self.gamma_search_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.gamma_search_result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.gamma_search_result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.gamma_search_result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # display e-xray results
        e_xray_res = search_e_xrays([(energy, error)])

        if not len(e_xray_res):
            self.e_xray_search_result_table.setRowCount(1)
            self.e_xray_search_result_table.setItem(0, 0, QTableWidgetItem("No matches."))
            self.e_xray_search_result_table.setItem(0, 1, QTableWidgetItem())
            self.e_xray_search_result_table.setItem(0, 2, QTableWidgetItem())
            self.e_xray_search_result_table.setItem(0, 3, QTableWidgetItem())
        else:
            self.e_xray_search_result_table.setRowCount(len(e_xray_res))

            for i, r in enumerate(e_xray_res):
                self.e_xray_search_result_table.setItem(i, 0, QTableWidgetItem(r["element"]))
                self.e_xray_search_result_table.setItem(i, 1, QTableWidgetItem(str(round(r["energy"], 6))))
                self.e_xray_search_result_table.setItem(i, 2, QTableWidgetItem(r["transition"]))
                self.e_xray_search_result_table.setItem(i, 3, QTableWidgetItem(str(abs(round(r["diff"], 6)))))

        self.e_xray_search_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.e_xray_search_result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.e_xray_search_result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.e_xray_search_result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        """ Previous method using the .dat files and custom search
        
        energy_min = int(self.energy_input.text()) - int(self.uncertainty_input.text())
        energy_max = int(self.energy_input.text()) + int(self.uncertainty_input.text())
        self.x_ray_search.insertPlainText(f"Searching for all values in between the energies {energy_min} and {energy_max} keV:\n")
        
        energy_list = range(energy_min, energy_max)
        separator = "\\.|"
        energy_pattern = separator.join(str(x) for x in energy_list)+"\\."
        filelist = glob.glob("elements/*.dat")
        for i in filelist:
            with open(i, "r", encoding = "utf8") as fp:
                for line in fp:
                    if re.match(energy_pattern, line):
                        self.x_ray_search.insertPlainText(line)
        """

    def closeEvent(self, event):
        self.window_closed_s.emit(event)
        event.accept()
