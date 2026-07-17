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
        self.plot_mode = plot_mode
        self.prompt_limit = prompt_limit
        self.delayed_limit = delayed_limit
        self.bin_method = self._bin_method_from_plotmode(plot_mode)
        self.data = deepcopy(self._raw)

    def set_corrections(self, **kwargs):
        # initialize an empty data dict with detector name: Spectrum key: value pairs
        self.data = deepcopy(self._raw)

        current_loaded_detectors = self.loaded_detectors
        self._set_mode(kwargs.get('plot_mode'), kwargs.get('prompt_limit'), kwargs.get('delayed_limit'))
        self._group_detectors(kwargs.get("detector_group_dict"))
        self._set_energy_correction(kwargs.get('energy_corrections'))
        self._set_binning(kwargs.get('bin_rate'), kwargs.get('default_bin'))
        self._set_normalisation(kwargs.get('normalisation'), kwargs.get('normalise_which'))
        if current_loaded_detectors != self.loaded_detectors:
            self.detectors_grouped_s.emit()
        self.corrections_updated_s.emit()
        # for detector, spectrum in self.data.items():
        #     print(f"name: {detector}, tot pts = {np.sum(spectrum.y)}")

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

    def _set_mode(
        self,
        plot_mode: str | None = None,
        prompt_limit: str | None = None,
        delayed_limit: str | None = None,
    ):
        """Set up detector data depending on the chosen plot mode."""
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

                self.data[detector].x = spectrum.x
                self.data[detector].y = spectrum.y
                self.data[detector].bin_range = self._raw[detector].bin_range
                self.bin_method = "prebinned"

            elif plot_mode == "IBEX Delayed Spectrum":
                spectrum.x = self._raw[detector].delayed_energy[:]
                spectrum.y = self._raw[detector].delayed_count[:]
                self.data[detector].x = spectrum.x
                self.data[detector].y = spectrum.y
                self.data[detector].bin_range = self._raw[detector].bin_range
                self.bin_method = "prebinned"

            elif plot_mode == "Manual Delayed Spectrum":
                time_data = self._raw[detector].time[:]
                energy_data = self._raw[detector].energy[:]
                mask = (time_data > self.prompt_limit) & (
                    time_data < self.delayed_limit
                )
                self._raw[detector].cut_data = energy_data[mask]
                self.data[detector].bin_range = self._raw[detector].bin_range
                self.bin_method = "raw"

            elif plot_mode == "Manual Prompt Spectrum":
                time_data = self._raw[detector].time[:]
                energy_data = self._raw[detector].energy[:]
                mask = (time_data > 0) & (time_data < self.prompt_limit)
                self._raw[detector].cut_data = energy_data[mask]
                self.data[detector].bin_range = self._raw[detector].bin_range
                self.bin_method = "raw"

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
                    time_data = self._raw[detector].time[:]
                    energy_data = self._raw[detector].energy[:]
                    mask = time_data > 0
                    self._raw[detector].cut_data = energy_data[mask]
                    self.bin_method = "raw"

                self.data[detector].bin_range = self._raw[detector].bin_range

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

    def _bin_method_from_plotmode(self, plot_mode: str) -> str:
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
        if self.bin_method == "prebinned":
            return self.combine_prebinned_spectra(detector_group_dict)
        elif self.bin_method == "raw":
            return self.combine_raw_spectra(detector_group_dict)

    def combine_prebinned_spectra(self, detector_group_dict: dict[str, list[str]]):
        combined_data = {}
        for group_name, detector_names in detector_group_dict.items():
            self.detector_group_dict[group_name] = [det for det in detector_names if det in self.data]
            spectra_in_group = [self.data.get(det) for det in detector_names if det in self.data]
            if not spectra_in_group:
                continue
            # Reference detector defines the energy axis
            reference_energy = spectra_in_group[0].x
            ref_width = np.mean(np.diff(reference_energy))
            bin_num = len(reference_energy)
            ref_edges = np.zeros(bin_num + 1)

            ref_edges[:-1] = reference_energy - ref_width/2
            ref_edges[-1] = reference_energy[-1] + ref_width/2
            combined_counts = np.zeros(bin_num)
            for spectrum in spectra_in_group:

                rebinned = rebin.rebin_to_reference(
                    spectrum.x,
                    spectrum.y,
                    ref_edges=ref_edges,
                    bin_number=bin_num
                )

                combined_counts += rebinned

            combined_data[group_name] = Spectrum(
                detector=group_name,
                run_number=spectra_in_group[0].run_number,
                x=reference_energy.copy(),
                y=combined_counts,
                bin_range=spectra_in_group[0].bin_range
            )
        return combined_data

    def combine_raw_spectra(self, detector_group_dict: dict[str, list[str]]):
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
