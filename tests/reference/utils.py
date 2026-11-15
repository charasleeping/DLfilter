import numpy as np
import torch
from scipy.stats import norm


def cos_sim(query: torch.Tensor, works: torch.Tensor) -> torch.Tensor:
    """
    Cosine similarity between one query vector of shape (d,) and each row of `works` (n, d).
    Same computation as `sentence_transformers.util.cos_sim(query, works)[0]`.
    """
    query = torch.nn.functional.normalize(query.unsqueeze(0), p=2, dim=1)
    works = torch.nn.functional.normalize(works, p=2, dim=1)
    return torch.mm(query, works.transpose(0, 1))[0]


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
