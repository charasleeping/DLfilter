"""
Print environment and data diagnostics.

Usage:
    python -m module.doctor            # versions, paths, database and genre data
    python -m module.doctor --model    # also load the embedding model offline and check its output
"""

import argparse
import importlib.metadata
import os
import pickle
import platform
import sys

from module import config
from module.database import REQUIRED_COLUMNS, TABLE, connect_readonly

PACKAGES = ["fastapi", "starlette", "uvicorn", "pydantic", "numpy", "scipy", "pandas", "torch"]
UPDATE_PACKAGES = ["sentence-transformers", "transformers", "tokenizers", "sentencepiece", "protobuf", "beautifulsoup4"]


def version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'OK' if ok else '!!'}] {label}{': ' + detail if detail else ''}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="DLfilter diagnostics.")
    parser.add_argument("--model", action="store_true", help="Load the embedding model offline and check its output.")
    args = parser.parse_args()

    print(f"Python {sys.version.split()[0]} on {platform.system()} {platform.machine()}")
    print("Packages:")
    for name in PACKAGES + UPDATE_PACKAGES:
        print(f"  {name}: {version(name)}")

    ok = True
    print("Paths:")
    ok &= check("templates", config.TEMPLATES_DIR.is_dir(), str(config.TEMPLATES_DIR))
    ok &= check("static", config.STATIC_DIR.is_dir(), str(config.STATIC_DIR))
    ok &= check("data directory", config.DATA_DIR.is_dir(), str(config.DATA_DIR))

    print("Database:")
    if check("works.sqlite", config.DATABASE_PATH.is_file(), str(config.DATABASE_PATH)):
        try:
            with connect_readonly(config.DATABASE_PATH) as conn:
                columns = {row[1] for row in conn.execute(f"PRAGMA table_info({TABLE})")}
                missing = REQUIRED_COLUMNS - columns
                ok &= check("required columns", not missing, f"missing {sorted(missing)}" if missing else "")
                rows, latest = conn.execute(f"SELECT COUNT(*), MAX(registDate) FROM {TABLE}").fetchone()
                check("works", rows > 0, f"{rows} rows, latest registDate {latest}")
        except Exception as e:
            ok &= check("open database", False, str(e))
    else:
        ok = False

    print("Genre data:")
    for name in ("genre_table.json", "workformat.json", "genre_vec.pkl"):
        ok &= check(name, (config.DATA_DIR / name).is_file())
    dimension = None
    if (config.DATA_DIR / "genre_vec.pkl").is_file():
        with open(config.DATA_DIR / "genre_vec.pkl", "rb") as f:
            vectors = pickle.load(f)
        dimension = len(next(iter(vectors.values())))
        check("genre vectors", True, f"{len(vectors)} genres, dimension {dimension}")

    if args.model:
        print(f"Model: {config.DEFAULT_MODEL}")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            embedding = SentenceTransformer(config.DEFAULT_MODEL, device="cpu").encode(["テスト"])
            ok &= check("finite output", bool(np.isfinite(embedding).all()), f"shape {embedding.shape}")
            if dimension is not None:
                ok &= check("matches genre vectors", embedding.shape[1] == dimension)
        except Exception as e:
            ok &= check("load model offline", False, f"{type(e).__name__}: {e}")

    print("All checks passed." if ok else "Some checks failed.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
