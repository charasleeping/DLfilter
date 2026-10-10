import zipfile

import pytest

from module import fetch_database
from module.fetch_database import REQUIRED_FILES, install_archive, is_installed


def make_zip(path, names, prefix=""):
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(prefix + name, name)
    return path


def test_installs_required_files(tmp_path):
    archive = make_zip(tmp_path / "db.zip", REQUIRED_FILES)
    data_dir = tmp_path / "data"
    names = install_archive(archive, data_dir)
    assert sorted(names) == sorted(REQUIRED_FILES)
    assert is_installed(data_dir)
    assert not list(data_dir.glob("*.tmp"))


def test_accepts_files_inside_a_folder(tmp_path):
    archive = make_zip(tmp_path / "db.zip", REQUIRED_FILES, prefix="database/")
    install_archive(archive, tmp_path / "data")
    assert is_installed(tmp_path / "data")


def test_ignores_unknown_and_unsafe_entries(tmp_path):
    archive = make_zip(tmp_path / "db.zip", [*REQUIRED_FILES, "../evil.txt", "works_table.json"])
    data_dir = tmp_path / "data"
    install_archive(archive, data_dir)
    assert not (tmp_path / "evil.txt").exists()
    assert not (data_dir / "works_table.json").exists()


def test_incomplete_archive_changes_nothing(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "works.sqlite").write_text("old")
    archive = make_zip(tmp_path / "db.zip", REQUIRED_FILES[:2])
    with pytest.raises(ValueError):
        install_archive(archive, data_dir)
    assert (data_dir / "works.sqlite").read_text() == "old"


def test_main_skips_when_installed(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    install_archive(make_zip(tmp_path / "db.zip", REQUIRED_FILES), data_dir)
    monkeypatch.setattr(fetch_database.config, "DATA_DIR", data_dir)
    monkeypatch.setattr("sys.argv", ["fetch_database"])
    assert fetch_database.main() == 0
    assert "already installed" in capsys.readouterr().out
