from dataclasses import dataclass
import h5py
import numpy as np

@dataclass
class Spectrum:
    """
    The 'Spectrum' dataclass holds the data from a single detector for a single run.

    Args:
        detector: string, name of detector.
        run_number: string, run number for the spectrum.
        x: numpy array, containing the x-data measured by the detector (histogram bins).
        y: numpy array, containing y-data measured by the detector (counts per bin).
    """

    detector: str
    run_number: str
    x: np.ndarray = None
    y: np.ndarray = None
    time: h5py.Dataset = None
    energy: h5py.Dataset = None
    prompt_energy: h5py.Dataset = None
    prompt_count: h5py.Dataset = None
    delayed_energy: h5py.Dataset = None
    delayed_count: h5py.Dataset = None
    ibex_hist_2d: h5py.Dataset = None
    manual_hist_2d: h5py.Dataset = None
    cut_data: h5py.Dataset = None
    bin_range: list = None
    efficiency_hist_counts: h5py.Dataset = None
    efficiency_hist_energy: h5py.Dataset = None


    