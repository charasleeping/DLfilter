import numpy as np
import pytest
import torch

from module.utils import cos_sim


def test_cos_sim_matches_numpy():
    rng = np.random.default_rng(1)
    query = rng.standard_normal(16).astype(np.float32)
    works = rng.standard_normal((50, 16)).astype(np.float32)

    expected = works @ query / np.linalg.norm(works, axis=1) / np.linalg.norm(query)
    result = cos_sim(torch.from_numpy(query), torch.from_numpy(works))

    assert result.shape == (50,)
    np.testing.assert_allclose(result.numpy(), expected, rtol=1e-5, atol=1e-6)


def test_cos_sim_matches_sentence_transformers():
    util = pytest.importorskip("sentence_transformers.util")
    query = torch.randn(32)
    works = torch.randn(100, 32)
    assert torch.equal(cos_sim(query, works), util.cos_sim(query, works)[0])
