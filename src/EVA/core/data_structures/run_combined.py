import re
import numpy as np
from EVA.core.data_structures.run import Run
from EVA.core.data_structures.spectrum import Spectrum
from EVA.core.physics import rebin
from EVA.core.physics.normalisation import normalise_events

class MultiRun(Run):
    """Run class to hold multiple RunNexus/RunBiriani objects and combine results from run corrections."""

    def __init__(self, runs: list[Run]):
        if not runs:
            raise ValueError("MultiRun requires at least one run.")

        self.runs = runs
        first = runs[0]
        super().__init__(
            raw={},
            # Combine loaded detectors from all runs into a single list. This is a bit complicated
            # for just finding and sorting all unique detectors in GE1-GE9 but more robust if different types of detectors
            # are used in the same run(s) in the future.

            loaded_detectors = sorted(set().union(*(run.loaded_detectors for run in runs)), key=detector_sort_key,),
            run_num=",".join([r.run_num for r in runs]),
            momentum=first.momentum,)
        # self.data = {}
        # for detector in self.loaded_detectors:
        #     self.data[detector] = Spectrum(detector=detector, run_number=self.run_num)
        self.data_type = first.data_type
        self.plot_mode = first.plot_mode
        self.comment_data = [
            "",
            0,
            0,
            "",
            "",
            "",
            "",
        ]  # comment, prompt events, delayed events, start time, end time, prompt time, delayed
        self.normalisation = first.normalisation
        self.prompt_limit = first.prompt_limit
        self.delayed_limit = first.delayed_limit
        self.bin_rate = first.bin_rate

    def set_corrections(self, **kwargs):
        """Apply corrections to each run then sum spectra."""
        current_loaded_detectors = self.loaded_detectors
        self._set_mode(**kwargs)
        self._combine_runs()
        self._group_detectors(kwargs.get("detector_group_dict"))
        self._set_energy_correction(kwargs.get('energy_corrections'))
        self._set_binning(kwargs.get('bin_rate'), kwargs.get('default_bin'))
        self._set_normalisation(kwargs.get('normalisation'), kwargs.get('normalise_which'))
        if current_loaded_detectors != self.loaded_detectors:
            self.detectors_grouped_s.emit()
        self.corrections_updated_s.emit()

    def _set_mode(self, **kwargs):
        """Call mode setting on each run."""
        for run in self.runs:
            run._set_mode(kwargs.get('plot_mode'), kwargs.get('prompt_limit'), kwargs.get('delayed_limit'))
        self.bin_method = self.runs[0].bin_method

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

    def read_comment_data(self):
        """Combine run metadata."""
        prompt_events = 0
        delayed_events = 0
        start = ""
        end = ""
        for run in self.runs:
            comment = run.comment_data[0]
            prompt_events += int(run.comment_data[1])
            delayed_events += int(run.comment_data[2])
            prompt_time = run.comment_data[5]
            delayed_time = run.comment_data[6]

        start = "\n".join(f"{run.run_num} - {run.comment_data[3]}" for run in self.runs)
        end = "\n".join(f"{run.run_num} - {run.comment_data[4]}" for run in self.runs)
        self.comment_data[1] = prompt_events
        self.comment_data[2] = delayed_events
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

    def _combine_runs(self):
        """Sum detector spectra across all runs."""

        # for det in self.loaded_detectors:
        #     x = None
        #     y_sum = None

        #     for run in self.runs:
        #         try:
        #             spectrum = run.data[det]
        #         except KeyError:
        #             continue
        #         if spectrum is None or spectrum.x.size == 0:
        #             continue

        #         if x is None:
        #             x = spectrum.x
        #             y_sum = np.zeros_like(spectrum.y)

        #         y_sum += spectrum.y

        #     if x is not None:
        #         self.data[det].x = x
        #         self.data[det].y = y_sum
        combined = {}
        for run in self.runs:
            for det, spec in run.data.items():
                if det not in combined:
                    combined[det] = Spectrum(
                        detector=det,
                        run_number=self.run_num,
                        x=spec.x.copy(),
                        y=spec.y.copy()
                    )
                else:
                    combined[det].y += spec.y
        self.data = dict(sorted(combined.items(), key=lambda item: detector_sort_key(item[0])))
        self.loaded_detectors = list(self.data.keys())

def detector_sort_key(det):
    return (
        re.match(r"[A-Za-z]+", det).group(),
        int(re.search(r"\d+", det).group())
    )