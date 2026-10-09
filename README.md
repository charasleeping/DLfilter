<h1 align="center">DLfilter</h1>

<p align="center">
  <b>Find DLsite works by what they feel like, not only by what they are called.</b><br>
  A tag-semantic search engine for DLsite, with a fast local catalogue search, four languages and one-command Docker.
</p>

<p align="center">
  <img alt="Python 3.11 - 3.14" src="https://img.shields.io/badge/python-3.11%20--%203.14-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white">
  <img alt="Docker ready" src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white">
  <img alt="Tests on Linux, macOS and Windows" src="https://img.shields.io/badge/tests-Linux%20%7C%20macOS%20%7C%20Windows-brightgreen">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

<p align="center">
  English | <a href="README.jp.md">日本語</a> | <a href="README.zh-tw.md">正體中文</a> | <a href="README.zh-cn.md">简体中文</a> | <a href="https://dlfilter.moe/">Demo</a>
</p>

> Demo: [https://dlfilter.moe/](https://dlfilter.moe/) (may be offline at any time)

DLfilter embeds DLsite tags (genres, e.g. `Healing`, `Totally Happy`) as words, so it can find works whose genres are *close in meaning* to what you like, even when they share no exact tag. It also searches its local database by title, circle name or RJ ID, and can start a similarity search from any result.

This repository is [charasleeping's](https://github.com/charasleeping/DLfilter) revived fork of [snowmeow2's DLfilter](https://github.com/snowmeow2/DLfilter). The similarity search and the idea are the original author's; this fork keeps it running on current Python and libraries and adds the features listed under [What's new in this fork](#whats-new-in-this-fork).

DLfilter is a side project for *personal* use and for learning purpose. It may not be maintained regularly. Please feel free to fork or PR.

## Table of Contents
[Features](#features) | [What's new in this fork](#whats-new-in-this-fork) | [Installation](#installation) | [Usage](#usage) | [HTTP API](#http-api) | [Roadmap](#roadmap) | [Known issues](#known-issues) | [Credits](#credits)

## Features

### Search
| | |
| --- | --- |
| **Find works** | Search the local database by title, circle name or RJ ID. Full-/half-width characters and letter case are ignored, and every word must match. |
| **Find similar** | Search by a set of genres, or by a given work, ranked by the semantic similarity of their genres. |
| **Random picks** | Draw random works from the database, filtered by the age ratings (and, in the **Find similar** tab, by all its filters). |
| **Find similar from any result** | One click on a result copies its RJ ID, genres and product format into the **Find similar** tab. |

### Tune the results
- Weight genres by popularity (favour niche or popular genres).
- Weight results by download count and release date.
- Include or exclude specific genres, and filter by product format.
- Filter by age ratings and exclude AI-generated, partially AI-generated, low-rated, guro or gay works.

### Comfortable to use
- **Presets**: save your whole search setup (RJ ID, genres, formats, advanced options) and load it later, or open a preset file from anywhere.
- **Four languages** with a one-click language button: English, Japanese, Traditional Chinese and Simplified Chinese. Genre and product format names come from DLsite's official translations, and the labels follow DLsite's own wording.
- **Light and dark themes** with a smooth transition. Both the language and the theme are remembered by the browser.
- Runs on your own machine with a local SQLite database; there is also a Docker setup.

DLfilter *cannot* search works by popularity as it requires real-time update of the database, which is not possible (obviously there is no access to DLsite's database). But - I believe - what's popular is not always what you want.

## What's new in this fork
Compared with [snowmeow2/DLfilter](https://github.com/snowmeow2/DLfilter):

| Area | Original | This fork |
| --- | --- | --- |
| **Search** | Similarity search only | Adds **Find works** (title / circle / RJ ID, ranked), **random picks**, and **Find similar** from any result |
| **Interface** | One search panel; language follows the browser | Tabbed search panel, reset and random buttons, **language switch** (EN / JA / zh-TW / zh-CN, DLsite wording), light/dark theme, presets |
| **Presets** | None | Save, load and import search setups as JSON files (validated, at most 200) |
| **Python** | 3.10 | **3.11 - 3.14** on Linux, macOS and Windows |
| **Dependencies** | Unpinned `requirements.txt` | `pyproject.toml` + `uv.lock` (locked), a generated `requirements.txt` for pip, CPU-only PyTorch on Linux |
| **Running** | `uvicorn app:app` | Also `python app.py`, settings through `DLFILTER_*` environment variables, paths independent of the working directory |
| **Docker** | None | `Dockerfile` and `compose.yaml` (non-root, read-only database, presets volume, optional offline `update` job) |
| **Database safety** | Written in place | Read-only connections for the website; the export is written to a temporary file, checked, and swapped in with a `.bak` backup |
| **Crawling** | Retries forever | Request timeouts, exponential backoff with a limit, confirmation before crawling more than 31 days |
| **Model** | Downloaded on demand | Can run fully offline from a local model folder; `transformers<5` pinned for the default model's tokenizer |
| **Runtime weight** | Imports `sentence-transformers` | The website no longer imports it (cosine similarity is computed with PyTorch); only `initial.py` needs it |
| **Diagnostics** | None | `python -m module.doctor` checks versions, paths, data and, with `--model`, the embedding model |
| **Tests** | None | 75 `pytest` tests on a small temporary database, run by GitHub Actions on Linux, macOS and Windows (Python 3.11 - 3.14) |
| **Fixes** | Deprecated Pydantic / FastAPI / pandas calls | Updated for current versions; static files are cache-busted by modification time; error responses no longer leak internal messages |

`recover_works_table_download.py` can also salvage the complete records of a truncated `works_table.json` (for example after an interrupted download) without touching the original file.

## Installation
The following instructions are for people who want to deploy on their own service (especially when my demo is down).
If you just want to use DLfilter, please visit [https://dlfilter.moe/](https://dlfilter.moe/).

Python 3.11 – 3.14 is supported (tested on Linux, macOS and Windows).

1. Clone the repository:
```bash
git clone https://github.com/charasleeping/DLfilter
cd DLfilter
```

2. Install dependencies. Either with [uv](https://docs.astral.sh/uv/) (recommended, uses the locked versions in `uv.lock`):
```bash
uv sync --extra update     # drop "--extra update" if you only run the website
```
or with pip in a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
The `update` extra (included in `requirements.txt`) is only needed by `initial.py`. On Linux the CPU-only PyTorch build is installed.

3. Initialize database. There are two ways to do this:
- Download the pre-built database from **[here](https://drive.google.com/file/d/1Jod-iFufGW3lIyqttlws9hOqK4k79ha8/view?usp=sharing)** and extract the content to `DLfilter/database/` (~130 MB, decompressed ~1 GB)
> The pre-built database is updated to 2026-10-09. You may want to [update it by yourself](docs/database.md#update-database) later.

- Initialize the database by yourself. See [here](docs/database.md#initialize-database) for the instructions.

4. Check the setup (optional). This prints versions, paths and database status; add `--model` to also load the embedding model offline:
```bash
uv run python -m module.doctor     # or: python -m module.doctor
```

5. Start the server
```bash
uv run python app.py               # or: python app.py
# equivalent: uvicorn app:app --port 8000
```
You should be able to access the website at `http://localhost:8000/`.

### Configuration
All settings are optional environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DLFILTER_DATA_DIR` | `./database` | Directory containing `works.sqlite` and the genre files |
| `DLFILTER_PRESETS_DIR` | `./presets` | Directory where presets are saved |
| `DLFILTER_HOST` | `127.0.0.1` | Address `python app.py` listens on |
| `DLFILTER_PORT` | `8000` | Port `python app.py` listens on |
| `DLFILTER_MODEL` | `sonoisa/sentence-luke-japanese-base-lite` | Embedding model for `initial.py`: a Hugging Face ID or a local directory |

### Docker
The image serves an existing database; it does not download or crawl anything on startup. It runs as a non-root user, mounts `./database` read-only and keeps your presets in a named volume.
```bash
docker compose up -d               # serves http://localhost:8000/ (bound to 127.0.0.1)
```
To update the database in a container with a local copy of the model (no model download), see the `update` service in [compose.yaml](compose.yaml).

### Tests
```bash
uv run pytest
```
The tests use a small temporary database and do not need the real data or the model. GitHub Actions runs them on Linux, macOS and Windows with Python 3.11 and 3.14 (and 3.12 and 3.13 on Linux).

## Usage
The usage of DLfilter very easy. You can search similar works by **genres** or by **a given work**. As a rule of thumb, works with >70% similarity are usually related.

### Find works by title, circle or RJ ID
Use the **Find works** tab of the search panel. Choose where to search (all, title, circle or RJ ID), pick the age ratings, and press Enter.
- Every word must match. Full-/half-width characters and letter case are ignored.
- An exact RJ ID comes first, then exact titles, then titles starting with the text, then the rest.
- **Find similar** on a result fills in its RJ ID, genres and product format in the **Find similar** tab, so you can adjust them and start a similarity search.
- The **dice** button shows random works with the chosen age ratings. The reset button clears every search and shows the welcome page again.

This searches the **local database only**, so it does not know about works released after the last update or works in other DLsite categories (only `maniax` is collected). Results show no similarity score because they are not ranked by similarity.

### By similar genres
> **Important**: The genres added here do *not nessarily* appear in the search results, as they are considered as the "seed" for searching.

Add genres you like. DLfilter will take this as the search query (by averaging the word embedding of the genres you added) and return works with similar genres.

2-6 genres are recommended. Too many or too few genres may not give you the best results.

![image](docs/images/usage1.png)

### By a given work
If you don't know what genres to add, you can search by work. Simply type the RJ ID (e.g. `RJ123456`) and DLfilter will automatically fetch its genres and return similar works.

If the ID is not in the local database, the database may be out of date, the record may be missing, or the work may belong to another DLsite category.

![image](docs/images/usage2.png)

### Filter genres
If you have some genres that must be included/excluded in the results, you can set them in the "Included genres" and "Excluded genres" fields.

![image](docs/images/usage3.png)

Please note that the genres you set here are *not* the genres for searching. They are only used to filter the results.

### Presets
The buttons beside **Search** in the **Find similar** tab save and load the RJ ID, genres, product formats and advanced options. Presets are JSON files in the `presets/` folder of the project (set `DLFILTER_PRESETS_DIR` to use another folder; the Docker setup keeps them in the `presets` volume). **Load preset** lists that folder and can also open a preset file from anywhere else.

### Random picks
Below **Search**, **Random** shows random works that match the filters of the tab you are in, and **Reset** clears everything and returns to the welcome page.

### Language and theme
The round buttons at the top right switch the language (English, Japanese, Traditional Chinese, Simplified Chinese, then back to English) and the light/dark theme. Without a saved choice, DLfilter uses your browser's language.

## HTTP API
The website is a thin client of a JSON API, so you can script against it. Interactive documentation is served at `/docs` while the server runs.

| Endpoint | Description |
| --- | --- |
| `GET /api/info` | Number of works and the last update time of the database |
| `GET /api/locale/{locale}` | Genre and product format names (`en_US`, `ja_JP`, `zh_TW`, `zh_CN`, `ko_KR`) |
| `GET /api/works?rj_id=...` | Details of up to 50 works; unknown IDs are listed in `missing` |
| `GET /api/search` | Title / circle / RJ ID search with age filter and paging |
| `GET /api/random` | Random works, optionally with the similarity-search filters |
| `POST /api/similarity` | Similarity search by genres or by a given work |
| `GET /api/presets`, `GET` / `PUT /api/presets/{name}` | List, read and save presets |
