from scipy.signal import find_peaks
from scipy.signal import find_peaks_cwt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def meanfilter(data: np.ndarray | list, filter_size: int = 9) -> np.ndarray:
    """
    Applies mean pass filter using np.convolve() by convolving ``data`` and ``np.ones(filter_size)/filter_size``

    Args:
        data: input array
        filter_size: size of filter array for convolution

    Returns:
        Copy of data with mean filter applied
    """
    return np.convolve(data, np.ones(filter_size) / filter_size, mode="same")


# Keith's peak finder
def findpeak_with_bck_removed(
    x: np.ndarray, y: np.ndarray, h: float, t: float, d: float
) -> tuple[tuple[np.ndarray, dict], np.ndarray]:
    """
    Filters out background signal using a mean pass filter and calls SciPy's find_peaks() method on filtered signal.

    Args:
        x: input x-data
        y: input y-data
        h: height threshold
        t: threshold for number of peaks within region
        d: minimum distance between peaks

    Returns:
        SciPy find_peaks() result and ndarray of the x-values where peaks were detected.
    """
    spectrum = y

    FSIZE = 20
    NFILTER = 9
    HIGH_CLIP = 25

    ## Create smooth backgroud
    rough_base = meanfilter(spectrum, FSIZE)
    for i in range(NFILTER):
        rough_base = meanfilter(rough_base, FSIZE)

    ## Subtract from main signal result smooth1
    smooth1 = spectrum - rough_base

    ## Look for points in smooth1 more than MAX_HEIGHT -> convert to NaN
    cond_high_clip = smooth1 > HIGH_CLIP
    clipped = np.where(cond_high_clip, np.nan, spectrum)

    ## Interpolate between dropped points
    interpd = pd.Series(clipped).interpolate().tolist()

    ## Get baseline from the interpd signal
    rough_base = meanfilter(interpd, FSIZE // 2)
    for i in range(NFILTER):
        rough_base = meanfilter(interpd, FSIZE // 2)

    ## Subract rough_base from spectrum to get a backgroud removed signal
    bg_removed = meanfilter(spectrum - rough_base, FSIZE // 10)

    ## Pick peaks on bg removed signal - scipy method
    peaks = find_peaks(bg_removed, h, t, d)

    """strong_pos, params = find_peaks(bg_removed, height=10)
    peaks = np.zeros(shape=len(spectrum))
    peaks[pos] = 30
    strong_peaks = np.zeros(shape=len(spectrum))
    strong_peaks[strong_pos] = 50"""

    peak_pos = x[peaks[0]]

    return peaks, peak_pos


def findpeaks(
    x: np.ndarray, y: np.ndarray, h: float, t: float, d: float
) -> tuple[tuple[np.ndarray, dict], np.ndarray]:
    """
    Wrapper for SciPy's find_peaks() method.

    Args:
        x: input x-data
        y: input y-data
        h: height threshold
        t: threshold for number of peaks within region
        d: minimum distance between peaks

    Returns:
        SciPy find_peaks() result and ndarray of the x-values where peaks were detected.
    """
    peaks = find_peaks(y, height=h, threshold=t, distance=d)
    peak_pos = x[peaks[0]]

    return peaks, peak_pos


def FindPeaksCwt(x, y, h, t, d):
    # peaks = find_peaks(y,height=h,threshold = t, distance = d)
    peaks = find_peaks_cwt(y, [h])
    # height = peaks[1]['peak_heights']
    height = y[peaks]
    # peak_pos = x[peaks[0]]
    peak_pos = x[peaks]

    figx = plt.figure()
    axx = figx.subplots()
    axx.plot(x, y)
    axx.scatter(peak_pos, height, color="r", s=40, marker="X", label="peaks")

    # plt.show()
    return [peaks], [peak_pos]
