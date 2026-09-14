from copy import deepcopy
import numpy as np
from EVA.core.data_structures.spectrum import Spectrum
from EVA.core.physics.normalisation import normalise_counts, normalise_events
from EVA.core.data_structures.run import Run


class RunBiriani(Run):
    """Run class for Biriani-based data files."""

    def __init__(self, raw, loaded_detectors, run_num, comment_data, momentum):
        super().__init__(raw, loaded_detectors, run_num, momentum)
        self.data_type = "biriani"
        self.plot_mode = "Biriani Spectrum"
        self.bin_method = "prebinned"
        self.prompt_limit = 0
        self.delayed_limit = 0
        self.start_time = comment_data[0]
        self.end_time = comment_data[1]
        self.events_str = comment_data[2]
        self.comment = comment_data[3]

    def set_corrections(self, **kwargs):
        if kwargs.get('normalise_which') is None:
            kwargs['normalise_which'] = self.normalise_which

        self.data = deepcopy(self._raw)
        current_loaded_detectors = self.loaded_detectors
        self._group_detectors(kwargs.get("detector_group_dict"))
        self._set_energy_correction(kwargs.get('energy_corrections'))
        self._set_normalisation(kwargs.get('normalisation'), kwargs.get('normalise_which'))
        self._set_binning(kwargs.get('bin_rate'))
        if current_loaded_detectors != self.loaded_detectors:
            self.detectors_grouped_s.emit()
        self.corrections_updated_s.emit()

    def _set_mode(self, *args, **kwargs):
        """No-op for Biriani (no plot modes)."""
        pass

    def _set_normalisation_counts(self, normalise_which: list[str]):
        """Normalise detector spectra by total counts."""
        for detector, spectrum in self.data.items():
            if detector in normalise_which:
                self.data[detector].y = normalise_counts(spectrum.y)
            else:
                self.data[detector].y = self.data[detector].y
        self.normalisation = "counts"
        self.normalise_which = normalise_which

    def _set_normalisation_events(self, normalise_which):
        try:
            spills = int(self.events_str[19:])
            for detector, spectrum in self.data.items():
                if detector in normalise_which:
                    self.data[detector].y = normalise_events(spectrum.y, spills)
            self.normalisation = "events"
            self.normalise_which = normalise_which
        except ValueError:
            self._set_normalisation_none()
            raise ValueError("Normalisation by events failed.")

    def _combine_detector_spectra(self, detector_group_dict: dict[str, list[str]] = None):
        combined_data = {}
        self.loaded_detectors = []
        for group_name, detector_names in detector_group_dict.items():
            self.detector_group_dict[group_name] = [det for det in detector_names if det in self.data]
            spectra_in_group = [self.data.get(det) for det in detector_names if det in self.data]
            first = spectra_in_group[0]  # Use the first spectrum as a reference for x values
            # Create a copy of the first spectrum to add y values of each spectrum in place to the x values of the first one.
            y_sum = np.array(first.y, copy=True)

            bad = []
            for detector_name in detector_names[1:]:
                spectrum = self.data[detector_name]
                # Verify if all detectors in group have the same x values across the iteration
                # TODO might be worth having a robust algorithm to add the histograms for different bin centers.
                if not np.array_equal(spectrum.x, first.x):
                    bad.append(detector_name)
                else:
                # if x vals are equal, sum up the counts
                    y_sum += spectrum.y
            if bad:
                # if any of the detectors did not match, raise error with list of detectors that didnt match the first one
                raise ValueError(f"Bad detectors: {bad}")
            combined_data[group_name] = Spectrum(
                detector=group_name,
                run_number=first.run_number,
                x=first.x,  # reuse energy bin values from first detector
                y=y_sum,
                bin_range=first.bin_range
            )
            self.loaded_detectors.append(group_name) # Change list of loaded detectors to the names of the detector groups used
        return combined_data
    def read_comment_data(self):
        mapping = dict.fromkeys(range(32))
        start = self.start_time.translate(mapping)[21:]
        end = self.end_time.translate(mapping)[21:]
        events = self.events_str.translate(mapping)[20:]
        comment = self.comment.translate(mapping)[11:]
        self.run_info = f"Run number: {self.run_num}\n\n{comment}\nEvents:{events}\n\nStart time:\n{start}\n\nEnd time:\n{end}"
        return comment, start, end, events
