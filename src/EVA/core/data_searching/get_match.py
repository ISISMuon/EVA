import math
import logging
import time
from EVA.core.app import get_app

logger = logging.getLogger(__name__)


def search_gammas_single_transition(isotope: str, energy: str) -> list[dict]:
    """
    Searches in the gamma database for all transitions within 0.5% of specified energy for a given isotope.

    Args:
        isotope: which isotope to search for
        energy: energy to search for

    Returns:
        List of dictionaries, one for each match, with keys
            * **isotope** (str)

            * **energy** (float)

            * **intensity** (str)

            * **lifetime** (str)
    """
    gammas = list(get_app().gamma_database.values())
    all_matches = []
    i = 1
    while i < len(gammas)-1:
        i += 1
        for j in range(len(gammas[i])):
            raw_data = gammas[i][j]

            if isotope == raw_data[0].strip():
                raw_data_kev = raw_data[1]
                sigma = 0.005 * raw_data_kev

                if raw_data_kev - sigma < float(energy) < raw_data_kev + sigma:
                    data = {
                        'isotope': raw_data[0],
                        'energy': raw_data_kev,
                        'intensity': raw_data[2],
                        'lifetime':  raw_data[3]
                    }

                    all_matches.append(data)
    return all_matches

def search_gammas_single_isotope(isotope: str) -> list[dict]:
    """
    Retrieves all gamma transitions available in the gamma database for specified isotope.

    Args:
        isotope: which isotope to search for

    Returns:
        List of dictionaries, one for each match, with keys

        * **isotope** (str)

        * **energy** (float)

        * **intensity** (str)

        * **lifetime** (str)

    """
    gammas = list(get_app().gamma_database.values())

    all_matches = []
    i = 1
    while i < len(gammas)-1:
        i += 1
        for j in range(len(gammas[i])):
            raw_data = gammas[i][j]

            if str(isotope) == raw_data[0].strip():
                raw_data_kev=float(raw_data[1])
                data = {
                    "isotope": raw_data[0],
                    "energy": raw_data_kev,
                    "intensity": raw_data[2],
                    "lifetime": raw_data[3]
                }

                all_matches.append(data)

    return all_matches

def search_muxrays_single_transition(input_element: str, input_trans: str) -> list[dict]:
    """
    Searches in muonic xray database for all peaks specified for a single transition. When using the Mudirac database,
    there will always be only one database entry per transition. However, the legacy database can sometimes contain
    multiple entries for a single transition. Hence, this function returns a list of dictionaries rather than a single.

    Args:
        input_element: which element to search for
        input_trans: name of transition to search for (in spectroscopic notation e.g. (2p3/2->1s1/2))

    Returns:
        List of dictionaries, one for each match, with keys

        * **element** (str)

        * **energy** (float)

        * **transition** (str)
    """

    app = get_app()

    matches = []
    raw_data = app.muon_database["All energies"]

    for element in raw_data:
        if element == input_element:
            for transition, transition_data in raw_data[element].items():
                if transition == input_trans:
                    data = {
                        "element": element,
                        "energy": transition_data["E"],
                        "transition": transition
                    }
                    matches.append(data)

    return matches

def search_muxrays_single_element(input_element: str) -> list[dict]:
    """
    Fetches all transitions available in the muonic x-ray database for specified element.

    Args:
        input_element: which element to search for

    Returns:
        List of dictionaries, one for each match, with keys

        * **element** (str)

        * **energy** (float)

        * **transition** (str)
    """
    app = get_app()
    matches = []

    raw_data = app.muon_database["All energies"]
    for element in raw_data:
        if element == input_element:
            for transition, transition_data in raw_data[element].items():
                data = {
                    "element": element,
                    "energy": transition_data["E"],
                    "transition": transition
                }
                matches.append(data)

    return matches

def search_muxrays_single_element_all_isotopes(input_element: str) -> list[dict]:
    """
    Fetches all transitions available in the muonic x-ray database for all isotopes of the specified element.

    Args:
        input_element: which element to search for

    Returns:
        List of dictionaries, one for each match, with keys

        * **element** (str)

        * **energy** (float)

        * **transition** (str)
    """
    app = get_app()
    matches = []

    raw_data = app.muon_database["All isotopes"]["All energies"]
    for element in raw_data:
        if element == input_element:
            for transition, transition_data in raw_data[element].items():
                data = {
                    "element": element,
                    "energy": transition_data["E"],
                    "transition": transition
                }
                matches.append(data)

    return matches

