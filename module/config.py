"""Project paths and settings, resolved independently of the working directory."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("DLFILTER_DATA_DIR") or PROJECT_ROOT / "database").resolve()
DATABASE_PATH = DATA_DIR / "works.sqlite"
PRESETS_DIR = Path(os.environ.get("DLFILTER_PRESETS_DIR") or PROJECT_ROOT / "presets").resolve()
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

# A Hugging Face model ID or a local model directory.
DEFAULT_MODEL = os.environ.get("DLFILTER_MODEL") or "sonoisa/sentence-luke-japanese-base-lite"

HOST = os.environ.get("DLFILTER_HOST") or "127.0.0.1"
PORT = int(os.environ.get("DLFILTER_PORT") or 8000)
