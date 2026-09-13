import re

import numpy as np
import os
import h5py
from EVA.core.data_structures.run import Run
from EVA.core.data_structures.run_nxs import RunNexus
from EVA.core.data_structures.run_brni import RunBiriani
from EVA.core.data_structures.run_combined import MultiRun
from EVA.core.data_structures.spectrum import Spectrum

from EVA.core.app import get_config


def load_run(
    run_num: str,
    data_directory: str,
    energy_corrections: dict,
    normalisation: str,
    binning: int,
    plot_mode: str,
    prompt_limit: int,
    delayed_limit: int,
) -> tuple[Run, dict]:
    """ Attempts to load specified run as both Biriani and Nexus run files 
    and returns whichever is found along with erorr flags. Throws file not found error if neither/both found.

    Args:
        run_num (str): run number to read for
        data_directory (str): _description_
        energy_corrections (dict): _description_
        normalisation (str): _description_
        binning (int): _description_
        plot_mode (str): _description_
        prompt_limit (int): _description_
        delayed_limit (int): _description_

    Returns:
        tuple[Run, dict]: _description_
    """
    brni_run, brni_flags = load_run_brni(
        run_num=run_num, data_directory=data_directory, energy_corrections=energy_corrections, normalisation=normalisation, binning=binning
    )
    nxs_run, nxs_flags = load_run_nxs(
        run_num=run_num,
        data_directory=data_directory,
        energy_corrections=energy_corrections,
        normalisation=normalisation,
        binning=binning,
        plot_mode=plot_mode,
        prompt_limit=prompt_limit,
        delayed_limit=delayed_limit,
    )
    # Check if brni and/or nxs run(s) were loaded and handle accordingly
    if brni_flags["no_files_found"] == 1 and nxs_flags["no_files_found"] == 1:
        return brni_run, {
            "no_files_found": 1
        }  # an empty brni run is returned to update the MainWindow
    if brni_flags["no_files_found"] == 0 and nxs_flags["no_files_found"] == 0:
        return brni_run, {"duplicate_files_found": 1}

    elif brni_flags["no_files_found"] == 0:
        return brni_run, brni_flags
    else:
        return nxs_run, nxs_flags

def load_run_multi(
    run_nums: str,
    data_directory: str,
    energy_corrections: dict,
    normalisation: str,
    binning: int,
    plot_mode: str,
    prompt_limit: int,
    delayed_limit: int,
) -> tuple[Run, dict]:
    flags = {
        "no_files_found": 1,
        "comment_not_found": 1,
        "norm_by_spills_error": 0,
    }
    run_num_list = [r.strip() for r in run_nums.split(",")]
    all_run_array = []
    good_run_array = []
    good_flag_array = []
    for run_num in run_num_list:
        run, run_flag = load_run(
            run_num,
            data_directory,
            energy_corrections,
            normalisation,
            binning,
            plot_mode,
            prompt_limit,
            delayed_limit,
        )
        all_run_array.append(run)
        if run_flag["no_files_found"] == 0:
            good_run_array.append(run)
            good_flag_array.append(run_flag)

    if len(good_run_array) > 0:
        flags["no_files_found"] = 0
        combined_run = MultiRun(good_run_array)
        try:
            # Apply corrections
            combined_run.set_corrections(
                energy_corrections=energy_corrections,
                normalise_which=None,
                normalisation=normalisation,
                bin_rate=binning,
                plot_mode=plot_mode,
                prompt_limit=prompt_limit,
                delayed_limit=delayed_limit,
            )
            flags["norm_by_spills_error"] = 0
        except ValueError:
            flags["norm_by_spills_error"] = 1 # value error is raised if normalisation fails
        if all(
            good_flag.get("comment_not_found") == 0 for good_flag in good_flag_array
        ):
            flags["comment_not_found"] = 0
        if any(
            good_flag.get("norm_by_spills_error") == 1
            for good_flag in good_flag_array
        ):
            flags["norm_by_spills_error"] = 1
        return combined_run, flags
    else:
        return 0, flags

############## BIRIANI RUN FILE FORMAT #####################


