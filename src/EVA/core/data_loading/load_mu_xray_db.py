import json
from EVA.util.path_handler import get_path

def load_mudirac_data():
    with open(get_path("src/EVA/databases/muonic_xrays/mudirac_data_estimated_intensities.json"), 'r') as read_file:

        data = json.load(read_file)

        primary_energies_all_isotopes = {}
        secondary_energies_all_isotopes = {}
        all_energies_all_isotopes = {}

        primary_energies_default_isotope = {}
        secondary_energies_default_isotope = {}
        all_energies_default_isotope = {}

        z_numbers = {}
        capture_ratios = {}
        abundancies = {}
        infos = {}
        isotope_names = {}

        # sort data
        for element, element_data in data.items():
            default_isotope = element_data["Default"]
            z_numbers[element] = element_data["Z"]
            capture_prob = element_data["Capture ratio"].split("+-")
            capture_ratios[element] = {"Value": float(capture_prob[0]), "Error": float(capture_prob[1])}
            abundancies[element] = {}
            infos[element] = element_data["Info"]
            isotope_names[element] = list(element_data["Isotopes"].keys())

            for isotope, isotope_data in element_data["Isotopes"].items():
                primary_energy = isotope_data["Primary"]
                secondary_energy = isotope_data["Secondary"]
                abundancies[element][isotope] = isotope_data["Abundancy"]

                # Insert isotope data into dictionaries
                primary_energies_all_isotopes[isotope] = primary_energy
                secondary_energies_all_isotopes[isotope] = secondary_energy
                all_energies_all_isotopes[isotope] = dict(**primary_energy, **secondary_energy)

                # If isotope is the default isotope into a separate set of dictionaries
                if isotope == default_isotope:
                    primary_energies_default_isotope[element] = primary_energy
                    secondary_energies_default_isotope[element] = secondary_energy
                    all_energies_default_isotope[element] = dict(**primary_energy, **secondary_energy)

        # Default to using only most abundant isotope
        peak_data = {
            "Primary energies": primary_energies_default_isotope,
            "Secondary energies": secondary_energies_default_isotope,
            "All energies": all_energies_default_isotope,
            "Atomic numbers": z_numbers,
            "Capture ratios": capture_ratios,
            "Infos": infos,
            "Isotope names": isotope_names,
            "Abundancies": abundancies,
            "All isotopes": {
                "Primary energies": primary_energies_all_isotopes,
                "Secondary energies": secondary_energies_all_isotopes,
                "All energies": all_energies_all_isotopes
            }
        }

    read_file.close()
    return peak_data

def load_extended_mudirac_data():
    with open(get_path("src/EVA/databases/muonic_xrays/mudirac_data_extended_missing_intensities_unindented.json"), 'r') as read_file:

        data = json.load(read_file)

        primary_energies_all_isotopes = {}
        secondary_energies_all_isotopes = {}
        all_energies_all_isotopes = {}

        primary_energies_default_isotope = {}
        secondary_energies_default_isotope = {}
        all_energies_default_isotope = {}

        z_numbers = {}
        capture_ratios = {}
        abundancies = {}
        infos = {}
        isotope_names = {}

        # sort data
        for element, element_data in data.items():
            default_isotope = element_data["Default"]
            z_numbers[element] = element_data["Z"]
            capture_prob = element_data["Capture ratio"].split("+-")
            capture_ratios[element] = {"Value": float(capture_prob[0]), "Error": float(capture_prob[1])}
            abundancies[element] = {}
            infos[element] = element_data["Info"]
            isotope_names[element] = list(element_data["Isotopes"].keys())

            for isotope, isotope_data in element_data["Isotopes"].items():
                primary_energy = isotope_data["Primary"]
                secondary_energy = isotope_data["Secondary"]
                abundancies[element][isotope] = isotope_data["Abundancy"]

                # Insert isotope data into dictionaries
                primary_energies_all_isotopes[isotope] = primary_energy
                secondary_energies_all_isotopes[isotope] = secondary_energy
                all_energies_all_isotopes[isotope] = dict(**primary_energy, **secondary_energy)

                # If isotope is the default isotope into a separate set of dictionaries
                if isotope == default_isotope:
                    primary_energies_default_isotope[element] = primary_energy
                    secondary_energies_default_isotope[element] = secondary_energy
                    all_energies_default_isotope[element] = dict(**primary_energy, **secondary_energy)

        # Default to using only most abundant isotope
        peak_data = {
            "Primary energies": primary_energies_default_isotope,
            "Secondary energies": secondary_energies_default_isotope,
            "All energies": all_energies_default_isotope,
            "Atomic numbers": z_numbers,
            "Capture ratios": capture_ratios,
            "Infos": infos,
            "Isotope names": isotope_names,
            "Abundancies": abundancies,
            "All isotopes": {
                "Primary energies": primary_energies_all_isotopes,
                "Secondary energies": secondary_energies_all_isotopes,
                "All energies": all_energies_all_isotopes
            }
        }

    read_file.close()
    return peak_data

