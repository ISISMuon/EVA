import numpy as np
from matplotlib.backend_bases import MouseEvent


# simulate a mouse click event in figure at specified location
def trigger_figure_click_event(canvas, xdata, ydata, button, ax):
    event = MouseEvent("", canvas, x=0, y=0, button=button)
    event.xdata = np.float64(xdata)
    event.ydata = np.float64(ydata)
    event.inaxes = ax

    return event
