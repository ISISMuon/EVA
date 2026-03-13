import logging
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from PyQt6.QtCore import QObject, pyqtSignal
from EVA.core.data_structures.spectrum import Spectrum
from EVA.core.physics import rebin
from EVA.core.physics.normalisation import normalise_events, normalise_counts

logger = logging.getLogger(__name__)

normalisation_types = ("none", "counts", "events")


class MetaQObjectABC(type(QObject), ABCMeta):
    """Metaclass combining QObject and ABC compatibility."""

    pass


class Run(QObject, metaclass=MetaQObjectABC):
    """
    Abstract base class for experiment runs.
    Provides shared logic and enforces a consistent interface for RunNexus and RunBiriani.
    """

    corrections_updated_s = pyqtSignal()

    def __init__(
        self,
        raw: dict[Spectrum],
        loaded_detectors: list[str],
        run_num: str,
        momentum: float,
    ):
        super().__init__()
        self._raw = raw
        self.loaded_detectors = loaded_detectors
        self.run_num = run_num

        # Common correction parameters
        self.momentum = momentum
        self.energy_corrections = {}
        self.normalisation = None
        self.normalise_which = loaded_detectors
        self.bin_rate = 1
        self.default_bin = 8192  # subclasses may override
        self.bin_method = ""  # subclass must set

    # =================================================================
    # ABSTRACT INTERFACE
    # =================================================================

    @abstractmethod
    def set_corrections(self, *args, **kwargs):
        """Reapply all corrections, normalisation, and binning in correct order."""
        pass

    @abstractmethod
    def read_comment_data(self):
        """Return formatted metadata (comment, start time, end time, etc.)."""
        pass

    @abstractmethod
    def _set_normalisation_events(self, normalise_which: list[str]):
        """Normalise by events (logic differs per run type)."""
        pass

    @abstractmethod
    def _set_mode(self, *args, **kwargs):
        """Set data depending on plot mode (IBEX/Manual/etc.)."""
        pass

    # Shared functions
    def _set_energy_correction(self, energy_corrections: dict):
        """Apply per-detector linear energy corrections."""
        if energy_corrections is None:
            energy_corrections = self.energy_corrections

        for detector, spectrum in self.data.items():
            try:
                if energy_corrections[detector]["use_e_corr"]:
                    gradient, offset = energy_corrections[detector]["e_corr_coeffs"]
                    self.data[detector].x = self.data[detector].x * gradient + offset
            except KeyError:
                logger.warning(
                    f"No energy correction information found for detector {detector}. Automatically skipping correction."
                )
        self.energy_corrections = energy_corrections

    def _set_normalisation(
        self, normalisation: str, normalise_which: list[str] | None = None
    ):
        """Dispatch to the correct normalisation method."""
        if normalise_which is None:
            normalise_which = self.normalise_which

        if normalisation is None:
            normalisation = self.normalisation

        if normalisation == "counts":
            self._set_normalisation_counts(normalise_which)
        elif normalisation == "events":
            self._set_normalisation_events(normalise_which)
        elif normalisation == "none":
            self._set_normalisation_none()
        else:
            raise TypeError(f"Invalid normalisation type: '{normalisation}'")

    def _set_normalisation_none(self):
        """Reset all normalisation."""
        for detector in self._raw.keys():
            self.data[detector].y = self.data[detector].y
        self.normalisation = "none"
        self.normalise_which = self.loaded_detectors

    def _set_normalisation_counts(self, normalise_which: list[str]):
        """Normalise detector spectra by total counts."""
        for detector, spectrum in self._raw.items():
            if detector in normalise_which:
                self.data[detector].y = normalise_counts(spectrum.y)
            else:
                self.data[detector].y = self.data[detector].y
        self.normalisation = "counts"
        self.normalise_which = normalise_which

    def _set_binning(
        self, binning_rate: float | None = None, default_bin: int | None = None
    ):
        """Dispatch to the appropriate binning method."""
        if self.bin_method == "prebinned":
            self._set_binning_prebinned(binning_rate)
        elif self.bin_method == "raw":
            self._set_binning_raw(binning_rate, default_bin)
        elif self.bin_method == "hist":
            pass
        else:
            raise ValueError(f"Invalid binning method '{self.bin_method}'.")

    def _set_binning_prebinned(self, binning_rate: float | None = None):
        """Rebin pre-binned histogram data."""
        if binning_rate is None:
            binning_rate = self.bin_rate
        else:
            self.bin_rate = binning_rate

        if binning_rate == 1.0:
            self.bin_rate = 1.0
            return

        for detector, spectrum in self._raw.items():
            if self.data[detector].x.size == 0:
                continue
            self.data[detector].x, self.data[detector].y = rebin.numpy_rebin(
                self.data[detector].x,
                self.data[detector].y,
                self.bin_rate,
                self._raw[detector].bin_range,
            )

    def _set_binning_raw(
        self, binning_rate: float | None = None, default_bin: int | None = None
    ):
        """Rebin unbinned (event) data."""
        if binning_rate is None:
            binning_rate = self.bin_rate
        else:
            self.bin_rate = binning_rate

        if default_bin is None:
            default_bin = self.default_bin
        else:
            self.default_bin = default_bin

        bin_num = int(default_bin / binning_rate)
        for detector, spectrum in self._raw.items():
            if getattr(spectrum, "energy", None) is None or spectrum.energy.size == 0:
                continue
            else:
                spectrum.x, spectrum.y = rebin.nxs_rebin(
                    spectrum.cut_data, bin_num, bin_range=spectrum.bin_range
                )
                self.data[detector].x, self.data[detector].y = spectrum.x, spectrum.y

    # Utility methods
    def is_empty(self) -> bool:
        """Return True if all detectors have no data."""
        return all([spectrum.x.size == 0 for spectrum in self._raw.values()])

    def get_nonzero_data(self) -> list[Spectrum]:
        """Return list of non-empty Spectrum objects."""
        return [spectrum for spectrum in self.data.values() if spectrum.x.size != 0]

    def get_raw(self) -> dict[Spectrum]:
        """Return a deep copy of raw data."""
        return deepcopy(self._raw)