def load_legacy_data():

    legacy_db_path = get_path('src/EVA/databases/muonic_xrays/peak_data.json')
    with open(legacy_db_path, 'r') as read_file:
        data = json.load(read_file)

        all_energies = {}

        primary_energies = {}
        secondary_energies = {}

        # sort data
        for element, element_data in data.items():
            primary_energies[element] = {}
            secondary_energies[element] = {}

            for transition, transition_data in element_data["Primary"].items():
                primary_energies[element][transition] = {
                    "E": float(transition_data),
                    "I": 1
                }

            for transition, transition_data in element_data["Secondary"].items():
                secondary_energies[element][transition] = {
                    "E": float(transition_data),
                    "I": 1
                }

            all_energies[element] = dict(primary_energies[element], **secondary_energies[element])

        peak_data = {
            "Primary energies": primary_energies,
            "Secondary energies": secondary_energies,
            "All energies": all_energies
        }

    read_file.close()
    return peak_data

"""
def load_databaseFile():
    if globals.muon_database == "legacy":
        with open('./src/EVA/databases/muonic_xrays/peak_data.json', 'r') as read_file:
            print('decoding file')
            globals.peakdata = json.load(read_file)
            primary_energies = {}
            secondary_energies = {}
            all_energies = {}
            # sort data
            for element in globals.peakdata:
                primary_energy = [float(x[1]) for x in list(globals.peakdata[element]['Primary'].items())]
                secondary_energy = [float(x[1]) for x in list(globals.peakdata[element]['Secondary'].items())]
                primary_trans = [x[0] for x in list(globals.peakdata[element]['Primary'].items())]
                secondary_trans = [x[0] for x in list(globals.peakdata[element]['Secondary'].items())]

                primary_energies[element] = dict(zip(primary_trans, primary_energy))
                secondary_energies[element] = dict(zip(secondary_trans, secondary_energy))
                all_energies[element] = dict(zip(primary_trans + secondary_trans,
                                                 primary_energy + secondary_energy))
            globals.peak_data['Primary energy'] = primary_energies
            globals.peak_data['Secondary energy'] = secondary_energies
            globals.peak_data['All energies'] = all_energies

        return

    elif globals.muon_database == "mudirac":
        with open('./src/EVA/databases/muonic_xrays/mudirac_data.json', 'r') as read_file:
            print('decoding file')
            peakdata = json.load(read_file)
            primary_energies = {}
            secondary_energies = {}
            all_energies = {}

            # sort data
            for element in peakdata:
                for isotope in peakdata[element]["Isotopes"]:
                    primary_energy = {}
                    secondary_energy = {}
                    for p_trans in peakdata[element]["Isotopes"][isotope]["Primary"]:
                        primary_energy[p_trans] = peakdata[element]["Isotopes"][isotope]["Primary"][p_trans]["E"]

                    for s_trans in peakdata[element]["Isotopes"][isotope]["Secondary"]:
                        secondary_energy[s_trans] = peakdata[element]["Isotopes"][isotope]["Secondary"][s_trans]["E"]

                    primary_energies[isotope] = primary_energy
                    secondary_energies[isotope] = secondary_energy
                    all_energies[isotope] = dict(primary_energy, **secondary_energy)

            globals.peak_data['Primary energy'] = primary_energies
            globals.peak_data['Secondary energy'] = secondary_energies
            globals.peak_data['All energies'] = all_energies
"""