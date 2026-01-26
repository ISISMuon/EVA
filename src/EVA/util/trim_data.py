import numpy as np


def Trimdata(
    x: np.ndarray, y: np.ndarray, e_min: float, e_max: float
) -> tuple[np.ndarray, np.ndarray]:
    """

    Args:
        x: input x-data
        y: input y-data
        e_min: start energy
        e_max: stop energy

    Returns:
        Trimmed x- and y-data

    Trims the desired x and y arrays to be within the desired x-values e_min and e_max.
    """
    # Trim data for fitting
    resmin = np.where(x > e_min)[0]
    resmax = np.where(x > e_max)[0]
    datax = x[resmin[0] : resmax[0]]
    datay = y[resmin[0] : resmax[0]]

    return datax, datay
