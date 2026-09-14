from copy import deepcopy

import numpy as np
from EVA.core.data_structures.spectrum import Spectrum
from EVA.core.physics import rebin
from EVA.core.physics.normalisation import normalise_events, normalise_counts
from EVA.core.data_structures.run import Run


class RunNexus(Run):
    """Run class for Nexus data."""

    def __init__(
        self,
        raw,
        loaded_detectors,
        run_num,
        plot_mode,
        prompt_limit,
        delayed_limit,
        comment_data,
        momentum,
    ):
        super().__init__(raw, loaded_detectors, run_num, momentum)
        self.data_type = "nexus"
        self.comment_data = comment_data
        # self.plot_mode = None
        self.plot_mode = plot_mode
        self.prompt_limit = prompt_limit
        self.delayed_limit = delayed_limit
        self.bin_method = self._bin_method_from_plotmode(plot_mode)
        self.data = deepcopy(self._raw)
        self._raw_cache = {}      # {detector : (time_array, energy_array)}
        self._mode_cache = {}     # Cache of binned data for {(detector, plot_mode, prompt_limit, delayed_limit) : energy, counts}
    def set_corrections(self, **kwargs):
        # initialize an empty data dict with detector name: Spectrum key: value pairs
        self.data = deepcopy(self._raw)

        current_loaded_detectors = self.loaded_detectors
        self._set_mode(kwargs.get('plot_mode'), kwargs.get('prompt_limit'), kwargs.get('delayed_limit'))
        self._set_energy_correction(kwargs.get('energy_corrections'))
        self._set_efficiency_correction(kwargs.get('efficiency_corrections'))
        self._group_detectors(kwargs.get("detector_group_dict"))
        self._set_binning(kwargs.get('bin_rate'), kwargs.get('default_bin'))
        self._set_normalisation(kwargs.get('normalisation'), kwargs.get('normalise_which'))
        if current_loaded_detectors != self.loaded_detectors:
            self.detectors_grouped_s.emit()
        else:
            self.corrections_updated_s.emit()

    def _set_normalisation_events(self, normalise_which):
        """Normalise spectra by event count using comment metadata."""
        if self.plot_mode in ["IBEX Prompt Spectrum", "Manual Prompt Spectrum"]:
            try:
                spills = int(self.comment_data[1]) # Prompt counts
            except ValueError:
                self._set_normalisation_none()
                raise ValueError("Normalisation by events failed.")

        elif self.plot_mode in [
            "IBEX Delayed Spectrum",
            "Manual Delayed Spectrum",
        ]:
            try:
                spills = int(self.comment_data[2]) # Delayed counts
            except ValueError:
                self._set_normalisation_none()
                raise ValueError("Normalisation by events failed.")
        else:
            raise ValueError(f"{self.plot_mode} not in list of normalisation methods.")

        for detector, spectrum in self.data.items():
            if detector in normalise_which:
                self.data[detector].y = normalise_events(
                    self.data[detector].y, spills
                )

        self.normalisation = "events"
        self.normalise_which = normalise_which

    def _set_efficiency_correction(self, energy_corrections):
        pass

    def _set_mode(
        self,
        plot_mode: str | None = None,
        prompt_limit: str | None = None,
        delayed_limit: str | None = None,
    ):
        """Loads datasets onto memory/ from saved references in the Nexus file/
        Fetches from memory if manual spectra are requested after the first time.
        For (prompt/delayed) manual spectra, also apply requested time selection cuts
        the spectrum objects stored in self._raw are then copied on to self.data
        for other run corrections.
        Args:
            plot_mode (str | None, optional): Spectrum required. Defaults to None.
            prompt_limit (str | None, optional): Upper time limit for IBEX/Manual prompt spectra, lower limit for delayed equivalents. if None, uses last saved one.
            delayed_limit (str | None, optional): Upper time limit for IBEX/Manual delayed spectra. if None, uses last saved one.
        Raises:
            ValueError: If a 
        """
        if plot_mode is None:
            plot_mode = self.plot_mode
        else:
            self.plot_mode = plot_mode

        if prompt_limit is None:
            prompt_limit = self.prompt_limit
        else:
            self.prompt_limit = int(prompt_limit)

        if delayed_limit is None:
            delayed_limit = self.delayed_limit
        else:
            self.delayed_limit = int(delayed_limit)

        for detector, spectrum in self._raw.items():
            if plot_mode == "IBEX Prompt Spectrum":
                spectrum.x = self._raw[detector].prompt_energy[:]
                spectrum.y = self._raw[detector].prompt_count[:]
                self.data[detector] = deepcopy(self._raw[detector])

                self.bin_method = "prebinned"

            elif plot_mode == "IBEX Delayed Spectrum":
                spectrum.x = self._raw[detector].delayed_energy[:]
                spectrum.y = self._raw[detector].delayed_count[:]
                self.data[detector] = deepcopy(self._raw[detector])

                self.bin_method = "prebinned"

            elif plot_mode == "Manual Delayed Spectrum":
                spectrum.x, spectrum.y = self._get_manual_spectrum(
                    detector, low_limit=self.prompt_limit, high_limit=self.delayed_limit
                )
                self.data[detector] = deepcopy(self._raw[detector])
                self.bin_method = "prebinned"

            elif plot_mode == "Manual Prompt Spectrum":
                spectrum.x, spectrum.y = self._get_manual_spectrum(detector, low_limit=0, high_limit=self.prompt_limit)
                self.data[detector] = deepcopy(self._raw[detector])
                self.bin_method = "prebinned"

            elif plot_mode == "Efficiency Spectrum":
                if (
                    self._raw[detector].efficiency_hist_counts
                    and self._raw[detector].efficiency_hist_energy
                ):
                    self.data[detector].x = self._raw[detector].efficiency_hist_energy[
                        :
                    ]
                    self.data[detector].y = self._raw[detector].efficiency_hist_counts[
                        :
                    ]
                    self.bin_method = "prebinned"
                else:
                    spectrum.x, spectrum.y = self._get_manual_spectrum(detector, low_limit=0, high_limit=np.inf)
                    self.data[detector] = deepcopy(self._raw[detector])
                    self.bin_method = "prebinned"

            elif plot_mode == "Time Plot":
                time_data = self._raw[detector].time[:]
                mask = (time_data > 0) & (time_data < 2000)
                filtered_time_data = self._raw[detector].time[mask]
                spectrum.x, spectrum.y = rebin.rebin_raw(
                    filtered_time_data, bin_num=100, bin_range=(0, 2000)
                )

                self.data[detector].x = spectrum.x
                self.data[detector].y = spectrum.y
                self.bin_method = "prebinned"

            else:
                raise ValueError(f"Invalid plot mode: '{plot_mode}'")

            if len(self.data[detector].x) == 0 or len(self.data[detector].y) == 0:
                raise ValueError(f"No data was successfully loaded for {plot_mode}")
            
    def _bin_method_from_plotmode(self, plot_mode: str) -> str:
        """ 
        Legacy function that used to control type of binning function called depending on if data was pre-binned or raw data points.
        Currently redundant as all data types are now binned to the same 32768 base first before rebin is called, but leaving it here if things
        change in the future.
        """
        if plot_mode in ["IBEX Prompt Spectrum", "IBEX Delayed Spectrum", "Time Plot"]:
            return "prebinned"
        elif plot_mode in [
            "Manual Prompt Spectrum",
            "Manual Delayed Spectrum",
            "Efficiency Spectrum",
        ]:
            return "raw"
        elif plot_mode in ["IBEX 2D Time-Energy Plot", "Manual 2D Time-Energy Plot"]:
            return "hist"
        else:
            raise ValueError(f"Invalid plot mode: '{plot_mode}'")

    def _combine_detector_spectra(self, detector_group_dict: dict[str, list[str]] = None):
        """ 
        Legacy function that controlled algorithm used to combine events into a single histogram depending on type. Currently all the main spectra are
        pre-binned before this block is executed so defaults to combine prebinned spectra.
        """
        if self.bin_method == "prebinned":
            return self.combine_prebinned_spectra(detector_group_dict)
        elif self.bin_method == "raw":
            return self.combine_raw_spectra(detector_group_dict)

    def combine_prebinned_spectra(self, detector_group_dict: dict[str, list[str]]):
        """Combines all spectra within a detector group onto the base energy axis of the first detector in the group
        using a fast piece-wise linear cum-sum interpolating function (that conserves total count for each spectra)
        and creates a dict of new spectrum objects for each detector group.

        Args:
            detector_group_dict (dict[str, list[str]]): dictionary of name for a detector group and list of detectors in the group

        Returns:
            dict[str, Spectrum]: Returns a dictionary with the same format as _raw with the combined spectra for each detector group.
        """
        combined_data = {}
        for group_name, detector_names in detector_group_dict.items():
            # Fetch detectors and spectra that are in a group that are also detected within the run.
            self.detector_group_dict[group_name] = [det for det in detector_names if det in self.data]
            spectra_in_group = [self.data.get(det) for det in detector_names if det in self.data]
            if not spectra_in_group:
                continue # If no run data is in a group, skip over it.
            # Use the x/energy/bin centers of the first spectrum as the reference base to interpolate other spectra onto.
            reference_energy = spectra_in_group[0].x
            ref_width = np.mean(np.diff(reference_energy))
            bin_num = len(reference_energy)
            ref_edges = np.zeros(bin_num + 1)
            # Convert the bin centers to lower and upper limit for bin edges
            ref_edges[:-1] = reference_energy - ref_width/2
            ref_edges[-1] = reference_energy[-1] + ref_width/2
            combined_counts = np.zeros(bin_num)
            for spectrum in spectra_in_group:
                # Interpolate each spectra to the reference bins.
                rebinned = rebin.rebin_to_reference_fast(
                    spectrum.x,
                    spectrum.y,
                    ref_edges=ref_edges,
                    bin_number=bin_num
                )
                # Add the spectra up
                combined_counts += rebinned
            # Create a combined data dict with similar format to self.data
            combined_data[group_name] = Spectrum(
                detector=group_name,
                run_number=spectra_in_group[0].run_number,
                x=reference_energy.copy(),
                y=combined_counts,
                bin_range=spectra_in_group[0].bin_range
            )
        return combined_data

    def combine_raw_spectra(self, detector_group_dict: dict[str, list[str]]):
        """ 
        An implementation was made for binning raw data points from each spectrum onto the same x axis and summing them up was made
        But was discarded due to digitizer limitations, left here for potential future implementations 
        """
        combined_data = {}
        for group_name, detector_names in detector_group_dict.items():
            self.detector_group_dict[group_name] = [det for det in detector_names if det in self.data]
            spectra_in_group = [self._raw.get(det) for det in detector_names if det in self.data]
            if not spectra_in_group:
                continue
            bin_num = int(self.default_bin / self.bin_rate)
            edges = np.linspace(
                spectra_in_group[0].bin_range[0],
                spectra_in_group[0].bin_range[1],
                bin_num + 1,
            )

            x = (edges[:-1] + edges[1:]) / 2
            combined_counts = np.zeros(bin_num, dtype=np.int64)

            for spectrum in spectra_in_group:
                counts, _ = np.histogram(
                    spectrum.cut_data,
                    bins=edges,
                )
                combined_counts += counts
            combined_data[group_name] = Spectrum(
                detector=group_name,
                run_number=spectra_in_group[0].run_number,
                x=x,
                y=combined_counts,
                bin_range=spectra_in_group[0].bin_range
            )
        return combined_data

    def _get_raw_time_energy(self, detector) -> list[np.array, np.array]:
        """Loads raw data on to memory when accessed for the first time for manual spectra.
        Cleanest way I could think of to avoid eagerly loading event data points at launch (which is the default IBEX spectra)
        and keeping event data points in memory when staying on manual spectra and making run corrections to avoid
        unloading and loading them each time as they can be quite big.

        Args:
            detector (str): detector to fetch event data for

        Returns:
            list[np.array, np.array]: time and energy arrays for detecotr.
        """
        if detector not in self._raw_cache:
            self._raw_cache[detector] = (
                self._raw[detector].time[:],
                self._raw[detector].energy[:],
            )
        return self._raw_cache[detector]

    def _get_manual_spectrum(self, detector, low_limit, high_limit):
        """
        Checks if a histogram dataset has already been generated using data points for a given time selection cut and returns (energy, counts if yes).
        Else:
        Fetches the unbinned energy and time data from data file, applies a time selection cut, bins it to default num bins (32768)
        and returns it. Shared by Manual Prompt/Delayed and Efficiency fallback (for old run files that were missing raw_data_1/detector_{i}_energyHist/energy).

        Args:
            detector (str): detector to fetch spectra for
            low_limit (int | float): The lower limit on the selection cut in ns( eg >0 for prompt spectrum)
            high_limit (int | float): The upper limit on the selection cut in ns( eg <2000 for prompt spectrum)

        Returns:
            tuple(np.array, np.array): The bin centers (energy) and counts (events in bin) of histogram of data points using the default bin (32768).
        """
        key = (detector, low_limit, high_limit)
        if key in self._mode_cache:
            return self._mode_cache[key]

        time_data, energy_data = self._get_raw_time_energy(detector)
        mask = (time_data > low_limit) & (time_data < high_limit)
        cut_data = energy_data[mask]
        energy, count = rebin.rebin_raw(
            cut_data, self.default_bin, bin_range=self.data[detector].bin_range
        )
        self._mode_cache[key] = (energy, count)
        return energy, count

    def read_comment_data(self):
        comment = self.comment_data[0]
        prompt_events = self.comment_data[1]
        delayed_events = self.comment_data[2]
        start = self.comment_data[3]
        end = self.comment_data[4]
        prompt_time = self.comment_data[5]
        delayed_time = self.comment_data[6]

        self.run_info = (
            f"Run number: {self.run_num}\n\n{comment}\n\n"
            f"Prompt Events: {prompt_events}\n"
            f"Prompt Interval:\n{prompt_time}\n\n"
            f"Delayed Events: {delayed_events}\n"
            f"Delayed Interval:\n{delayed_time}\n\n"
            f"Start time:\n{start}\n\n"
            f"End time:\n{end}"
        )

        return (
            comment,
            start,
            end,
            f"Prompt events: {prompt_events} Delayed events: {delayed_events}",
        )

    @classmethod
    def empty(cls) -> "Run":
        """Create an empty Run with only run_num populated."""
        return cls(
            run_num=0,
            momentum=0,
            raw={},
            loaded_detectors=[],
            plot_mode="IBEX Prompt Spectrum",
            prompt_limit=0,
            delayed_limit=20000000,
            comment_data=[""] * 7,
        )