def load_comment_brni(run_num: str, file_path: str) -> tuple[list[str], int]:
    """
    Loads data from comment.dat at specified path.

    Args:
        run_num: run number to read for
        file_path: path to comment file

    Returns:
        Returns a list containing [start time, end time, number of events, full comment str] and an integer success flag.
        If no data was found, the list will be equal to ``[" ", " ", " ", " "]``.

    """
    try:
        with open(file_path + "/Comment.dat", "r") as fd:
            # commenttext = open(globals.workingdirectory + '/comment.dat', 'r').readlines()
            commenttext = fd.readlines()

            search_str = "Run " + run_num
            flag = 1
            index = 0
            for line in commenttext:
                index += 1
                if search_str in line:
                    flag = 0
                    break
            if flag == 1:
                rtn_str = [" ", " ", " ", " "]
            else:
                starttime_str = commenttext[index]
                endtime_str = commenttext[index + 1]
                events_str = commenttext[index + 2]
                comment_str = commenttext[index + 4]
                rtn_str = [starttime_str, endtime_str, events_str, comment_str]
                fd.close()
    except OSError:
        rtn_str = [" ", " ", " ", " "]
        flag = 1

    return rtn_str, flag


def load_run_brni(
    run_num: str,
    data_directory: str,
    energy_corrections: dict,
    normalisation: str,
    binning: int,
) -> tuple[Run, dict]:
    """
    Loads the specified run by searching for the run in the working directory.
    Creates Spectrum objects to store data from each detector.
    Calls load_comment() to get run info and stores metadata and lists of Spectrum objects (for each detector)
    in a Run object.
    Calls normalise() and energy_correction() to normalise the data and stores the normalised data under run.data.

    Args:
        run_num: run number to load for
        data_directory: Folder where run file is to be searched for
        Run corrections

    Returns:
        Returns a tuple containing the Run object and a dict containing error status, with keys ``no_files_found``,
        ``comment_not_found``, ``norm_by_spills_error``
    """

    channels = {"GE1": "2099", "GE2": "3099", "GE3": "4099", "GE4": "5099"}

    # Load metadata from comment
    comment_data, comment_flag = load_comment_brni(run_num, data_directory)

    raw = {}
    detectors = []

    none_loaded_flag = 1
    encoding = get_config()["general"]["encoding"]
    for detector, channel in channels.items():
        filename = f"{data_directory}/ral0{run_num}.rooth{channel}.dat"
        try:
            # Attempt to load data from file using selected encoding, raises UnicodeDecodeError if encoding is incorrect
            # Which main presenter handles.
            xdata, ydata = np.loadtxt(filename, delimiter=" ", unpack=True, encoding=encoding)
            # Store data read from file in a Spectrum object
            spectrum = Spectrum(detector=detector, run_number=run_num, x=xdata, y=ydata)

            raw[detector] = spectrum  # Add Spectrum to list of spectra
            detectors.append(detector)  # Add detector name to list of detectors

            none_loaded_flag = 0  # data was found - lowering flag

        except FileNotFoundError:
            # Append empty arrays to spectrum if data file is not found for the given detector.
            # This maintains a consistent detector order in the list
            raw[detector] = Spectrum(
                detector=detector, run_number=run_num, x=np.array([]), y=np.array([])
            )

    # Add everything into a Run object
    run = RunBiriani(
        raw=raw,
        loaded_detectors=detectors,
        run_num=str(run_num),
        comment_data=comment_data,
        momentum=-1,
    )

    try:
        # Apply corrections
        run.set_corrections(
            energy_corrections=energy_corrections,
            normalise_which=None,
            normalisation=normalisation,
            bin_rate=binning,
        )
        norm_flag = 0

    except ValueError:
        norm_flag = 1  # value error is raised if normalisation fails

    # Assemble flag dictionary to return error status
    flags = {
        "no_files_found": none_loaded_flag,
        "comment_not_found": comment_flag,
        "norm_by_spills_error": norm_flag,
    }

    return run, flags


############## NEXUS RUN FILE FORMAT #####################

def get_detector_indices(data_file: h5py.File) -> list[int]:
    """Finds detector channels present in the Nexus file by looking up subfolders in the pattern detector_X_energyA where X is a whole number."""
    pattern = re.compile(r"^detector_(\d+)_energyA$")
    indices = []
    for key in data_file.keys():
        match = pattern.match(key)
        if match:
            indices.append(int(match.group(1)))
    return sorted(indices)

