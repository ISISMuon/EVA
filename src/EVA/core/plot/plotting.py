import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from EVA.core.app import get_app
from EVA.core.data_structures.run import Run
from EVA.core.data_structures.spectrum import Spectrum


def get_ylabel(normalisation: str) -> str:
    """
    Returns the appropriate ylabel for given normalisation
    Args:
        normalisation: normalisation type

    Returns:
        formatted ylabel
    """

    if normalisation == "counts":
        return "Intensity Normalised to Counts (10^5)"
    elif normalisation == "events":
        return "Intensity Normalised to Spills (10^5)"
    else:
        return "Unnormalised Intensity"


def Plot_Peak_Location(
    ax: plt.Axes, x: np.ndarray, y: np.ndarray, peak_indices: np.ndarray
):
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
    ax.scatter(peak_positions, peak_heights, color="r", s=20, marker="X", label="peaks")


def plot_spectrum(
    spectrum: Spectrum, normalisation: str, **settings: dict
) -> tuple[plt.Figure, plt.Axes]:
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
    title = settings.get(
        "title", f"Run Number: {spectrum.run_number} {spectrum.detector}"
    )
    colour = settings.get("colour", "yellow")

    fig, ax = plt.subplots(1)
    fig.suptitle(title)
    fig.supxlabel("Energy (keV)")

    # sets the correct labels
    fig.supylabel(get_ylabel(normalisation))

    ax.fill_between(spectrum.x, spectrum.y, step="mid", color=colour)
    ax.step(
        spectrum.x,
        spectrum.y,
        where="mid",
        color="black",
        label=f"_{spectrum.detector}",
    )
    ax.set_ylim(0.0)
    ax.set_xlim(0.0)

    return fig, ax


def plot_spectrum_residual(
    spectrum: Spectrum, normalisation: str, **settings: dict
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plots a single spectrum (for a single detector) and creates an empty plot to be populated with fit residuals.

    Args:
        spectrum: Spectrum object to plot
        normalisation: Normalisation type - valid options are "counts", "none", "spills"
        **settings:
            * **title** (str): plot title
            * **colour** (str): plot fill colour

    Returns:
        matplotlib Figure and Axes with plotted spectrum and empty Axis for residuals
    """
    title = settings.get(
        "title", f"Run Number: {spectrum.run_number} {spectrum.detector}"
    )
    colour = settings.get("colour", "yellow")

    fig, ax = plt.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    main_ax = ax[0]  # use the first Axes for the spectrum plot
    residual_ax = ax[1]  # use the second Axes for the residuals

    # sets the correct labels
    fig.suptitle(title)
    fig.supylabel(get_ylabel(normalisation))

    main_ax.set_ylabel("Intensity")
    residual_ax.set_ylabel(f"$\\Delta$ Intensity")
    residual_ax.set_xlabel("Energy (keV)")
    residual_ax.grid(True)

    # Plot the spectrum data in main_ax
    main_ax.fill_between(spectrum.x, spectrum.y, step="mid", color=colour)
    main_ax.step(
        spectrum.x,
        spectrum.y,
        where="mid",
        color="black",
        label=f"_{spectrum.detector}",
    )
    main_ax.set_ylim(0.0)
    main_ax.set_xlim(0.0)
    main_ax.tick_params(labelbottom=True)

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
        "wspace": 0.23,
    }

    show_detectors = settings.get("show_detectors", run.loaded_detectors)
    # Format title, if comment data exists include it
    try:
        title = settings.get(
            "title", f"Run Number: {run.run_num} {run.plot_mode}\n{run.comment_data[0]}"
        )
    except AttributeError:
        title = settings.get("title", f"Run Number: {run.run_num} {run.plot_mode}")
    ylabel = settings.get("ylabel", None)
    xlabel = settings.get("xlabel", None)
    colour = settings.get("colour", "white")
    size = settings.get("size", (16, 7))
    adjustments = settings.get("adjustment_dict", default_adjustments)
    num_plots = len(show_detectors)
    fig, axs = plt.subplots(nrows=num_plots, figsize=size)

    # hack to loop through all axes even if number of subplots == 1
    if num_plots == 1:
        axs = [axs]

    fig.suptitle(title)

    if run.plot_mode == "Time Plot":
        fig.supxlabel(" Time (ns)")
    else:
        fig.supxlabel("Energy (keV)")

    # sets the correct labels

    if ylabel is not None:
        fig.supylabel(ylabel)
    else:
        fig.supylabel(get_ylabel(run.normalisation))

    i = 0
    for detector, dataset in run.data.items():
        if detector in show_detectors:
            axs[i].step(
                dataset.x, dataset.y, where="mid", color="black", label=f"_{detector}"
            )
            axs[i].fill_between(dataset.x, dataset.y, step="mid", color=colour)

            axs[i].set_xlim(0.0)
            axs[i].set_ylim((0, 1.2 * np.max(dataset.y)))
            axs[i].set_title(dataset.detector)
            i += 1
    # Adjustments
    plt.subplots_adjust(**adjustments)
    return fig, axs


def replot_run(
    run: Run, fig: plt.Figure, axs: np.ndarray[plt.Axes] | plt.Axes, **settings: dict
):
    # Regenerate title in-case plot mode changed
    try:
        title = settings.get(
            "title", f"Run Number: {run.run_num} {run.plot_mode}\n{run.comment_data[0]}"
        )
    except AttributeError:
        title = settings.get("title", f"Run Number: {run.run_num} {run.plot_mode}")

    fig.suptitle(title)

    fig.supylabel(get_ylabel(run.normalisation))
    if run.plot_mode == "Time Plot":
        fig.supxlabel(" Time (ns)")
    else:
        fig.supxlabel("Energy (keV)")

    if isinstance(axs, plt.Axes):
        axes = [axs]
    elif isinstance(axs, np.ndarray):
        axes = axs.ravel().tolist()
    else:
        axes = axs

    for ax in axes:
        candidates = [
            (line.get_label()[1:], line)
            for line in ax.lines
            if line.get_label()[1:] in run.loaded_detectors
        ]
        if not candidates:
            raise ValueError(
                "No matching lines found in ax.lines with labels matching run.loaded_detectors"
            )

        detector, line = candidates[0]

        xdata = run.data[detector].x
        ydata = run.data[detector].y

        line.set_xdata(xdata)
        line.set_ydata(ydata)

        fill_obj = [
            child
            for child in ax.get_children()
            if isinstance(child, matplotlib.collections.FillBetweenPolyCollection)
        ][0]

        # lastly, re-fill the histogram
        fill_obj.set_data(xdata, 0, ydata)

        if "colour" in settings.keys():
            fill_obj.set_color(settings["colour"])

        ax.set_ylim((0, 1.2 * np.max(ydata)))


def replot_run_residual(
    run: Run,
    fig: plt.Figure,
    axs: np.ndarray[plt.Axes] | plt.Axes,
    fit_result,
    **settings: dict,
):
    replot_run(run, fig, axs[0], **settings)
    if fit_result is not None:
        axs[1].set_ylim(
            -np.max(np.abs(fit_result.residual)) * 1.2,
            np.max(np.abs(fit_result.residual)) * 1.2,
        )
    fig.supylabel(get_ylabel(run.normalisation))
