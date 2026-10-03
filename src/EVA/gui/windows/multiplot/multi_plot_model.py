import matplotlib.pyplot as plt

from EVA.core.app import get_config
from EVA.core.data_loading import load_data
from EVA.core.plot.plotting import get_ylabel


class MultiPlotModel:
    def _init__(self):
        self.fig, self.ax = None, None
        self.offset = 1
        self.loaded_runs = []

    @staticmethod
    def multi_plot(runs, offset, plot_detectors):
        config = get_config()


        # Group data by detectors selected for plotting and remove detectors which either contain no data for all runs
        data = [
            [
                run.data[detector_name]
                for run in runs
                if detector_name in run.data
                and plot_detectors.get(detector_name, False)
                and run.data[detector_name].x.size != 0
            ]
            for detector_name in plot_detectors
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
        data_directory = config["general"]["data_directory"]
        corrections = config["default_corrections"]
        energy_corrections = corrections["detector_specific"]
        normalisation = corrections["normalisation"]
        binning = corrections["binning"]
        plot_mode = corrections["plot_mode"]
        prompt_limit = corrections["prompt_limit"]
        delayed_limit = corrections["delayed_limit"]

        result = [
            load_data.load_run(
                run_num,
                data_directory,
                energy_corrections,
                normalisation,
                binning,
                plot_mode,
                prompt_limit,
                delayed_limit,
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
