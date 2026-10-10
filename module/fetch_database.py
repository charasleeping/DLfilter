"""
Download the pre-built database and install it into the data directory.

Usage:
    python -m module.fetch_database                  # download unless the database is already installed
    python -m module.fetch_database --force          # download and overwrite
    python -m module.fetch_database --file db.zip    # install a zip you downloaded yourself

The zip may be fetched from another place with --url or the DLFILTER_DB_URL environment variable.
"""

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

from module import config

# A GitHub release tagged "database" holds this asset, so it does not depend on the code releases.
DEFAULT_URL = "https://github.com/charasleeping/DLfilter/releases/download/database/works-db.zip"
REQUIRED_FILES = ("works.sqlite", "genre_table.json", "workformat.json", "genre_vec.pkl")
OPTIONAL_FILES = ("dates_table.json", "works_table.json")


def is_installed(data_dir: Path) -> bool:
    return all((data_dir / name).is_file() for name in REQUIRED_FILES)


def install_archive(archive: Path, data_dir: Path) -> list[str]:
    """Extract the known database files from `archive` into `data_dir`; anything else in the zip is ignored."""
    data_dir.mkdir(parents=True, exist_ok=True)
    allowed = REQUIRED_FILES + OPTIONAL_FILES
    staged: list[tuple[Path, Path]] = []
    try:
        with zipfile.ZipFile(archive) as zf:
            members = {}
            for info in zf.infolist():
                # Only the base name is used, so a crafted path inside the zip can never leave data_dir.
                name = Path(info.filename).name
                if name in allowed and not info.is_dir():
                    members[name] = info
            missing = [name for name in REQUIRED_FILES if name not in members]
            if missing:
                raise ValueError(f"the archive is missing: {', '.join(missing)}")
            for name, info in members.items():
                tmp = data_dir / f"{name}.tmp"
                staged.append((tmp, data_dir / name))
                with zf.open(info) as src, open(tmp, "wb") as dst:
                    shutil.copyfileobj(src, dst, 1 << 20)
        # Replace only after every file was extracted and verified by its CRC.
        for tmp, final in staged:
            os.replace(tmp, final)
    finally:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)
    return sorted(final.name for _, final in staged)


def download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=(10, 60)) as response:
        response.raise_for_status()
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        last_percent = -1
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    percent = done * 100 // total
                    if percent != last_percent and percent % 5 == 0:
                        print(f"  {percent:3d}% ({done >> 20} / {total >> 20} MB)", flush=True)
                        last_percent = percent


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and install the pre-built DLfilter database.")
    parser.add_argument("--url", default=os.environ.get("DLFILTER_DB_URL") or DEFAULT_URL, help="Where to download the zip from.")
    parser.add_argument("--file", type=Path, help="Install this local zip instead of downloading.")
    parser.add_argument("--force", action="store_true", help="Overwrite an installed database.")
    args = parser.parse_args()

    data_dir = config.DATA_DIR
    if is_installed(data_dir) and not args.force:
        print(f"Database already installed in {data_dir}")
        return 0

    try:
        if args.file:
            names = install_archive(args.file, data_dir)
        else:
            data_dir.mkdir(parents=True, exist_ok=True)
            print(f"Downloading the database from {args.url}")
            with tempfile.TemporaryDirectory(dir=data_dir) as tmp:
                archive = Path(tmp) / "database.zip"
                download(args.url, archive)
                print("Extracting...")
                names = install_archive(archive, data_dir)
    except (requests.RequestException, zipfile.BadZipFile, ValueError, OSError) as e:
        print(f"Could not install the database: {e}", file=sys.stderr)
        print("Download the zip manually and run: python -m module.fetch_database --file <zip>", file=sys.stderr)
        return 1

    print(f"Installed {', '.join(names)} in {data_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
