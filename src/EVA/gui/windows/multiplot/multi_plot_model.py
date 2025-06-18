import matplotlib.pyplot as plt

from EVA.core.app import get_config
from EVA.core.data_loading import load_data

class MultiPlotModel:
    def _init__(self):
        self.fig, self.ax = None, None

        self.offset = 1
        self.detector_selection = ["GE1"]
        self.loaded_runs = None

    @staticmethod
    def multi_plot(runs, offset, plot_detectors):
        config = get_config()

        # Sort the runs in the run list by detector to make it easier to plot
        detectors = list(zip(*[run.data.values() for run in runs]))

        # Remove detectors which either contain no data or are set to not be plotted by config
        data = [detector_data for detector_data in detectors if detector_data[0].detector in plot_detectors]

        numplots = len(data)

        if numplots > 1:
            fig, axs = plt.subplots(nrows=numplots, figsize=(16, 7))

        else:
            #annoying matplotlib fix for one figure in a subplot
            fig, temp = plt.subplots(nrows=1, figsize=(16, 7), squeeze=False)
            axs = [temp[0][0]]

            # labels figures
            fig.suptitle("MultiPlot")
            fig.supxlabel("Energy (keV)")

            fig.supylabel("Intensity (raw)")

        # loop through each detector
        for i, detector_data in enumerate(data):

            # loop through each run in the detector
            j = 0
            for dataset in detector_data:
                # get next colour (this will ensure that a color is skipped if data is not plotted)
                next_color = axs[i]._get_lines.get_next_color()
                # only plot if data is not zero
                if dataset.x.size != 0:
                    axs[i].step(dataset.x, dataset.y+j*offset, where='mid', label=dataset.run_number, color=next_color)
                    j += 1

            detector_name = detector_data[0].detector
            axs[i].set_ylim(0.0)
            axs[i].set_xlim(0.0)
            axs[i].set_title(detector_name)
            axs[i].legend()
            #axs[i].legend(loc="center left", bbox_to_anchor=(1, 0.5))

        plt.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.9, hspace=0.45, wspace=0.23)
        return fig, axs

    @staticmethod
    def GenReadList(line):
        #decodes the Table
        RunList = []

        for i in range(len(line)):
            #print(i, line[i][0])
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
                        for j in range(start,end+1,step):
                            RunList.append(str(j))
        return RunList

    @staticmethod
    def load_runs(run_list):
        dir = get_config()["general"]["working_directory"]
        e_corr = get_config()["default_corrections"]["detector_specific"]
        norm = get_config()["default_corrections"]["normalisation"]
        binning = get_config()["default_corrections"]["binning"]

        result = [load_data.load_run(run_num, working_directory=dir, energy_corrections=e_corr,
                                     normalisation=norm, binning=binning) for run_num in run_list]

        runs, flags = list(zip(*result))

        # iterate through loaded runs to remove failed ones:
        blank_runs = []
        norm_failed_runs = []
        good_runs = []

        for i, run in enumerate(runs):
            if flags[i]["no_files_found"]:
                blank_runs.append(run)
            else:
                if flags[i]["norm_by_spills_error"]: # if normalisation failed, remove run
                    norm_failed_runs.append(run)
                else:
                    good_runs.append(run)

        return good_runs, blank_runs, norm_failed_runs

