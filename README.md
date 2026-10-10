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
  English | <a href="README.jp.md">日本語</a> | <a href="README.zh-tw.md">正體中文</a> | <a href="README.zh-cn.md">简体中文</a>
</p>

DLfilter embeds DLsite tags (genres, e.g. `Healing`, `Totally Happy`) as words, so it can find works whose genres are *close in meaning* to what you like, even when they share no exact tag. It also searches its local database by title (Japanese, English or Chinese), circle name or RJ ID, and can start a similarity search from any result.

This repository is [charasleeping's](https://github.com/charasleeping/DLfilter) revived fork of [snowmeow2's DLfilter](https://github.com/snowmeow2/DLfilter). The similarity search and the idea are the original author's; this fork keeps it running on current Python and libraries and adds the features listed under [What's new in this fork](#whats-new-in-this-fork).

May not be maintained regularly. Please feel free to fork or PR.

BJ and VJ product IDs are not supported yet; support is planned by the end of November 2026.

## Table of Contents
[Features](#features) | [What's new in this fork](#whats-new-in-this-fork) | [Installation](#installation) | [Usage](#usage) | [HTTP API](#http-api) | [Roadmap](#roadmap) | [Known issues](#known-issues) | [Credits](#credits)

## Features

### Search
| | |
| --- | --- |
| **Find works** | Search the local database by title, circle name or RJ ID. Full-/half-width characters and letter case are ignored, and every word must match. |
| **Find by translated title** | Works are also found by their official English, Traditional Chinese and Simplified Chinese titles. A card found that way has a small switch to read the original title. |
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
| **Translations** | Japanese titles only | Search by official English / Traditional Chinese / Simplified Chinese titles, for works that offer several languages under one ID and for translations with their own ID, with a title switch on the cards. `initial.py -u EN TC SC` collects them |
| **Translation crawl** | None | Parallel lookups with a rate limit that slows down by itself when DLsite answers 403 or 429, progress bars, resumable runs, and an offer to rebuild the database after an interrupt |
| **`initial.py` options** | `-i`, `-s`, `-u`, `-d` | `-c` checks the dates, `-u` can be repeated on the same day, `-r` removes translations or every work, `-u` and `-d` take the languages, `-k` picks the kinds, `-s` skips every question, and `--workers`, `--rate` and `--limit` tune the crawl |
| **Model** | Downloaded on demand | Can run fully offline from a local model folder; `transformers<5` pinned for the default model's tokenizer |
| **Runtime weight** | Imports `sentence-transformers` | The website no longer imports it (cosine similarity is computed with PyTorch); only `initial.py` needs it |
| **Diagnostics** | None | `python -m module.doctor` checks versions, paths, data and, with `--model`, the embedding model |
| **Tests** | None | More than 120 `pytest` tests on a small temporary database, run by GitHub Actions on Linux, macOS and Windows (Python 3.11 - 3.14) |
| **Fixes** | Deprecated Pydantic / FastAPI / pandas calls | Updated for current versions; static files are cache-busted by modification time; error responses no longer leak internal messages |

`recover_works_table_download.py` can also salvage the complete records of a truncated `works_table.json` (for example after an interrupted download) without touching the original file.

## Installation
The following instructions are for deploying DLfilter on your own machine or server.

Python 3.11 – 3.14 is supported (tested on Linux, macOS and Windows).

#### Quick start (release zip)
1. Download `DLfilter-vX.Y.Z.zip` from the [Releases](https://github.com/charasleeping/DLfilter/releases) page and unzip it.
2. Double-click `start.bat` (Windows) or `start.command` (macOS; the first time, right-click it and choose **Open**; on Linux run `./start.command`).

The launcher asks before installing [uv](https://docs.astral.sh/uv/), installs the libraries (about 1 GB on the first run), downloads the pre-built database (original works only, about 470 MB) and opens the website in your browser. It has the original works only (Japanese titles), without translations: to get them yourself, see [Manage the database](#manage-the-database). Set `DLFILTER_DB_URL` to download the database from another place, or run `python -m module.fetch_database --file works-db.zip` to install a zip you already have.

#### From source
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
- Download the pre-built database (latest update: 2026-10-10) from [Mega](https://mega.nz/file/D4Q3jJYR#UrUQep6zSEqHJ0dZh2LUuGOF6YhO4p07YAjtxbRyaXw), then extract the content to `DLfilter/database/` (original works only, ~470 MB, decompressed ~3.8 GB), or install the zip with `python -m module.fetch_database --file <the zip>`
> The download has the original works up to 2026-10-10 with their Japanese titles only, so it has no translated works and no translated-title search. It includes the raw catalogue, so you can update it with `python initial.py -u` and fetch translations with `python initial.py -u EN TC SC` as usual; fetching translations can take a long time, see [Manage the database](#manage-the-database).

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
To update the database in a container with a local copy of the model (no model download), see the `update` service in [compose.yaml](compose.yaml). It runs `initial.py -u -s`, so every question gets its default answer (originals only, no translations).

### Tests
```bash
uv run pytest
```
The tests use a small temporary database and do not need the real data or the model. GitHub Actions runs them on Linux, macOS and Windows with Python 3.11 and 3.14 (and 3.12 and 3.13 on Linux).

## Usage
DLfilter finds works in two ways: by **name** (title, circle or RJ ID, in Japanese, English or Chinese) and by **similarity** (a set of genres or a given work). As a rule of thumb, works with >70% similarity are usually related.

### Start the website
Double-click `start.bat` (Windows) or `start.command` (macOS, Linux), or from the project folder:
```bash
python app.py            # serves http://localhost:8000/
python app.py --open     # also opens it in your browser
uv run python app.py     # the same, when you use uv
```
Set `DLFILTER_HOST` and `DLFILTER_PORT` to listen elsewhere (see [Configuration](#configuration)).

### Find works by title, circle or RJ ID
Use the **Find works** tab of the search panel. Choose where to search (all, title, circle or RJ ID), pick the age ratings, and press Enter.
- Every word must match. Full-/half-width characters and letter case are ignored.
- An exact RJ ID comes first, then exact titles, then titles starting with the text, then the rest.
- **Find similar** on a result fills in its RJ ID, genres and product format in the **Find similar** tab, so you can adjust them and start a similarity search.
- The **dice** button shows random works with the chosen age ratings. The reset button clears every search and shows the welcome page again.

This searches the **local database only**, so it does not know about works released after the last update or works in other DLsite categories (only `maniax` is collected). Results show no similarity score because they are not ranked by similarity.

### Find works by translated title
Works are also found by their official English, Traditional Chinese and Simplified Chinese titles; for example `Interactive Mii` finds `ふれあいミイちゃん`. A card found through a translation shows that title and a small translucent switch at the top right of its thumbnail. Slide it to read the original title instead; its glyph is the one of the language button (A, あ, 繁, 简). The switch does not appear when you searched in the original language.

This needs a database that includes the translations, such as the pre-built one (see [Manage the database](#manage-the-database)). Databases built before this feature keep working, without translated titles.

### By similar genres
> **Important**: The genres added here do *not nessarily* appear in the search results, as they are considered as the "seed" for searching.

Add genres you like. DLfilter will take this as the search query (by averaging the word embedding of the genres you added) and return works with similar genres.

2-6 genres are recommended. Too many or too few genres may not give you the best results.

### By a given work
If you don't know what genres to add, you can search by work. Simply type the RJ ID (e.g. `RJ123456`) and DLfilter will automatically fetch its genres and return similar works.

If the ID is not in the local database, the database may be out of date, the record may be missing, or the work may belong to another DLsite category.

### Filter genres
If you have some genres that must be included/excluded in the results, you can set them in the "Included genres" and "Excluded genres" fields.

Please note that the genres you set here are *not* the genres for searching. They are only used to filter the results.

### Presets
The buttons beside **Search** in the **Find similar** tab save and load the RJ ID, genres, product formats and advanced options. Presets are JSON files in the `presets/` folder of the project (set `DLFILTER_PRESETS_DIR` to use another folder; the Docker setup keeps them in the `presets` volume). **Load preset** lists that folder and can also open a preset file from anywhere else.

### Random picks
Below **Search**, **Random** shows random works that match the filters of the tab you are in, and **Reset** clears everything and returns to the welcome page.

### Language and theme
The round buttons at the top right switch the language (English, Japanese, Traditional Chinese, Simplified Chinese, then back to English) and the light/dark theme. The language button shows the current language and slides to the next one when pressed. Without a saved choice, DLfilter uses your browser's language.

### Manage the database
Run these from the project folder, with `uv run` in front if you use uv. `initial.py` needs the `update` extra (`uv sync --extra update` or `pip install -r requirements.txt`); the launcher scripts do not install it.

> Updating needs the raw catalogue `database/works_table.json` (about 2.6 GB), which the pre-built download includes, so `-u` works right after installing it, and `-u EN TC SC` adds the translations. You only need `python initial.py -i` to build the catalogue yourself; it crawls every day from the start date you enter and takes many hours.

> **Warning**: fetching translations takes a long time. On a first run, one update with `EN TC SC` can take several hours, because DLsite is asked about one work at a time and refuses clients that go too fast, so the default speed is deliberately cautious. Start with `-k titles` or `--limit`, and let it run; it can be interrupted and resumed. Later updates only look up new works and are much shorter.

| What you want | Command |
| --- | --- |
| Download and install the pre-built database | `python -m module.fetch_database` (`--file works-db.zip` installs a zip you already have, `--force` overwrites) |
| Check the setup | `python -m module.doctor` (`--model` also loads the embedding model) |
| Build a database from scratch | `python initial.py -i` (asks for the date range) |
| See which dates are recorded | `python initial.py -c` |
| Update to yesterday | `python initial.py -u` (asks which translations to fetch too) |
| Update, with English and Chinese titles | `python initial.py -u EN TC SC` |
| Update, originals only | `python initial.py -u NONE` |
| Fetch only the fast part of the translations | `python initial.py -u EN TC SC -k titles` |
| Crawl one day | `python initial.py -d 2026-10-01` |
| Crawl a range, with translations | `python initial.py -d 2026-10-01 2026-10-10 EN TC SC` |
| Work in small steps | `python initial.py -u EN --limit 500 --workers 4 --rate 2` |
| Rebuild the database from the saved data | `python initial.py -u NONE --no_genre` |
| Remove translations of some languages | `python initial.py -r EN SC` |
| Remove every work from the database | `python initial.py -r ALL` |
| Run without questions (scripts, Docker) | `python initial.py -u EN TC SC -s`, or `docker compose run --rm update -u EN TC SC -s` |
| Update offline with a local model | `HF_HUB_OFFLINE=1 python initial.py -u --model /path/to/model` |
| Salvage a truncated `works_table.json` | `python recover_works_table_download.py` |

Languages are `JA` (the originals, nothing extra to fetch), `EN`, `TC`, `SC` and `NONE`, separated by spaces or commas. `-u` and `-d` update the originals first, then fetch the translations you named; without any language they ask. With `-d`, write the languages after the dates.

| Option | Meaning |
| --- | --- |
| `-k`, `--kinds` | `titles` (works that offer several languages under one ID, fast) and/or `editions` (translations with their own ID, slow); default: both |
| `-s`, `--skip` | Answer every question with its default (needed without a terminal) |
| `--workers`, `--rate`, `--limit` | Parallel requests (6), requests per second in total (4) and the maximum number of works per run |
| `--path`, `--model`, `--no_genre`, `--raw_only` | Database folder, embedding model, skip the genre update, skip rebuilding `works.sqlite` |

Runs show progress bars, can be interrupted with Ctrl-C and resumed, slow down by themselves when DLsite answers 403 or 429, and offer to rebuild the database after an interrupt. Running `-u` twice on the same day is fine. Stop the website before a rebuild and keep free disk space of about twice the size of `works.sqlite`. See [docs/database.md](docs/database.md) for details.

## HTTP API
The website is a thin client of a JSON API, so you can script against it. Interactive documentation is served at `/docs` while the server runs.

| Endpoint | Description |
| --- | --- |
| `GET /api/info` | Number of works and the last update time of the database |
| `GET /api/locale/{locale}` | Genre and product format names (`en_US`, `ja_JP`, `zh_TW`, `zh_CN`, `ko_KR`) |
| `GET /api/works?rj_id=...` | Details of up to 50 works; unknown IDs are listed in `missing` |
| `GET /api/search` | Title / circle / RJ ID search with age filter and paging; a match through a translated title carries `lang`, `originalName`, `originalLang` and `titleToggle` |
| `GET /api/random` | Random works, optionally with the similarity-search filters |
| `POST /api/similarity` | Similarity search by genres or by a given work |
| `GET /api/presets`, `GET` / `PUT /api/presets/{name}` | List, read and save presets |
