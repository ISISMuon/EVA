import json


def load_gamma_test_db():
    pass


def load_mudirac_test_db():
    with open("test_data/test_databases/mudirac_test_data.json", "r") as read_file:
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

        # sort data
        for element, element_data in data.items():
            default_isotope = element_data["Default"]
            z_numbers[element] = element_data["Z"]
            capture_ratios[element] = element_data["Capture_Prob"]
            abundancies[element] = {}

            for isotope, isotope_data in element_data["Isotopes"].items():
                primary_energy = isotope_data["Primary"]
                secondary_energy = isotope_data["Secondary"]
                abundancies[element][isotope] = isotope_data["Abundancy"]

                # Insert isotope data into dictionaries
                primary_energies_all_isotopes[isotope] = primary_energy
                secondary_energies_all_isotopes[isotope] = secondary_energy
                all_energies_all_isotopes[isotope] = dict(
                    **primary_energy, **secondary_energy
                )

                # If isotope is the default isotope into a separate set of dictionaries
                if isotope == default_isotope:
                    primary_energies_default_isotope[element] = primary_energy
                    secondary_energies_default_isotope[element] = secondary_energy
                    all_energies_default_isotope[element] = dict(
                        **primary_energy, **secondary_energy
                    )

        # Default to using only most abundant isotope
        peak_data = {
            "Primary energies": primary_energies_default_isotope,
            "Secondary energies": secondary_energies_default_isotope,
            "All energies": all_energies_default_isotope,
            "Z-numbers": z_numbers,
            "Capture ratios": capture_ratios,
            "Abundancies": abundancies,
            "All isotopes": {
                "Primary energies": primary_energies_all_isotopes,
                "Secondary energies": secondary_energies_all_isotopes,
                "All energies": all_energies_all_isotopes,
            },
        }

    read_file.close()

    return peak_data


def load_legacy_test_db():
    with open("test_data/test_databases/legacy_test_data.json", "r") as read_file:
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
                    "I": 1,
                }

            for transition, transition_data in element_data["Secondary"].items():
                secondary_energies[element][transition] = {
                    "E": float(transition_data),
                    "I": 1,
                }

            all_energies[element] = dict(
                primary_energies[element], **secondary_energies[element]
            )

        peak_data = {
            "Primary energies": primary_energies,
            "Secondary energies": secondary_energies,
            "All energies": all_energies,
        }

    read_file.close()
    return peak_data
