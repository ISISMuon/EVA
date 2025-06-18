import numpy as np

def gaussian(x: np.ndarray, mean: float, sigma: float, intensity: float = 1., offset: float = 0.) -> np.ndarray:
    """
    Calculates a Gaussian function for given input array.

    .. math:: f(x) = \\frac{1}{\sigma\sqrt{2\pi}}\exp{-\\frac{(x-\mu)^2}{2\sigma^2}}

    Args:
        x: x-values to calculate Gaussian for
        mean: mean of Gaussian
        sigma: standard deviation of Gaussian
        intensity: area of Gaussian, defaults is 1
        offset: height intercept, default is 0

    Returns:
        Array of points corresponding to the Gaussian function.
    """

    return (intensity / (sigma * np.sqrt(2 * np.pi))) * np.exp(-(x - mean)**2 / (2 * sigma)**2) + offset

def line(x: np.ndarray, x0: float, x1: float) -> np.ndarray:
    """
    Calculates a linear function for given input array.

    .. math:: f(x) = mx + c

    Args:
        x: Input array to calculate for
        x0: "c", intercept
        x1: "m", gradient

    Returns:
        Array of points corresponding to line function.
    """
    return x0 + x1 * x

def quadratic(x: np.ndarray, x0: float, x1: float, x2: float) -> np.ndarray:
    """
    Calculates a quadratic function for given input array.

    .. math:: f(x) = ax^2 + bx + c

    Args:
        x: Input array to calculate for
        x0: "c", 0th degree coefficient
        x1: "b", 1st degree coefficient
        x2: "a", 2nd degree coefficient

    Returns:
        Array of points corresponding to quadratic function.
    """

    return x0 + x1 * x + x2 * x * x