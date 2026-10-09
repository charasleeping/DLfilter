import numpy as np
import pandas as pd
from scipy.stats import norm


def dlCount_fitting(df: pd.DataFrame) -> tuple[float, float]:
    """
    Fit the download count of the works to a Gaussian distribution.

    Parameters
    ----------
    df : DataFrame
        The DataFrame containing the download count of the works, with the column name 'dlCount'.

    Returns
    -------
    mu : float
        The mean of the Gaussian distribution.
    std : float
        The standard deviation of the Gaussian distribution.
    """

    data = df.dlCount.astype(int)
    data = np.log10(data, where=data > 10)
    mu, std = norm.fit(data)
    return mu, std


def dlCount_weight(weight: int, dlCount: np.ndarray, mu: float, std: float) -> np.ndarray:
    """
    Compute the popularity weight of a work based on its download count, assuming the download count follows a Gaussian distribution.
    The weight is computed by the ratio of the PDF of the download count and the PDF of the download count shifted by sigma.

    Parameters
    ----------
    weight : int
        The weight of popularity.
    dlCount : ndarray
        The download count of the work.
    mu : float
        The mean of the Gaussian distribution.
    std : float
        The standard deviation of the Gaussian distribution.

    Returns
    -------
    weight : ndarray
        The weight of the work.
    """
    dlCount = np.log10(dlCount + 1)
    sigma = 2 / 50 * weight - 2

    raw = norm.pdf(dlCount, mu, std)
    new = norm.pdf(dlCount, mu + sigma, std)
    return np.where(raw > new, new / raw, 1)


def weibull_dist(x: float, a: float, b: float) -> float:
    """
    The Weibull distribution.

    Parameters
    ----------
    x : float
        The x value.
    a : float
        The shape parameter.
    b : float
        The scale parameter.

    Returns
    -------
    y : float
        The y value.
    """
    if 0:
        return 0
    else:
        return (a / b) * (x / b) ** (a - 1) * np.exp(-(x / b) ** a)
