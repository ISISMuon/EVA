from copy import deepcopy

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from EVA.core.data_structures.spectrum import Spectrum
from EVA.core.physics import rebin
from EVA.core.physics.normalisation import normalise_events, normalise_counts

normalisation_types = ("none", "counts", "events")

class Run(QObject):
    corrections_updated_s = pyqtSignal()

    """
    The Run class specifies the experiment data and context for all detectors during a single measurement run.

   Args:
       raw: List of Spectrum objects, one Spectrum for each detector. The list may
       contain empty Spectrum objects if no data was found for a detector.
       loaded_detectors: Names of all detectors for which data was successfully loaded.
       run_num: Run number.
       start_time: Time run was started.
       end_time: Time run was ended.
       events_str: Number of events registered.
       comment: All metadata available for the run.
       """
    def __init__(self, raw : dict[Spectrum], loaded_detectors : list[str], run_num: str, start_time: str, end_time: str,
                 events_str: str, comment: str):
        super().__init__()

        # Main data containers
        self._raw = raw # raw, unprocessed data as read from file - is NOT to be changed
        self.data = deepcopy(raw) # copy of raw which can be modified and accessed outside the class

        # Basic run info
        self.loaded_detectors = loaded_detectors
        self.run_num = run_num

        # Normalisation and energy correction info
        self.normalisation = None
        self.normalise_which = loaded_detectors # currently normalising all detectors
        self.bin_rate = 1

        # energy corrections
        self.energy_corrections = {}

        # Metadata from comment file (may not be available)
        self.start_time = start_time
        self.end_time = end_time
        self.events_str = events_str
        self.comment = comment

    def set_corrections(self, energy_corrections: dict[dict] | None = None,
                        normalisation: str | None = None, normalise_which: list[str] | None = None, bin_rate: float | None = None):
        """
        Reapplies all normalisation, corrections and binning specified for the data. Order here is important, and so
        to be safe, any time any form of correction is wanted, everything should be re-calculated. This could become
        inefficient if many more complicated processing methods are implemented, so another approach could be
        considered here in the future.

        The order of
        processing is:
            * energy calibrations / corrections
            * normalisation
            * binning
        """

        if normalise_which is None:
            normalise_which = self.normalise_which

        self.data = deepcopy(self._raw)

        self._set_energy_correction(energy_corrections)
        self._set_normalisation(normalisation, normalise_which)
        self._set_binning(bin_rate)

        # emit a signal to let program know the run has changed
        self.corrections_updated_s.emit()

    # dispatcher method to set normalisation type from string
    def _set_normalisation(self, normalisation: str, normalise_which: list[str] | None = None):
        """
        Sets normalisation to ``data``.

        Args:
            normalisation: name of desired normalisation method. Valid options: "none", "counts", "spills".
            normalise_which: Which detectors to set normalisation for. If normalisation type is set to "none", all
            detectors will be affected.

        Raises:
            TypeError: when invalid normalisation type is specified.
        """
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
            raise TypeError(f"Normalisation type '{normalisation}' is not valid.")

    def _set_normalisation_none(self):
        """
        Resets all normalisation applied for each detector.
        """
        for detector in self._raw.keys():
            self.data[detector].y = self.data[detector].y

        self.normalisation = "none"
        self.normalise_which = self.loaded_detectors

    def _set_normalisation_counts(self, normalise_which: list[str]):
        """
        Sets normalisation by counts for each detector specified.

        Args:
            normalise_which: Names of which detectors to apply normalisation by counts for.
        """
        for detector, spectrum in self._raw.items():
            # Apply normalisation to specified spectra
            if detector in normalise_which:
                self.data[detector].y = normalise_counts(spectrum.y)
            else:
                self.data[detector].y = self.data[detector].y

        # Update the normalisation status
        self.normalisation = "counts"
        self.normalise_which = normalise_which

    def _set_normalisation_events(self, normalise_which: list[str]):
        """
        Sets normalisation by events for each detector specified.

        Args:
            normalise_which: Names of which detectors to apply normalisation by events for.
        """
        try:
            spills = int(self.events_str[19:])
            for detector, spectrum in self._raw.items():
                # Apply normalisation to specified spectra
                if detector in self.normalise_which:
                    self.data[detector].y = normalise_events(spectrum.y, spills)
                else:
                    self.data[detector].y = self.data[detector].y

            # Update the normalisation status
            self.normalisation = "events"
            self.normalise_which = normalise_which

        except ValueError:
            # If spills data is not available, revert normalisation to none
            for detector, spectrum in self._raw.items():
                self.data[detector].y = self.data[detector].y

            # set normalisation status to "none"
            self.normalisation = "none"
            self.normalise_which = self.loaded_detectors
            raise ValueError("Normalisation by events failed.")

    def _set_energy_correction(self, energy_corrections: dict):
        """
        Sets current energy correction.

        Args:
            energy_corrections: Dict of containing energy correction parameters (gradient, offset) for each detector.
        """

        if energy_corrections is None:
            energy_corrections = self.energy_corrections

        # Iterate through each Spectrum in the run and apply energy correction if the detector is in e_corr_which
        for detector, spectrum in self.data.items():
            if energy_corrections[detector]["use_e_corr"]:
                gradient, offset = energy_corrections[detector]["e_corr_coeffs"]

                self.data[detector].x = self.data[detector].x * gradient + offset # store energy correction in data

        self.energy_corrections = energy_corrections

    def _set_binning(self, binning_rate: float | None = None):
        if binning_rate is None:
            binning_rate = self.bin_rate
        else:
           self.bin_rate = binning_rate

        # avoid weird glitches
        if binning_rate == 1.0:
            self.bin_rate = 1.0
            return

        for detector, spectrum in self._raw.items():
            if self.data[detector].x.size == 0:
                print("continued")
                continue
            print("binning")
            self.data[detector].x, self.data[detector].y = rebin.numpy_rebin(self.data[detector].x,
                                                                                   self.data[detector].y, binning_rate)

    def is_empty(self) -> bool:
        """
        Returns: Boolean indicating whether any data was loaded or not.
        """
        return all([spectrum.x.size == 0 for spectrum in self._raw])

    def get_nonzero_data(self) -> list[Spectrum]:
        """
        Returns: Copy of ``data`` without empty Spectrum objects for missing detectors.
        """
        return [spectrum for spectrum in self.data.values() if spectrum.x.size != 0]

    def get_raw(self) -> dict[Spectrum]:
        """
        Returns: Copy of ``raw``.
        """
        return deepcopy(self._raw)