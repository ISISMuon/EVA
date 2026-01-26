import numpy as np


def numpy_rebin(
    x0: np.ndarray, y0: np.ndarray, bin_size: int, bin_range: tuple[float, float] = None
) -> tuple[np.ndarray, np.ndarray]:
    """
    Rebins pre-binned data using numpy's histogram() function. Will use linear interpolation if bin rate is less than 1.

    Args:
        x0: input x-data
        y0: input y-data
        bin_size: bin size, must be positive.
        bin_range: tuple specifying min and max range for binning. If none, full range of x_0 used for range.
    Returns:
        Rebinned data using numpy's 'histogram' function. If binning rate is greater than 1, the data will be rebinned
        according to numpy's 'histogram()'. If binning rate is less than 1, bin positions will be calculated from
        numpy's 'histogram()', while the counts will be linearly interpolated using numpy's 'interp()' to increase
        the number of datapoints.
    """

    # un-histogram the data to re-bin it with numpy
    energies = np.array(
        [x_val for i, x_val in enumerate(x0) for _ in range(int(y0[i]))]
    )

    n_init = len(x0)
    n_bins = int(n_init / bin_size)

    # get the histogram (y-values) and bin edges (x-values) which are of size len(hist) + 1
    hist, bin_edges = np.histogram(energies, n_bins, range=bin_range)

    hist = hist / bin_size

    # center bin edges (drop the last element and shift all bin edges by 0.5x bin width)
    bin_centres = bin_edges[:-1] + (bin_edges[1] - bin_edges[0]) / 2

    # if binning rate is less than 1, linearly interpolate counts instead
    if n_bins > n_init:
        hist = np.interp(bin_centres, x0, y0)

    return bin_centres, hist


def nxs_rebin(x_data: np.ndarray, bin_num: int, bin_range: tuple[float, float] = None):
    """
    Rebin raw data into desired bin sizes.

    Args:
        x0: input xvalues (energy bins)
        y0: input yvalues (counts per bin)
        bin_factor: bin size

    Returns:
        Rebinned data with bin centers for use with matplotlib step plots.
    """
    if range is None:
        counts, bin_edges = np.histogram(x_data, bins=bin_num)
    else:
        counts, bin_edges = np.histogram(x_data, bins=bin_num, range=bin_range)

    bin_centres = bin_edges[:-1] + (bin_edges[1] - bin_edges[0]) / 2
    return bin_centres, counts


def simple_rebin(
    x0: np.ndarray, y0: np.ndarray, bin_factor: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Rebin data into desired bin sizes. Only works for values bin_factor that are factors len(x0).

    Args:
        x0: input xvalues (energy bins)
        y0: input yvalues (counts per bin)
        bin_factor: bin size

    Returns:
        Rebinned data
    """

    init_bins = len(x0)
    rows = int(bin_factor)
    cols = int(init_bins // bin_factor)

    x1 = np.mean(x0.reshape(cols, rows), axis=1)
    y1 = np.sum(y0.reshape(cols, rows), axis=1)

    return x1, y1


def rebin_interpolate(
    x0: np.ndarray, y0: np.ndarray, bin_size: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Rebins data into desired number of points per bin and uses linear interpolation if necessary.

    Args:
        x0: x-values (energy bins)
        y0: y-values (counts per bin)
        bin_size: number of points to put in each bin

    Returns:
        Rebinned data

    Examples:
        Example 1 =========================================================================
        x0 = [0, 1, 2, 3, 4, 5]
        y0 = [10, 20, 30, 30, 20, 30]
        bin_size = 2
        ------------
        Total number of bins: int(6 // 2) = 3
        Required number of points = 3*2 = 6

        Interpolation step:
            In this case nothing happens there is no need to resample the data since there are
            enough points to bin the data perfectly.
            x1 = [0, 1, 2, 3, 4, 5]
            y1 = [10, 20, 30, 30, 20, 30]

        Reshaping and binning step:
            x1 = [0, 1, 2, 3, 4, 5] ->
                [[0, 1],
                [2, 3],
                [4, 5]]

            y1 = [10, 20, 30, 30, 20, 30] ->
                [[10, 20],
                [30, 30],
                [20, 30]]

        Averaging x1 across axis 1 gives [0.5, 2.5, 4.5]
        Summing y1 across axis 1 gives [30, 60, 50]

        Result:
            x1 = [0.5, 2.5, 4.5], y1 = [30, 60, 50]

        Example 2 ========================================================================
        x0 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        y0 = [10, 20, 30, 30, 20, 30, 10, 0, 20, 10]
        bin_size = 3

        Total number of bins: int(10 // 3) = 3 (integer division always rounds down)
        Required number of points: 3*3 = 9

        Interpolation step:
            Need to resample the data from 10 points down to 9.
            x1 is calculated using linspace, y1 is calculated using numpy linear interpolation:
            x1 = [0.0, 1.125, 2.25, 3.375, 4.5, 5.625, 6.75, 7.875, 9.0]
            y1 = [10.0, 21.25, 30.0, 26.25, 25.0, 17.5, 2.5, 17.5, 10.0]

        Reshaping and binning step:
            x1 = [0.0, 1.125, 2.25, 3.375, 4.5, 5.625, 6.75, 7.875, 9.0] ->
                [[0.    1.125 2.25 ]
                [3.375 4.5   5.625]
                [6.75  7.875 9.   ]]

            y1 = [10.0, 21.25, 30.0, 26.25, 25.0, 17.5, 2.5, 17.5, 10.0] ->
                [[10.   21.25 30.  ]
                [26.25 25.   17.5 ]
                [ 2.5  17.5  10.  ]]

            Averaging x1 across axis 1 gives [1.125, 4.5, 7.875]
            Summing y1 across axis 1 gives [61.25, 68.75, 30.0]

        Result:
            x1 = [1.125, 4.5, 7.875], y1 = [61.25, 68.75, 30.0]

    """
    # Calculate number of bins to divide data into (rounds down)
    N_bins = int(len(x0) // bin_size)
    N_total = N_bins * bin_size

    # Re-sample the data into N_total using linear interpolation
    x1 = np.linspace(x0[0], x0[-1], N_total)
    y1 = np.interp(x1, x0, y0)

    # Reshape the data into matrices with the points to be binned together along the columns
    x1_binned = np.mean(
        x1.reshape(N_bins, bin_size), axis=1
    )  # calculate center position of bin
    y1_binned = np.sum(
        y1.reshape(N_bins, bin_size), axis=1
    )  # calculate total count in bin

    return x1_binned, y1_binned


def bin_2d(
    x_data: np.ndarray,
    y_data: np.ndarray,
    num_bin: int,
    range_param: tuple[(tuple[float, float], tuple[float, float])],
):
    # Compute 2D histogram
    H, xedges, yedges = np.histogram2d(
        x_data, y_data, bins=[num_bin, num_bin], range=range_param
    )
    return H, xedges, yedges
