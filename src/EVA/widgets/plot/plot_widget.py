import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout
)

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
    def __init__(self, fig=None, axs=None, parent=None):
        super().__init__()
        # create the figure canvas
        self.canvas = FigureCanvas(fig=fig, axs=axs)

        # this avoids having a navbar when there is no figure
        if fig is None:
            self.navbar = None
        else:
            self.navbar = NavigationToolbar2QT(self.canvas, self)

        # add navbar and plot canvas to layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.navbar, Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

    def update_plot(self, fig=None, axs=None):
        """
        For a simple axes update, it is enough to update the axs parameter of the canvas and redraw.

        When updating the figure of the plot, the navbar will un-link and the figure will not be resized to fit the
        size of the container. To re-link the nav bar and force a size update, the navbar and canvas is removed from
        the layout, deleted, then re-initialised and re-added to widget.
        """

        if axs is not None:
            self.canvas.axs = axs

        if fig is not None:
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
            self.navbar = NavigationToolbar2QT(self.canvas, self)

            self.layout.addWidget(self.navbar)
            self.layout.addWidget(self.canvas)

        self.canvas.draw()

    def release_navigation(self, event):
        # Removes any current zoom or pan
        self.navbar.release_zoom(event)
        self.navbar.release_pan(event)
