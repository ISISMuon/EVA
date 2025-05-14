import matplotlib.pyplot as plt
import numpy as np

from EVA.core.app import get_app
from EVA.core.data_structures.run import Run
from EVA.core.data_structures.spectrum import Spectrum


def Plot_Peak_Location(ax: plt.Axes, x: np.ndarray, y: np.ndarray, peak_indices: np.ndarray):
    """
    Plots the peak location for each peak specified in peak_indices on a specified Axes instance.

    Args:
        ax: axis to plot peaks on
        x: input x-data
        y: input y-data
        peak_indices: indices of data arrays to plot peaks on
    """
    peak_heights = y[peak_indices]
    peak_positions = x[peak_indices]
    ax.scatter(peak_positions, peak_heights, color='r', s=20, marker='X', label='peaks')

def plot_spectrum(spectrum: Spectrum, normalisation: str, **settings: dict) -> tuple[plt.Figure, plt.Axes]:
    """
    Plots a single spectrum (for a single detector).

    Args:
        spectrum: Spectrum object to plot
        normalisation: Normalisation type - valid options are "counts", "none", "spills"
        **settings:
            * **title** (str): plot title
            * **colour** (str): plot fill colour

    Returns:
        matplotlib Figure and Axes with plotted spectrum
    """
    title = settings.get("title", f"Run Number: {spectrum.run_number} {spectrum.detector}")
    colour = settings.get("colour", "yellow")

    fig, ax = plt.subplots(1)
    fig.suptitle(title)
    fig.supxlabel("Energy (keV)")

    # sets the correct labels
    if normalisation == "counts":
        fig.supylabel("Intensity Normalised to Counts (10^5)")
    elif normalisation == "events":
        fig.supylabel("Intensity Normalised to Spills (10^5)")
    else:
        fig.supylabel("Intensity")

    ax.fill_between(spectrum.x, spectrum.y, step='mid', color=colour)
    ax.step(spectrum.x, spectrum.y, where='mid', color='black', label=f"_{spectrum.detector}")
    ax.set_ylim(0.0)
    ax.set_xlim(0.0)

    return fig, ax

def plot_run(run: Run, **settings: dict) -> tuple[plt.Figure, plt.Axes]:
    """
    Plots a Run with a subplot for each Spectrum in the Run.

    Args:
        run: Run object to plot
        **settings:

            * **show_detectors** (list): which detectors to plot (default is all loaded detectors)

            * **title** (str): plot title

            * **colour** (str): plot fill colour (default is yellow)

            * **size** (tuple): plot size (default is (16, 7))

            * **adjustment_dict** (dict): plot adjustments for plt.subplots_adjust()

    Returns:
        matplotlib Figure and Axes with plotted data
    """
    default_adjustments = {
        "top": 0.875,
        "bottom": 0.085,
        "left": 0.095,
        "right": 0.99,
        "hspace": 0.53,
        "wspace": 0.23
    }

    show_detectors = settings.get("show_detectors", run.loaded_detectors)
    title = settings.get("title", f"Run Number: {run.run_num}\n{run.comment}")
    colour = settings.get("colour", "yellow")
    size = settings.get("size", (16, 7))
    adjustments = settings.get("adjustment_dict", default_adjustments)

    num_plots = len(show_detectors)

    fig, axs = plt.subplots(nrows=num_plots, figsize=size)

    # hack to loop through all axes even if number of subplots == 1
    if num_plots == 1:
        axs = [axs]

    fig.suptitle(title)
    fig.supxlabel("Energy (keV)")

    # sets the correct labels
    if run.normalisation == "counts":
        fig.supylabel("Intensity Normalised to Counts (10^5)")
    elif run.normalisation == "events":
        fig.supylabel("Intensity Normalised to Spills (10^5)")
    else:
        fig.supylabel("Intensity")

    i = 0
    for detector, dataset in run.data.items():
        if detector in show_detectors:
            axs[i].fill_between(dataset.x, dataset.y, step='mid', color=colour)
            axs[i].step(dataset.x, dataset.y, where='mid', color='black', label=f"_{detector}")
            axs[i].set_ylim(0.0)
            axs[i].set_xlim(0.0)
            axs[i].set_title(dataset.detector)
            i += 1

    # Adjustments
    plt.subplots_adjust(**adjustments)
    return fig, axs