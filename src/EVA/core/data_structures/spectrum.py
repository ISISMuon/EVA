from copy import deepcopy
from dataclasses import dataclass
import h5py
import numpy as np

@dataclass
class Spectrum:
    """
    The 'Spectrum' dataclass holds the data from a single detector for a single run.
    It holds the name of the detector, associated run number and the x (energy) and
    y (counts) arrays, as well as references to hdf datasets to be loaded on to memory
    as needed.
    Args:
        detector: string, name of detector.
        run_number: string, run number for the spectrum.
        x: numpy array, containing the x-data measured by the detector (histogram bin centers).
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

    def __deepcopy__(self, memo):
        """
        Custom deepcopy implementation that copies detector, run number information
        and x,y histogram arrays, ignoring the hdf dataset references. Work around
        for default deepcopy failing due to hdf datasets not supporting pickling.
        Args:

        Returns:
            Spectrum: A minimal deepcopy of Spectrum object that only contains data points.
        """
        return Spectrum(
            detector=self.detector,
            run_number=self.run_number,
            x=None if self.x is None else self.x.copy(),
            y=None if self.y is None else self.y.copy(),
            bin_range=deepcopy(self.bin_range, memo),
        )
    