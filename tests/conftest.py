"""Builds a small fixture data directory and points DLFILTER_DATA_DIR at it before the app is imported."""

import json
import os
import pickle
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

LOCALES = ["ja_JP", "en_US", "zh_CN", "zh_TW", "ko_KR"]

GENRES = {"001": 5000, "002": 300, "003": 40, "004": 12000}
WORK_FORMATS = {"MNG": "Manga", "ICG": "CG", "SOU": "Voice"}


def work(index, name, maker, age=1, type_="MNG", tags="#001#002#", date="2024-01-01 00:00:00", **extra):
    row = {
        "index": index,
        "ageCategory": age,
        "sexCategory": 1,
        "inservice": 1,
        "name": name,
        "description": f"Description of {name}",
        "maker": maker,
        "type": type_,
        "price": 1100,
        "tags": tags,
        "siteId": "maniax",
        "options": "#JPN#DLP#",
        "dlCount": 100,
        "rate": 45,
        "reviewCount": 2,
        "registDate": date,
        "rateCount": 10,
    }
    row.update(extra)
    return row


WORKS = [
    work("RJ01000001", "魔法少女の冒険", "星のサークル", tags="#001#002#"),
    work("RJ01000002", "Magic Girl Adventure", "Star Circle", age=3, type_="ICG", tags="#002#003#"),
    work("RJ01000003", "100% Pure Love", "Percent_Works", type_="SOU", tags="#003#"),
    work("RJ01000004", "Ｍａｇｉｃ　Ｆｕｌｌｗｉｄｔｈ", "ＦＷサークル", age=2, tags="#004#"),
    work("RJ01000005", "magic", "Exact Maker", tags="#001#"),
    work("RJ01000006", "Under_score Story", "Plain Maker", tags="#002#", date="2023-05-05 00:00:00"),
    work("RJ123456", "Old Classic", "Legacy Circle", tags="#001#004#", date="2010-03-03 00:00:00"),
] + [work(f"RJ0200{i:04d}", f"Filler {i:02d}", "Bulk Maker", tags="#001#") for i in range(60)]


def write_works_db(path: Path, works: list[dict]) -> None:
    import sqlite3

    df = pd.DataFrame(works).set_index("index")
    df["registDate"] = pd.to_datetime(df["registDate"])
    conn = sqlite3.connect(path)
    try:
        df.to_sql("maniax", conn, if_exists="replace")
    finally:
        conn.close()


def build_data_dir(path: Path) -> None:
    genre_table = {
        gid: {
            "category": {loc: f"Category {loc}" for loc in LOCALES},
            "name": {loc: f"Genre {gid} {loc}" for loc in LOCALES},
            "count": count,
        }
        for gid, count in GENRES.items()
    }
    workformat = {
        fid: {"category": {loc: "Format" for loc in LOCALES}, "name": {loc: name for loc in LOCALES}}
        for fid, name in WORK_FORMATS.items()
    }
    rng = np.random.default_rng(0)
    vectors = {gid: rng.standard_normal(8).astype(np.float32) for gid in GENRES}

    (path / "genre_table.json").write_text(json.dumps(genre_table), encoding="utf-8")
    (path / "workformat.json").write_text(json.dumps(workformat), encoding="utf-8")
    with open(path / "genre_vec.pkl", "wb") as f:
        pickle.dump(vectors, f)
    write_works_db(path / "works.sqlite", WORKS)


DATA_DIR = Path(tempfile.mkdtemp(prefix="dlfilter-test-"))
build_data_dir(DATA_DIR)
os.environ["DLFILTER_DATA_DIR"] = str(DATA_DIR)
PRESETS_DIR = Path(tempfile.mkdtemp(prefix="dlfilter-presets-")) / "presets"
os.environ["DLFILTER_PRESETS_DIR"] = str(PRESETS_DIR)


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    import app

    with TestClient(app.app) as c:
        yield c
