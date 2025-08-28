from dataclasses import dataclass
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
    x: np.ndarray
    y: np.ndarray
    t: np.ndarray
