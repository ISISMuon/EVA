from copy import deepcopy
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
        self.start_time = comment_data[0]
        self.end_time = comment_data[1]
        self.events_str = comment_data[2]
        self.comment = comment_data[3]

    def set_corrections(
        self,
        energy_corrections=None,
        normalisation=None,
        normalise_which=None,
        bin_rate=None,
        default_bin=None,
        plot_mode=None,
        prompt_limit=None,
    ):
        if normalise_which is None:
            normalise_which = self.normalise_which

        self.data = deepcopy(self._raw)
        self._set_energy_correction(energy_corrections)
        self._set_normalisation(normalisation, normalise_which)
        self._set_binning(bin_rate)
        self.corrections_updated_s.emit()

    def _set_mode(self, *args, **kwargs):
        """No-op for Biriani (no plot modes)."""
        pass

    def _set_normalisation_counts(self, normalise_which: list[str]):
        """Normalise detector spectra by total counts."""
        for detector, spectrum in self._raw.items():
            if detector in normalise_which:
                self.data[detector].y = normalise_counts(spectrum.y)
            else:
                self.data[detector].y = self.data[detector].y
        self.normalisation = "counts"
        self.normalise_which = normalise_which

    def _set_normalisation_events(self, normalise_which):
        try:
            spills = int(self.events_str[19:])
            for detector, spectrum in self._raw.items():
                if detector in normalise_which:
                    self.data[detector].y = normalise_events(spectrum.y, spills)
            self.normalisation = "events"
            self.normalise_which = normalise_which
        except ValueError:
            self._set_normalisation_none()
            raise ValueError("Normalisation by events failed.")

    def read_comment_data(self):
        mapping = dict.fromkeys(range(32))
        start = self.start_time.translate(mapping)[21:]
        end = self.end_time.translate(mapping)[21:]
        events = self.events_str.translate(mapping)[20:]
        comment = self.comment.translate(mapping)[11:]
        self.run_info = f"Run number: {self.run_num}\n\n{comment}\nEvents:{events}\n\nStart time:\n{start}\n\nEnd time:\n{end}"
        return comment, start, end, events
