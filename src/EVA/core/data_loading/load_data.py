import numpy as np
import os
import h5py
from EVA.core.data_structures.run import Run
from EVA.core.data_structures.spectrum import Spectrum
from EVA.core.settings.config import Config

def load_comment(run_num: str, file_path: str) -> tuple[list[str], int]:
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
        fd = open(file_path + '/comment.dat', 'r')
        #commenttext = open(globals.workingdirectory + '/comment.dat', 'r').readlines()
        commenttext = fd.readlines()

        search_str = 'Run ' + run_num
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
    except IOError:
        rtn_str = [" ", " ", " ", " "]
        flag = 1

    return rtn_str, flag

def load_run(run_num: str, working_directory: str, energy_corrections: dict,
             normalisation: str, binning: int) -> tuple[Run, dict]:
    """
    Loads the specified run by searching for the run in the working directory.
    Creates Spectrum objects to store data from each detector.
    Calls load_comment() to get run info and stores metadata and lists of Spectrum objects (for each detector)
    in a Run object.
    Calls normalise() and energy_correction() to normalise the data and stores the normalised data under run.data.

    Args:
        run_num: run number to load for
        config: Config object

    Returns:
        Returns a tuple containing the Run object and a dict containing error status, with keys ``no_files_found``,
        ``comment_not_found``, ``norm_by_spills_error``
    """

    channels = {
        "GE1": "2099",
        "GE2": "3099",
        "GE3": "4099",
        "GE4": "5099"
    }

    # Load metadata from comment
    comment_data, comment_flag = load_comment(run_num, working_directory)

    raw = {}
    detectors = []

    none_loaded_flag = 1

    for detector, channel in channels.items():
        filename = f"{working_directory}/ral0{run_num}.rooth{channel}.dat"
        try:
            # Store data read from file in a Spectrum object
            xdata, ydata = np.loadtxt(filename, delimiter=" ", unpack=True)
            spectrum = Spectrum(detector=detector, run_number=run_num, x=xdata, y=ydata)

            raw[detector] = spectrum # Add Spectrum to list of spectra
            detectors.append(detector) # Add detector name to list of detectors

            none_loaded_flag = 0 # data was found - lowering flag

        except FileNotFoundError:
            # Append empty arrays to spectrum if data file is not found for the given detector.
            # This maintains a consistent detector order in the list
            raw[detector] = Spectrum(detector=detector, run_number=run_num, x=np.array([]), y=np.array([]))

    # Add everything into a Run object
    run = Run(raw=raw, loaded_detectors=detectors, run_num=str(run_num), start_time=comment_data[0],
              end_time=comment_data[1], events_str=comment_data[2], comment=comment_data[3])

    try:
        # Apply corrections
        run.set_corrections(energy_corrections, normalise_which=None,
                            normalisation=normalisation, bin_rate=binning)
        norm_flag = 0

    except ValueError:
        norm_flag = 1 # value error is raised if normalisation fails

    # Assemble flag dictionary to return error status
    flags = {
        "no_files_found": none_loaded_flag,
        "comment_not_found": comment_flag,
        "norm_by_spills_error": norm_flag
    }

    return run, flags


def open_hex_file(run_num: int, channels: list, base_path: str, max_digits: int = 10):
    for digits in range(len(str(run_num)), max_digits + 1):
        filename = f"{channels[0]}_{run_num:0{digits}d}_{channels[1]}.nxs"
        file_path = os.path.join(base_path, filename)
        file_path = os.path.normpath(file_path)
        if os.path.exists(file_path):
            return h5py.File(file_path, 'r')
    # If loop finishes without returning, raise an error
    raise FileNotFoundError(f"No file found for run number {run_num} in {base_path}")


def load_run_nxs(run_num: str, working_directory: str, energy_corrections: dict,
             normalisation: str, binning: int, plot_mode: str) -> tuple[Run, dict]:
    """
    Loads the specified run by searching for the run in the working directory.
    Creates Spectrum objects to store data from each detector.
    Calls load_comment() to get run info and stores metadata and lists of Spectrum objects (for each detector)
    in a Run object.
    Calls normalise() and energy_correction() to normalise the data and stores the normalised data under run.data.

    Args:
        run_num: run number to load for
        config: Config object

    Returns:
        Returns a tuple containing the Run object and a dict containing error status, with keys ``no_files_found``,
        ``comment_not_found``, ``norm_by_spills_error``
    """

    channels = {
        "GE1": ["hex0", "ch0"],
        "GE2": ["hex0", "ch1"],
        "GE3": ["hex1", "ch0"],
        "GE4": ["hex1", "ch1"],
    }

    # Load metadata from comment
    comment_data, comment_flag = load_comment(run_num, working_directory)

    raw = {}
    detectors = []

    none_loaded_flag = 1

    for detector, channel in channels.items():
        try:
            # Store data read from file in a Spectrum object
            data_file = open_hex_file(run_num=int(run_num), channels=channel, base_path=working_directory)
            count_data = data_file['/raw_data_1/detector_1_events/event_energy'][:]
            tdata = data_file['/raw_data_1/detector_1_events/event_time_offset'][:]

            a = 0.3208
            b = -0.2267
            a = 0.0653
            b = -1.2143
            count_data = count_data * a + b
            """
            mask = (tdata > 0) & (tdata < 2000)
            count_data = count_data[mask]
            a = 0.3208
            b = -0.2267
            count_data = count_data * a + b
            counts, bin_edges = np.histogram(count_data, bins=2000)

            # Bin centers = average of consecutive edges
            bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

            # Assign to x, y
            xdata = bin_centers
            ydata = counts
            """
            spectrum = Spectrum(detector=detector, run_number=run_num, x=count_data, y=None, t =tdata)

            raw[detector] = spectrum # Add Spectrum to list of spectra
            detectors.append(detector) # Add detector name to list of detectors

            none_loaded_flag = 0 # data was found - lowering flag

        except FileNotFoundError:
            # Append empty arrays to spectrum if data file is not found for the given detector.
            # This maintains a consistent detector order in the list
            raw[detector] = Spectrum(detector=detector, run_number=run_num, x=np.array([]), y=np.array([]))

    # Add everything into a Run object
    run = Run(raw=raw, loaded_detectors=detectors, run_num=str(run_num), start_time=comment_data[0],
              end_time=comment_data[1], events_str=comment_data[2], comment=comment_data[3], plot_mode=plot_mode, prompt_limit=2000)
    
    try:
        # Apply corrections
        run.set_corrections(energy_corrections, normalise_which=None,
                            normalisation=normalisation, bin_rate=binning, plot_mode=plot_mode, prompt_limit=2000)
        norm_flag = 0

    except ValueError:
        norm_flag = 1 # value error is raised if normalisation fails

    # Assemble flag dictionary to return error status
    flags = {
        "no_files_found": none_loaded_flag,
        "comment_not_found": comment_flag,
        "norm_by_spills_error": norm_flag
    }

    return run, flags
