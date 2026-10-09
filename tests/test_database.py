import json
import sqlite3

import pandas as pd
import pytest
from conftest import WORKS, write_works_db

from module.database import connect_readonly, export_works, serialize_nested


def works_frame(rows=WORKS[:5]):
    df = pd.DataFrame(rows).set_index("index")
    df["registDate"] = pd.to_datetime(df["registDate"])
    return df


def test_serialize_nested_to_json():
    df = works_frame()
    df["creatorBys"] = [["作者A"], None, {"k": "値"}, ("x", 1), "plain"]
    out = serialize_nested(df)
    assert json.loads(out.iloc[0]["creatorBys"]) == ["作者A"]
    assert out.iloc[0]["creatorBys"] == '["作者A"]'
    assert json.loads(out.iloc[2]["creatorBys"]) == {"k": "値"}
    assert out.iloc[3]["creatorBys"] == '["x", 1]'
    assert out.iloc[4]["creatorBys"] == "plain"
    assert pd.isna(out.iloc[1]["creatorBys"])


def test_serialize_rejects_unsupported_values():
    df = works_frame()
    df["bad"] = [object(), None, None, None, None]
    with pytest.raises(ValueError, match="'bad'.*object.*RJ01000001"):
        serialize_nested(df)


def test_export_creates_database(tmp_path):
    path = tmp_path / "works.sqlite"
    assert export_works(works_frame(), path) is None
    with connect_readonly(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM maniax").fetchone()[0] == 5
        assert conn.execute("SELECT name FROM maniax WHERE [index] = 'RJ01000001'").fetchone()[0] == "魔法少女の冒険"
    assert not (tmp_path / "works.sqlite.tmp").exists()


def test_export_replaces_and_keeps_backup(tmp_path):
    path = tmp_path / "works.sqlite"
    write_works_db(path, WORKS[:2])
    backup = export_works(works_frame(), path)
    assert backup == tmp_path / "works.sqlite.bak"
    with connect_readonly(backup) as conn:
        assert conn.execute("SELECT COUNT(*) FROM maniax").fetchone()[0] == 2
    with connect_readonly(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM maniax").fetchone()[0] == 5


def test_failed_export_keeps_existing_database(tmp_path):
    path = tmp_path / "works.sqlite"
    write_works_db(path, WORKS[:2])
    before = path.read_bytes()

    with pytest.raises(ValueError, match="Missing required columns"):
        export_works(works_frame().drop(columns=["maker"]), path)

    assert path.read_bytes() == before
    assert not (tmp_path / "works.sqlite.tmp").exists()
    assert not (tmp_path / "works.sqlite.bak").exists()


def test_readonly_connection_does_not_create_files(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        with connect_readonly(tmp_path / "missing.sqlite"):
            pass
    assert not (tmp_path / "missing.sqlite").exists()