def load_comment_nxs(input_file: h5py.File) -> tuple[list[str], int]:
    """
    Loads data from the appropriate comment subfolders in run file

    Args:
        input_file: HDF run file with comment metadata

    Returns:
        Returns a list containing [title, num prompt events, num delayed events, start time, end time, IBEX time cut for prompt, IBEX time cut for delayed] and an integer success flag.
        If no data was found, the list will be equal to ``[" ", " ", " ", " "]``.

    """
    try:
        encoding = get_config()["general"]["encoding"]
        title = input_file['title'][()].decode(encoding)
        title += ": " + input_file['notes'][()].decode(encoding)
        start_time = input_file['start_time'][()].decode(encoding)
        end_time = input_file['end_time'][()].decode(encoding)
        num_prompt_events = 0
        num_delayed_events = 0
        detector_channels = get_detector_indices(input_file)

        for i in detector_channels:
            num_prompt_events += input_file[
                f"detector_{i}_energyA/num_events"
            ][()]
            num_delayed_events += input_file[
                f"detector_{i}_energyB/num_events"
            ][()]
            try:  # Failsafe for now as not sure if all four channels will always record time
                key_Amin = f"detector_{i}_energyA/event_time_min"
                key_Amax = f"detector_{i}_energyA/event_time_max"
                prompt_time = (
                    f"{input_file[key_Amin][()]} - {input_file[key_Amax][()]} ns"
                )
                key_Bmin = f"detector_{i}_energyB/event_time_min"
                key_Bmax = f"detector_{i}_energyB/event_time_max"
                delayed_time = (
                    f"{input_file[key_Bmin][()]} - {input_file[key_Bmax][()]} ns"
                )
            except KeyError:
                pass
        comment_flag = 0
        rtn_str = [
            title,
            str(num_prompt_events),
            str(num_delayed_events),
            start_time,
            end_time,
            prompt_time,
            delayed_time,
        ]

    except IOError:
        rtn_str = [" ", " ", " ", " ", " ", " ", " "]
        comment_flag = 1
    return rtn_str, comment_flag


def open_hex_file(run_num: int, base_path: str, max_digits: int = 10) -> h5py.File:
    """Detect and open .nxs file for given run number

    Args:
        run_num (int): truncated run number with zeroes removed
        base_path (str): base folder where run file is searched for
        max_digits (int, optional): number of leading zeros to check for. Defaults to 10.

    Raises:
        FileNotFoundError: If run file is not in current folder.

    Returns:
        h5py.File: returns a raw_data_1 File object of the loaded HDF run file.
    """
    for digits in range(len(str(run_num)), max_digits + 1):
        filename = f"MUX{run_num:0{digits}d}.nxs"  # e.g. hex0_000123_ch0.nxs
        file_path = os.path.join(base_path, filename)
        file_path = os.path.normpath(file_path)
        if os.path.exists(file_path):
            file = h5py.File(file_path, "r")
            return file["raw_data_1"]
    # If loop finishes without returning, raise an error
    raise FileNotFoundError(f"No file found for run number {run_num} in {base_path}")


