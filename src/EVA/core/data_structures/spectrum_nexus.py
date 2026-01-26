from dataclasses import dataclass
import h5py
import numpy as np


@dataclass
class SpectrumNexus:
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