def search_muxrays(input_peaks: list[list[float]]) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Searches for possible muonic xray transitions in the database at multiple energies at once.

    NOTE: This function searches within an error range of 3x search width. if you'd only like energies within your
    search width, you will have to filter out matches outside the search width using the "error" key in the results.

    Args:
        input_peaks: List of [search energy, search width] search parameters.

    Returns:
        Tuple of results, where index 0 contains all matches, index 1 primary matches only, and index 2 secondary
        matches only. The elements in the tuples are lists of dictionaries.

        Dictionary keys

        * **element**: the element which was searched for

        * **energy**: the energy which was searched for

        * **error**: the error range used to search within (takes values of 1x search width, 2x search width or 3x search width)

        * **peak_centre**: energy of transition matched in database

        * **transition**: name of transition matched in database

        * **diff**: difference between searched energy and match (how close the match is)
    """
    start_time = time.time_ns()
    app = get_app()
    peak_data = app.muon_database

    primary_matches = []
    secondary_matches = []
    all_matches = []
    prims = []

    raw_data = peak_data["All energies"]
    for peak, sigma in input_peaks:
        for element in raw_data:
            for transition, transition_data in raw_data[element].items():
                energy = transition_data["E"]
                diff = abs(peak - energy)

                if diff <= 3*sigma:
                    data = {
                        "element": element,
                        "energy": energy,
                        "error": math.ceil(diff/sigma) * sigma,
                        "peak_centre": peak,
                        "transition": transition,
                        "diff": diff
                    }

                    all_matches.append(data)

            prims = [peak[0] for peak in peak_data["Primary energies"][element].items()]

    all_matches = sorted(all_matches, key=lambda o: o['diff'])

    for match in all_matches:
        if match["transition"] in prims:
            primary_matches.append(match)
        else:
            secondary_matches.append(match)

    end_time = time.time_ns()
    logger.debug(f"Found matches in {(end_time - start_time) / 1e9} s.")

    return all_matches, primary_matches, secondary_matches

def search_muxrays_all_isotopes(input_peaks: list[list[float]]) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Searches for possible muonic xray transitions for all isotopes in the database at multiple energies at once.

    NOTE: This function searches within an error range of 3x search width. if you'd only like energies within your
    search width, you will have to filter out matches outside the search width using the "error" key in the results.

    Args:
        input_peaks: List of [search energy, search width] search parameters.

    Returns:
        Tuple of results, where index 0 contains all matches, index 1 primary matches only, and index 2 secondary
        matches only. The elements in the tuples are lists of dictionaries.

        Dictionary keys

        * **element**: the element which was searched for

        * **energy**: the energy which was searched for

        * **error**: the error range used to search within (takes values of 1x search width, 2x search width or 3x search width)

        * **peak_centre**: energy of transition matched in database

        * **transition**: name of transition matched in database

        * **diff**: difference between searched energy and match (how close the match is)
    """
    start_time = time.time_ns()
    app = get_app()
    peak_data = app.muon_database

    primary_matches = []
    secondary_matches = []
    all_matches = []
    prims = []

    raw_data = peak_data["All isotopes"]["All energies"]
    for peak, sigma in input_peaks:
        for element in raw_data:
            for transition, transition_data in raw_data[element].items():
                energy = transition_data["E"]
                diff = abs(peak - energy)

                if diff <= 3*sigma:
                    data = {
                        "element": element,
                        "energy": energy,
                        "error": math.ceil(diff/sigma) * sigma,
                        "peak_centre": peak,
                        "transition": transition,
                        "diff": diff
                    }

                    all_matches.append(data)

            prims = [peak[0] for peak in peak_data["All isotopes"]["Primary energies"][element].items()]

    all_matches = sorted(all_matches, key=lambda o: o['diff'])

    for match in all_matches:
        if match["transition"] in prims:
            primary_matches.append(match)
        else:
            secondary_matches.append(match)

    end_time = time.time_ns()
    logger.debug(f"Found matches in {(end_time - start_time) / 1e9} s.")

    return all_matches, primary_matches, secondary_matches

def search_gammas(input_peaks: list[list[float]]) -> list[dict]:
    """
    Searches for possible gamma transitions in the database at multiple energies at once.

    Args:
        input_peaks: list of [search energy, search width] search parameters.

    Returns:
        List of dictionaries containing matches with keys

        * **isotope**: the isotope which was searched for.

        * **energy**:  energy of transition matched in database.

        * **diff**: difference between searched energy and match (how close the match is).

        * **lifetime**: lifetime of transition

        * **intensity**: intensity of transition.
    """
    all_matches = []
    gammas = list(get_app().gamma_database.values())

    i = 1
    while i < len(gammas)-1:
        i += 1
        #print('i=',i)
        for j in range(len(gammas[i])):

            raw_data = gammas[i][j]
            #print('raw_data', raw_data)
            for peak, sigma in input_peaks:
                raw_data_kev=float(raw_data[1])

                if (raw_data_kev - sigma) <= peak <= (raw_data_kev + sigma):
                 #print('in print', peak, sigma, raw_data)
                    data = {
                        "isotope": raw_data[0],
                        "energy": raw_data_kev,
                        "diff": peak - float(raw_data_kev),
                        "intensity": raw_data[2],
                        "lifetime": raw_data[3]
                    }

                    all_matches.append(data)

    all_matches.sort(key = lambda x: abs(x['diff']))

    return all_matches

def search_e_xrays(values: list[tuple[float, float]]) -> list[dict]:
    """
    Searches in the electronic xray database given a list of search energies and widths.
    Args:
        values: list of tuples containing (search energy, search width)

    Returns:
        List of dictionaries, one for each match. dict keys are:

            * **element**: element name.

            * **transition**: transition name.

            * **energy**:  energy of transition matched in database.

            * **diff**: difference between searched energy and match (how close the match is).

    """
    results = []

    for element, element_data in get_app().e_xray_database.items():
        for transition, energy in element_data.items():
            energy = float(energy)
            for search_energy, search_width in values:
                if (energy - search_width) <= search_energy <= (energy + search_width):
                    results.append({
                        "element": element,
                        "transition": transition,
                        "energy": energy,
                        "diff": search_energy - energy
                    })

    results.sort(key=lambda x: abs(x['diff']))

    return results