def generate_spectrum_nxs(run_number, data_file) -> dict[str:Spectrum]:
    """Build a Spectrum object for each detector channel in Nexus file using references to raw and pre-binned data.
    Skips over detectors with missing data for now, eventually will handle missing detectors more gracefully TODO.
    Combines detector name and Spectrum objects into a dict.
    Args:
        run_number (str): Store a string of the loaded run's number for individual access in peakfit
        data_file (h5py.File): HDF file to load detector data from 

    Returns:
        dict[str: Spectrum]: a dictionary of detector names : all data sets in run file for associated detector.
    """
    raw = {}
    detectors = []
    none_loaded_flag = 1
    encoding = get_config()["general"]["encoding"]
    detector_channels = get_detector_indices(data_file)

    for i in detector_channels:
        check_loaded_cond_1 = f"detector_{i}_energyA/counts"
        check_loaded_cond_2 = f"detector_{i}_energyHist/energy"
        try:
            if (
                data_file[check_loaded_cond_1][()].any()
                or data_file[check_loaded_cond_2][()].any()
            ):
                detector_name = data_file[f'instrument/detector_{i}/name'][()].decode(encoding)
                
                prompt_energy = data_file[f"detector_{i}_energyA/energy"]
                prompt_count = data_file[f"detector_{i}_energyA/counts"]

                delayed_energy = data_file[f"detector_{i}_energyB/energy"]
                delayed_count = data_file[f"detector_{i}_energyB/counts"]

                energy = data_file[f"detector_{i}_events/event_energy"]
                time = data_file[f"detector_{i}_events/event_time_offset"]

                try:
                    efficiency_hist_energy = data_file[
                        f"detector_{i}_energyHist/energy"
                    ]
                    efficiency_hist_counts = data_file[
                        f"detector_{i}_energyHist/counts"
                    ]
                except KeyError:
                    efficiency_hist_energy = None
                    efficiency_hist_counts = None

                ibex_hist_2d = data_file[f"detector_{i}_energy2D/counts"]
                bin_width_lower_limit = delayed_energy[1] - delayed_energy[0]
                bin_width_upper_limit = delayed_energy[-1] - delayed_energy[-2]

                bin_range = (np.min(delayed_energy) - bin_width_lower_limit, np.max(delayed_energy) - bin_width_upper_limit)

                spectrum = Spectrum(
                    detector=detector_name,
                    run_number=run_number,
                    prompt_count=prompt_count,
                    prompt_energy=prompt_energy,
                    delayed_count=delayed_count,
                    delayed_energy=delayed_energy,
                    energy=energy,
                    time=time,
                    ibex_hist_2d=ibex_hist_2d,
                    bin_range=bin_range,
                    efficiency_hist_energy=efficiency_hist_energy,
                    efficiency_hist_counts=efficiency_hist_counts,
                )
                raw[detector_name] = spectrum
                detectors.append(detector_name)
                none_loaded_flag = 0

        except KeyError:
            pass
    try:
        momentum = data_file["/selog/Momentum/value"][()][0]

    except KeyError:
        momentum = -100
    return detectors, raw, momentum, none_loaded_flag


def load_run_nxs(
    run_num: str,
    data_directory: str,
    energy_corrections: dict,
    normalisation: str,
    binning: int,
    plot_mode: str,
    prompt_limit: int,
    delayed_limit: int,
) -> tuple[Run, dict]:
    """
    Loads the specified run by searching for the run in the working directory.
    Creates Spectrum objects to store data from each detector.
    Calls load_comment() to get run info and stores metadata and lists of Spectrum objects (for each detector)
    in a Run object.
    Calls saved run corrections on run data

    Args:
        run_num: run number to load for
        data_directory: Folder where run file is to be searched for
        Run corrections

    Returns:
        Returns a tuple containing the Run object and a dict containing error status, with keys ``no_files_found``,
        ``comment_not_found``, ``norm_by_spills_error``
    """
    try:
        data_file = open_hex_file(int(run_num), data_directory)
        comment_data, comment_flag = load_comment_nxs(data_file)
        detectors, raw, momentum, none_loaded_flag = generate_spectrum_nxs(
            run_num, data_file
        )

        run = RunNexus(
            raw=raw,
            loaded_detectors=detectors,
            run_num=str(run_num),
            comment_data=comment_data,
            plot_mode=plot_mode,
            prompt_limit=prompt_limit,
            delayed_limit=delayed_limit,
            momentum=momentum,
        )
        try:
            # Apply corrections
            run.set_corrections(
                energy_corrections=energy_corrections,
                normalise_which=None,
                normalisation=normalisation,
                bin_rate=binning,
                plot_mode=plot_mode,
                prompt_limit=prompt_limit,
                delayed_limit=delayed_limit,
            )
            norm_flag = 0

        except ValueError:
            norm_flag = 1  # value error is raised if normalisation fails

        # Assemble flag dictionary to return error status
        flags = {
            "no_files_found": none_loaded_flag,
            "comment_not_found": comment_flag,
            "norm_by_spills_error": norm_flag,
        }

        return run, flags

    except FileNotFoundError:
        run = RunNexus.empty()
        return run, {"no_files_found": 1}
