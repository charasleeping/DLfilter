"""Opt-in: DLFILTER_MODEL_PATH=/path/to/model uv run pytest -m model"""

import os
import pickle

import numpy as np
import pytest

pytestmark = pytest.mark.model


def test_model_matches_stored_genre_vectors():
    model_path = os.environ.get("DLFILTER_MODEL_PATH")
    vectors_path = os.environ.get("DLFILTER_GENRE_VEC")
    if not model_path:
        pytest.skip("DLFILTER_MODEL_PATH is not set")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_path, device="cpu")
    embedding = model.encode(["テスト"])
    assert embedding.shape == (1, 768)
    assert np.isfinite(embedding).all()

    if vectors_path:
        import json

        with open(vectors_path, "rb") as f:
            vectors = pickle.load(f)
        with open(os.path.join(os.path.dirname(vectors_path), "genre_table.json"), encoding="utf-8") as f:
            genres = json.load(f)
        for genre_id in list(vectors)[:20]:
            parts = genres[genre_id]["name"]["ja_JP"].split("/")
            new = sum(model.encode(parts)) / len(parts)
            old = vectors[genre_id]
            assert np.dot(new, old) / np.linalg.norm(new) / np.linalg.norm(old) > 0.9999
