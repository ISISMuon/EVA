from dataclasses import dataclass
import numpy as np
from EVA.core.data_structures.spectrum_nexus import SpectrumNexus

# @dataclass
# class Spectrum:
#     """
#     The 'Spectrum' dataclass holds the data from a single detector for a single run.

#     Args:
#         detector: string, name of detector.
#         run_number: string, run number for the spectrum.
#         x: numpy array, containing the x-data measured by the detector (histogram bins).
#         y: numpy array, containing y-data measured by the detector (counts per bin).
#     """
#     detector: str
#     run_number: str
#     x: np.ndarray = None
#     y: np.ndarray = None
#     time: np.ndarray = None
#     energy: np.ndarray = None
#     prompt_energy: np.ndarray = None
#     prompt_count: np.ndarray = None
#     delayed_energy: np.ndarray = None
#     delayed_count: np.ndarray = None
#     ibex_hist_2d: np.ndarray = None
#     manual_hist_2d: np.ndarray = None
#     cut_data: np.ndarray = None
#     bin_range: list = None


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

    detector: str = None
    run_number: str = None
    x: np.ndarray = None
    y: np.ndarray = None
    bin_range: list = None
