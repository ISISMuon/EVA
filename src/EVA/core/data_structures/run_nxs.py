import numpy as np
from EVA.core.data_structures.spectrum_nexus import SpectrumNexus
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
        comment_data,
        momentum,
    ):
        super().__init__(raw, loaded_detectors, run_num, momentum)
        self.data_type = "nexus"
        self.comment_data = comment_data
        self.plot_mode = plot_mode
        self.prompt_limit = prompt_limit
        self.bin_method = self._bin_method_from_plotmode(plot_mode)
        self.data = {
            key: SpectrumNexus(
                detector=nexus_obj.detector, run_number=nexus_obj.run_number
            )
            for key, nexus_obj in self._raw.items()
        }

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
        self.data = {
            key: SpectrumNexus(
                detector=nexus_obj.detector, run_number=nexus_obj.run_number
            )
            for key, nexus_obj in self._raw.items()
        }
        self._set_mode(plot_mode, prompt_limit)
        self._set_energy_correction(energy_corrections)
        self._set_binning(bin_rate, default_bin)
        self._set_normalisation(normalisation, normalise_which)

        self.corrections_updated_s.emit()

    def _set_normalisation_events(self, normalise_which):
        """Normalise spectra by event count using comment metadata."""
        try:
            if self.plot_mode in ["IBEX Prompt Spectrum", "Manual Prompt Spectrum"]:
                spills = int(self.comment_data[1])
            else:
                spills = int(self.comment_data[2])

            for detector, spectrum in self._raw.items():
                if detector in normalise_which:
                    self.data[detector].y = normalise_events(spectrum.y, spills)

            self.normalisation = "events"
            self.normalise_which = normalise_which

        except ValueError:
            self._set_normalisation_none()
            raise ValueError("Normalisation by events failed.")

    def _set_mode(self, plot_mode: str | None = None, prompt_limit: str | None = None):
        """Set up detector data depending on the chosen plot mode."""
        if plot_mode is None:
            plot_mode = self.plot_mode
        else:
            self.plot_mode = plot_mode

        if prompt_limit is None:
            prompt_limit = self.prompt_limit
        else:
            self.prompt_limit = int(prompt_limit)
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
                mask = (time_data > self.prompt_limit) & (time_data < 20000000)
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
                time_data = self._raw[detector].time[:]
                energy_data = self._raw[detector].energy[:]
                mask = time_data > 0
                self._raw[detector].cut_data = energy_data[mask]
                self.data[detector].bin_range = self._raw[detector].bin_range
                self.bin_method = "raw"

            elif plot_mode == "Time Plot":
                time_data = self._raw[detector].time[:]
                mask = (time_data > 0) & (time_data < 2000)
                filtered_time_data = self._raw[detector].time[mask]
                spectrum.x, spectrum.y = rebin.nxs_rebin(
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
            comment_data=[""] * 7,
        )
