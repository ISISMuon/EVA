import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from EVA.core.app import get_app

matplotlib.use("QtAgg")


class FigureCanvas(FigureCanvasQTAgg):
    """
    This is the class that interacts with matplotlib and does all the plot rendering.
    """

    def __init__(self, fig=None, axs=None):
        super().__init__(fig)
        self.axs = axs


class PlotWidget(QWidget):
    """
    This is a "wrapper" widget class that contains both the navigation bar and the figure canvas, to avoid having to
    link the two manually every time a PlotWidget is needed. It also takes care of figure resizing and linking the
    navbar and plot together.
    """

    plot_clicked = pyqtSignal(object)
    def __init__(
        self, fig=None, axs=None, parent=None, plot_name=None, plot_manager=None
    ):
        super().__init__()
        self.layout = QVBoxLayout(self)
        # create the figure canvas
        self.canvas = FigureCanvas(fig=fig, axs=axs)
        self.plot_manager = plot_manager
        self.plot_name = plot_name
        # add navbar and plot canvas to layout
        # this avoids having a navbar when there is no figure
        if fig is None:
            self.navbar = None
        else:
            self.canvas.mpl_connect("button_press_event", self.plot_clicked.emit)
            self.navbar = NavigationToolbar2QT(self.canvas, self)
            self.layout.addWidget(self.navbar, Qt.AlignmentFlag.AlignLeft)
        # add navbar and plot canvas to layout
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

    def trigger_update(self, plot_id):
        if self.plot_id == plot_id:
            self.update_plot()

    def update_plot(self, fig=None, axs=None):
        """
        For a simple axes update, it is enough to update the axs parameter of the canvas and redraw.

        When updating the figure of the plot, the navbar will un-link and the figure will not be resized to fit the
        size of the container. To re-link the nav bar and force a size update, the navbar and canvas is removed from
        the layout, deleted, then re-initialised and re-added to widget.
        """

        if axs is not None:
            self.canvas.axs = axs

        if fig is not None and fig is not self.canvas.figure:
            # only hit this when the Figure identity actually changes
            plt.close(self.canvas.figure)

            self.canvas.figure = fig

            # Since canvas is removed from widget and has no parent, 'deleteLater()' will delete it immediately.
            self.layout.removeWidget(self.canvas)
            self.canvas.deleteLater()

            # Only delete navbar if it is not None, else it will error
            if self.navbar is not None:
                self.layout.removeWidget(self.navbar)
                self.navbar.deleteLater()

            # Create new navbar and figure canvas, link them and add them back into widget layout
            self.canvas = FigureCanvas(fig=self.canvas.figure, axs=self.canvas.axs)
            self.canvas.mpl_connect("button_press_event", self.plot_clicked.emit)
            self.navbar = NavigationToolbar2QT(self.canvas, self)
            self.layout.addWidget(self.navbar)
            self.layout.addWidget(self.canvas)

        self.canvas.draw_idle()
        self.update_home_view(self.canvas.axs)

    def update_home_view(self, axs):
        """
        Set the toolbar's "home" view to the full data range (x: 0 to
        max, y: 0 to 1.2 * data max) without changing what's currently displayed.
        """
        axs = axs if isinstance(axs, (list, tuple, np.ndarray)) else [axs]

        # remember the current (zoomed) view so we can restore it after
        current_limits = [(ax.get_xlim(), ax.get_ylim()) for ax in axs]

        for ax in axs:
            ax.relim()  # refresh dataLim based on current artist data
            x0, x1 = ax.dataLim.x0, ax.dataLim.x1
            y0, y1 = ax.dataLim.y0, ax.dataLim.y1

            # skip axes with no usable data (empty/NaN artists leave dataLim non-finite)
            # Simplest work around for blank residual axes in a fresh peakfit window I could think of.
            if not (np.isfinite(x0) and np.isfinite(x1) and np.isfinite(y0) and np.isfinite(y1)):
                continue

            ax.set_xlim(x0, x1)
            lower_ylim = min(0, y0)
            ax.set_ylim(1.2 * lower_ylim, 1.2 * y1)

        # wipe the nav stack and capture this full view as "home"
        self.navbar.update()
        self.navbar.push_current()

        # put the actual (zoomed) view back on screen
        for ax, (xlim, ylim) in zip(axs, current_limits):
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        self.canvas.draw_idle()

    def release_navigation(self, event):
        # Removes any current zoom or pan
        self.navbar.release_zoom(event)
        self.navbar.release_pan(event)
