import matplotlib.pyplot as plt

from EVA.core.app import get_config
from EVA.core.data_loading import load_data
from EVA.core.data_structures.run import Run, normalisation_types
from EVA.core.plot.plotting import get_ylabel


class MultiPlotModel:
    def _init__(self):
        self.fig, self.ax = None, None
        self.offset = 1
        self.loaded_runs = []

    @staticmethod
    def multi_plot(runs, offset, plot_detectors):
        config = get_config()

        # Sort the runs in the run list by detector to make it easier to plot
        detectors = list(zip(*[run.data.values() for run in runs]))

        # Remove detectors which either contain no data or are set to not be plotted by config
        data = [
            detector_data
            for detector_data in detectors
            if plot_detectors[detector_data[0].detector]
        ]

        numplots = len(data)

        if numplots > 1:
            fig, axs = plt.subplots(nrows=numplots, figsize=(16, 7))

        else:
            # annoying matplotlib fix for one figure in a subplot
            fig, temp = plt.subplots(nrows=1, figsize=(16, 7), squeeze=False)
            axs = [temp[0][0]]

        # labels figures
        fig.suptitle(f"{runs[0].plot_mode} - MultiPlot")
        fig.supxlabel("Energy (keV)")

        fig.supylabel(get_ylabel(runs[0].normalisation))

        # loop through each detector
        for i, detector_data in enumerate(data):
            # loop through each run in the detector
            j = 0
            for dataset in detector_data:
                # get next colour (this will ensure that a color is skipped if data is not plotted)
                next_color = axs[i]._get_lines.get_next_color()
                # only plot if data is not zero
                if dataset.x.size != 0:
                    axs[i].step(
                        dataset.x,
                        dataset.y + j * offset,
                        where="mid",
                        label=dataset.run_number,
                        color=next_color,
                    )
                    j += 1

            detector_name = detector_data[0].detector
            axs[i].set_ylim(0.0)
            axs[i].set_xlim(0.0)
            axs[i].set_title(detector_name)
            axs[i].legend()
            # axs[i].legend(loc="center left", bbox_to_anchor=(1, 0.5))

        plt.subplots_adjust(
            top=0.9, bottom=0.1, left=0.1, right=0.9, hspace=0.45, wspace=0.23
        )
        return fig, axs

    @staticmethod
    def GenReadList(line):
        # decodes the Table
        RunList = []

        for i in range(len(line)):
            # print(i, line[i][0])
            start = line[i][0]
            end = line[i][1]
            step = line[i][2]

            if start != 0:
                if end == 0:
                    RunList.append(str(line[i][0]))
                else:
                    if step == 0:
                        RunList.append(str(start))
                        RunList.append(str(end))
                    else:
                        for j in range(start, end + 1, step):
                            RunList.append(str(j))
        return RunList

    @staticmethod
    def load_multirun(run_list):
        config = get_config()
        working_directory = config["general"]["working_directory"]
        corrections = config["default_corrections"]
        energy_corrections = corrections["detector_specific"]
        normalisation = corrections["normalisation"]
        binning = corrections["binning"]
        plot_mode = corrections["plot_mode"]
        prompt_limit = corrections["prompt_limit"]
        result = [
            load_data.load_run(
                run_num,
                working_directory,
                energy_corrections,
                normalisation,
                binning,
                plot_mode,
                prompt_limit,
            )
            for run_num in run_list
        ]

        runs, flags = list(zip(*result))

        # iterate through loaded runs to remove failed ones:
        blank_runs = []
        norm_failed_runs = []
        good_runs = []

        for i, run in enumerate(runs):
            if flags[i]["no_files_found"]:
                blank_runs.append(run)
            else:
                if flags[i][
                    "norm_by_spills_error"
                ]:  # if normalisation failed, remove run
                    norm_failed_runs.append(run)
                else:
                    good_runs.append(run)

        return good_runs, blank_runs, norm_failed_runs

    def get_plot_detectors(self) -> list[str]:
        """
        Gets which detectors to plot for from the loaded config.

        Returns: list of detector names to plot for.

        """
        config = get_config()
        show_plot = config.get_run_save(
            config["general"]["working_directory"], self.loaded_runs[0].run_num
        )["show_plot"]
        plot_detectors = [
            det
            for det, show in show_plot.items()
            if show and det in self.loaded_runs[0].loaded_detectors
        ]
        return plot_detectors

    def multirun_corrections(self):
        """
        Apply run corrections to all loaded runs using settings from workspace view.
        """
        workspace_view = self.workspace.view
        binning = workspace_view.binning_spin_box.value()
        normalisation_index = workspace_view.normalisation_type_combo_box.currentIndex()
        norm_type = normalisation_types[normalisation_index]
        plot_type = workspace_view.nexus_plot_display_combo_box.currentText()
        prompt_limit = workspace_view.prompt_limit_textbox.text()
        # normalisation can fail if user wants to normalise by events but no comment file have been loaded
        try:
            [
                run.set_corrections(
                    normalisation=norm_type,
                    bin_rate=binning,
                    plot_mode=plot_type,
                    prompt_limit=prompt_limit,
                )
                for run in self.model.loaded_runs
            ]

        except ValueError:
            workspace_view.display_error_message(
                title="Normalisation error",
                message="Cannot normalise by events when comment file is not loaded. Please ensure that the comment.dat file is in your loaded directory.",
            )

            self.populate_settings_panel()
