import numpy as np
import os
import h5py
from EVA.core.data_structures.run import Run
from EVA.core.data_structures.run_nxs import RunNexus
from EVA.core.data_structures.run_brni import RunBiriani
from EVA.core.data_structures.spectrum import Spectrum
from EVA.core.data_structures.spectrum_nexus import SpectrumNexus

from EVA.core.app import get_config

def load_run(run_num: str, working_directory: str,
            energy_corrections: dict, normalisation: str, binning: int, plot_mode: str, prompt_limit: int) -> tuple[Run, dict]:
    """
    Attempts to load specified run as both Biriani and Nexus run files and returns whichever is found. Throws error if neither/both found."""
    brni_run, brni_flags = load_run_brni(run_num, working_directory, energy_corrections, normalisation, binning)
    nxs_run, nxs_flags = load_run_nxs(run_num, working_directory, energy_corrections, normalisation, binning, plot_mode, prompt_limit)
    if brni_flags["no_files_found"] == 1 and nxs_flags["no_files_found"] == 1:
        return 0, {"no_files_found": 1}
    if brni_flags["no_files_found"] == 0 and nxs_flags["no_files_found"] == 0:
        return 0, {"duplicate_files_found": 1}

    elif brni_flags["no_files_found"] == 0:
        return brni_run, brni_flags
    else:
        return nxs_run, nxs_flags

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

def load_run_brni(run_num: str, working_directory: str, energy_corrections: dict,
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
    comment_data, comment_flag = load_comment_brni(run_num, working_directory)

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
    run = RunBiriani(raw=raw, loaded_detectors=detectors, run_num=str(run_num), comment_data=comment_data, momentum=0)

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

###################################

def load_comment_nxs(input_file: h5py.File) -> tuple[list[str], int]:
    """
    Loads and formats comment data from metadata in Nexus file."""
    try:
        title = input_file['raw_data_1/title'][()].decode('utf-8')
        title += ": " + input_file['raw_data_1/notes'][()].decode('utf-8')
        start_time = input_file['raw_data_1/start_time'][()].decode('utf-8')
        end_time = input_file['raw_data_1/end_time'][()].decode('utf-8')
        num_prompt_events = 0
        num_delayed_events = 0
        for i in range(1,5):
            num_prompt_events += input_file[f"raw_data_1/detector_{i}_energyA/num_events"][()]
            num_delayed_events += input_file[f"raw_data_1/detector_{i}_energyB/num_events"][()]
            try: # Failsafe for now as not sure if all four channels will always record time
                key_Amin = f"raw_data_1/detector_{i}_energyA/event_time_min"
                key_Amax = f"raw_data_1/detector_{i}_energyA/event_time_max"
                prompt_time = f"{input_file[key_Amin][()]} - {input_file[key_Amax][()]} ns"
                key_Bmin = f"raw_data_1/detector_{i}_energyB/event_time_min"
                key_Bmax = f"raw_data_1/detector_{i}_energyB/event_time_max"
                delayed_time = f"{input_file[key_Bmin][()]} - {input_file[key_Bmax][()]} ns"
            except KeyError:
                pass
        comment_flag = 0
        rtn_str = [title, str(num_prompt_events), str(num_delayed_events), start_time, end_time, prompt_time, delayed_time]

    except IOError: 
        rtn_str = [" ", " ", " ", " ", " ", " ", " "]
        comment_flag = 1
    return rtn_str, comment_flag

def open_hex_file(run_num: int, base_path: str, max_digits: int = 10):
    """ Detect and open .nxs file for given run number"""
    for digits in range(len(str(run_num)), max_digits + 1):
        filename = f"MUX{run_num:0{digits}d}.nxs" # e.g. hex0_000123_ch0.nxs
        file_path = os.path.join(base_path, filename)
        file_path = os.path.normpath(file_path)
        if os.path.exists(file_path):
            return h5py.File(file_path, 'r')
        
    # If loop finishes without returning, raise an error
    raise FileNotFoundError(f"No file found for run number {run_num} in {base_path}")


def generate_spectrum_nxs(run_number, data_file):
    """ Build a SpectrumNexus object for each detector channel in Nexus file using references to raw and pre-binned data.
    Skips over detectors with missing data for now, eventually will handle missing detectors more gracefully TODO."""
    raw = {}
    detectors = []
    none_loaded_flag = 1
    config = get_config()

    for i in range(1,5):
        check_loaded = f"raw_data_1/detector_{i}_energyA/counts"
        try:
            if data_file[check_loaded][()].any():
                detector_name = data_file[f'raw_data_1/instrument/detector_{i}/name'][()].decode('utf-8')
                
                prompt_energy = data_file[f"raw_data_1/detector_{i}_energyA/energy"]
                prompt_count = data_file[f"raw_data_1/detector_{i}_energyA/counts"]

                delayed_energy = data_file[f"raw_data_1/detector_{i}_energyB/energy"]
                delayed_count = data_file[f"raw_data_1/detector_{i}_energyB/counts"]

                energy = data_file[f"raw_data_1/detector_{i}_events/event_energy"]
                time = data_file[f"raw_data_1/detector_{i}_events/event_time_offset"]

                ibex_hist_2d = data_file[f"raw_data_1/detector_{i}_energy2D/counts"]
                bin_range = (np.min(delayed_energy), np.max(delayed_energy))
            
                spectrum = SpectrumNexus(detector=detector_name, run_number=run_number, prompt_count=prompt_count,
                                prompt_energy=prompt_energy, delayed_count=delayed_count, delayed_energy=delayed_energy, 
                                energy=energy, time=time, ibex_hist_2d=ibex_hist_2d, bin_range=bin_range)
                raw[detector_name] = spectrum
                detectors.append(detector_name)
                none_loaded_flag = 0
    
        except KeyError:
            pass
    try:
        momentum = data_file['/raw_data_1/selog/Momentum/value'][()][0]
    
    except KeyError:
        momentum = -100
    return detectors, raw, momentum, none_loaded_flag


def load_run_nxs(run_num: str, working_directory: str,
            energy_corrections: dict, normalisation: str, binning: int, plot_mode: str, prompt_limit: int) -> tuple[Run, dict]:
    """ Loads nexus run file from given run number, collects data from each channel into dictionary of SpectrumNexus objects, stores in RunNexus object
    along with run metadata, and apply any detected corrections from saved settings in config."""
    try:
        data_file = open_hex_file(int(run_num), working_directory)
        comment_data, comment_flag = load_comment_nxs(data_file)
        detectors, raw, momentum, none_loaded_flag = generate_spectrum_nxs(run_num, data_file)

        run = RunNexus(raw=raw, loaded_detectors=detectors, run_num=str(run_num), comment_data=comment_data,
                    plot_mode=plot_mode, prompt_limit=prompt_limit, momentum= momentum)
        try:
            # Apply corrections
            run.set_corrections(energy_corrections, normalise_which=None,
                                normalisation=normalisation, bin_rate=binning, plot_mode=plot_mode, prompt_limit=prompt_limit)
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
    
    except FileNotFoundError:
        run = RunNexus.empty()
        return run, {"no_files_found": 1}