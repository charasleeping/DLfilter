"""Search presets, saved as one JSON file per preset in the presets folder."""

import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MAX_PRESETS = 200
# Letters (any script), digits, spaces, `-` and `_`: no dots or slashes, so a name cannot leave the folder.
NAME = re.compile(r"^[\w\- ]{1,60}$")

GenreId = Annotated[str, StringConstraints(pattern=r"^[0-9]{3}$")]
CategoryId = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{3}$")]
GenreList = Annotated[list[GenreId], Field(max_length=100)]


class TooManyPresets(Exception):
    pass


class SliderOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    value: int = Field(ge=0, le=100)


class Preset(BaseModel):
    """The RJ ID, genres, categories and advanced options of the similarity search."""

    model_config = ConfigDict(extra="forbid")

    rj_id: Annotated[str, StringConstraints(pattern=r"^(?:RJ(?:\d{8}|\d{6}))?$")] = ""
    genres: GenreList = []
    included_genres: GenreList = []
    excluded_genres: GenreList = []
    categories: Annotated[list[CategoryId], Field(max_length=100)] = []
    popularity_weight: SliderOption = SliderOption(value=1)
    release_date: SliderOption = SliderOption(value=5)
    download_count: SliderOption = SliderOption(value=50)
    ages: Annotated[list[bool], Field(min_length=3, max_length=3)] = [False, False, True]
    excluded_contents: Annotated[list[bool], Field(min_length=5, max_length=5)] = [True] * 5
    advanced_options_open: bool = False


def valid_name(name: str) -> bool:
    return bool(NAME.match(name)) and name == name.strip()


def list_presets(directory: Path) -> list[dict[str, Any]]:
    """The saved presets, newest first."""
    if not directory.is_dir():
        return []
    presets = []
    for path in directory.glob("*.json"):
        if path.is_file() and valid_name(path.stem):
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            presets.append({"name": path.stem, "modified": modified.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return sorted(presets, key=lambda preset: preset["modified"], reverse=True)


def load_preset(directory: Path, name: str) -> Preset:
    """Raises FileNotFoundError, or ValueError when the file is not a valid preset."""
    return Preset.model_validate_json((directory / f"{name}.json").read_bytes())


def save_preset(directory: Path, name: str, preset: Preset) -> None:
    """Creates or replaces the preset. Raises TooManyPresets when a new one would exceed MAX_PRESETS."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.json"
    if not path.exists() and len(list(directory.glob("*.json"))) >= MAX_PRESETS:
        raise TooManyPresets()

    fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".preset-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(preset.model_dump_json(indent=2))
        os.replace(temp_path, path)
    except BaseException:
        Path(temp_path).unlink(missing_ok=True)
        raise
