"""SQLite helpers: read-only connections for the web app and a validated, atomic export for initial.py."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

TABLE = "maniax"

# Columns read by app.py and the frontend.
REQUIRED_COLUMNS = {
    "index",
    "name",
    "maker",
    "siteId",
    "type",
    "ageCategory",
    "tags",
    "options",
    "registDate",
    "dlCount",
    "rate",
    "rateCount",
    "reviewCount",
}

_SCALAR_TYPES = (str, int, float, bytes, bool, np.integer, np.floating, np.bool_, pd.Timestamp, datetime, date)


@contextmanager
def connect_readonly(path: Path) -> Iterator[sqlite3.Connection]:
    """Open the database read-only and always close it; fails instead of creating an empty file."""
    conn = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True)
    try:
        yield conn
    finally:
        conn.close()


def serialize_nested(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert dict/list/tuple cells to JSON text and check that every remaining value can be stored by sqlite3.

    Raises
    ------
    ValueError
        If a cell holds a type that sqlite3 cannot bind, naming the column, row and type.
    """
    df = df.copy()
    for column in df.columns:
        if df[column].dtype != "object":
            continue

        nested = df[column].map(lambda value: isinstance(value, (dict, list, tuple)))
        if nested.any():
            print(f"Serializing nested values in column {column!r} to JSON.")
            df[column] = df[column].map(
                lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list, tuple)) else value
            )

        unsupported = df[column].map(lambda value: not (value is None or isinstance(value, _SCALAR_TYPES)))
        if unsupported.any():
            row = unsupported.idxmax()
            raise ValueError(
                f"Column {column!r} has a value of unsupported type {type(df.at[row, column]).__name__} "
                f"(first at row {row!r}, {int(unsupported.sum())} rows affected)."
            )
    return df


def validate_database(path: Path, expected_rows: int) -> None:
    """Raise ValueError if the exported database is corrupt, incomplete or missing required columns."""
    with connect_readonly(path) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"Integrity check failed: {integrity}")

        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({TABLE})")}
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        rows = conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
        if rows != expected_rows:
            raise ValueError(f"Expected {expected_rows} rows but found {rows}.")


def export_works(df: pd.DataFrame, path: Path) -> Path | None:
    """
    Write `df` to a temporary database, validate it, then atomically replace `path`.

    The previous database is kept as `<name>.bak` next to it, overwriting any older backup.
    If anything fails, the temporary file is removed and the existing database is left untouched.

    Returns
    -------
    Path | None
        The backup path, or None if there was no previous database.
    """
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    backup = path.with_name(path.name + ".bak")
    tmp.unlink(missing_ok=True)

    try:
        df = serialize_nested(df)
        conn = sqlite3.connect(tmp)
        try:
            df.to_sql(TABLE, conn, if_exists="replace")
            conn.commit()
        finally:
            conn.close()
        validate_database(tmp, expected_rows=len(df))
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

    if path.exists():
        os.replace(path, backup)
        os.replace(tmp, path)
        return backup
    os.replace(tmp, path)
    return None
