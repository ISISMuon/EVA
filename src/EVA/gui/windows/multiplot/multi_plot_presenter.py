import logging
from EVA.gui.windows.multiplot.multi_plot_model import MultiPlotModel
from EVA.gui.windows.multiplot.multi_plot_view import MultiPlotView

logger = logging.getLogger(__name__)


class MultiPlotPresenter:
    def __init__(self, view: MultiPlotView, model: MultiPlotModel):
        self.view = view
        self.model = model

        self.view.plot_multi.clicked.connect(self.start_multiplot)

    def start_multiplot(self):
        try:
            offset, table_data, checkstates = self.view.get_form_data()
        except (ValueError, AttributeError):
            self.view.display_message(title="Input error", message="Invalid input.")
            return

        plot_detectors =  [det for det, show in checkstates.items() if show]

        if len(plot_detectors) == 0:
            self.view.display_message(title="Input error", message="Select at least one detector to plot for.")

        # generates a list of runs to load and plot
        run_list = self.model.GenReadList(table_data)

        if not run_list: # if no runs found
            logger.error("No runs specified for multiplot.")
            self.view.display_error_message(title="Multi-run plot error",
                                            message="Error: You must specify at least one valid run number in the table.")
            return

        # loads runs from list
        runs, empty_runs, norm_failed_runs = self.model.load_runs(run_list)

        # reads data and returns as each detector and as an array
        self.model.loaded_runs = runs
        self.model.offset = offset

        # error handling
        run_numbers_str = ", ".join([run.run_num for run in empty_runs])

        if 0 < len(empty_runs) < 10:
            self.view.display_message(title="Multi-run plot error",
                                      message=f"Error: No files found for following run(s): {run_numbers_str}")
        elif len(empty_runs) >= 10:
            self.view.display_message(title="Multi-run plot error",
                                      message=f"Error: More than 10 runs failed to load.")

        if len(runs) == 0:
            logger.error("No files found for runs %s.", run_numbers_str)
            return  # Quit now if all runs failed to load
        else:
            logger.warning("No files found for runs %s.", run_numbers_str)

        # plots multiple runs from the runlist and with a y offset
        fig, ax = self.model.multi_plot(runs, offset, plot_detectors)
        self.view.plot.update_plot(fig, ax)
