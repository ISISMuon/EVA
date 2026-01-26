import numpy as np


# Normalisation by 100000 counts
def normalise_counts(ydata: np.ndarray) -> np.ndarray:
    """
    Normalise data to 10,000 counts.

    Args:
        ydata: input array
    Returns:
        Normalised array

    """
    return ydata / np.sum(ydata) * pow(10, 5)


def normalise_events(ydata: np.ndarray, spills: int) -> np.ndarray:
    """
    Normalise data by number of spill events in comment.dat file.

    Args:
        ydata: input array
        spills: number of spill events

    Returns:
        Normalised array

    Raises:
        ValueError:  If spills is empty (not loaded)
    """
    return ydata / spills * pow(10, 5)
