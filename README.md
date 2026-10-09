# DLfilter
English | [正體中文](README.zh-tw.md)

Tag semantic-driven search engine for DLsite works. 
> Demo: [https://dlfilter.moe/](https://dlfilter.moe/) 
> (may be offline at any time)

DLfilter aims to provide a better experience for searching works on DLsite.
It enables users to find works with similar genre through word embedding of DLsite tags (genres, e.g. `Healing`, `Totally Happy`).

See [here](docs/description.md) for the full description of the project.

DLfilter is a side project for my *personal* use and for learning purpose. I may not be able to maintain it regularly. Sorry. Please feel free to fork or PR.

## Table of Contents
[Features](#features) | [Installation](#installation) | [Usage](#usage) | [Roadmap](#roadmap) | [Known issues](#known-issues)

## Features
DLfilter provides the following features that are **not available** on DLsite:
- Search works by similar genres
- Search similar works for a given work
- Weightable genres by popularity
- Weightable search results by download count and release date

It can also find works in its local database by title, circle name or RJ ID, and start a similarity search from any result.

DLfilter *cannot* search works by popularity as it requires real-time update of the database, which is not possible (obviously I don't have the access to DLsite's database). But - I believe - what's popular is not always what you want. 

## Installation
The following instructions are for people who want to deploy on their own service (especially when my demo is down).
If you just want to use DLfilter, please visit [https://dlfilter.moe/](https://dlfilter.moe/).

Python 3.11 – 3.14 is supported (tested on Linux, macOS and Windows).

1. Clone the repository:
```bash
git clone https://github.com/snowmeow2/DLfilter
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
> The pre-built database is updated to 2023-07-10. You may want to [update it by yourself](docs/database.md#update-database) later.

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
| `DLFILTER_HOST` | `127.0.0.1` | Address `python app.py` listens on |
| `DLFILTER_PORT` | `8000` | Port `python app.py` listens on |
| `DLFILTER_MODEL` | `sonoisa/sentence-luke-japanese-base-lite` | Embedding model for `initial.py`: a Hugging Face ID or a local directory |

### Docker
The image serves an existing database; it does not download or crawl anything on startup.
```bash
docker compose up -d               # mounts ./database read-only, serves http://localhost:8000/
```
To update the database in a container with a local copy of the model, see the `update` service in [compose.yaml](compose.yaml).

### Tests
```bash
uv run pytest
```
The tests use a small temporary database and do not need the real data or the model.

## Usage
The usage of DLfilter very easy. You can search similar works by **genres** or by **a given work**. As a rule of thumb, works with >70% similarity are usually related.

### Find works by title, circle or RJ ID
Use the **Find works** tab of the search panel. Choose where to search (all, title, circle or RJ ID), pick the age ratings, and press Enter.
- Every word must match. Full-/half-width characters and letter case are ignored.
- An exact RJ ID comes first, then exact titles, then titles starting with the text, then the rest.
- **Find similar** on a result fills in its RJ ID, genres and category in the **Find similar** tab, so you can adjust them and start a similarity search.
- The dice button shows random works with the chosen age ratings. The reset button clears every search and shows the welcome page again.

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
The buttons left of **Search** save and load the RJ ID, genres, categories and advanced options. Presets are JSON files in the `presets/` folder of the project (set `DLFILTER_PRESETS_DIR` to use another folder; the Docker setup keeps them in the `presets` volume). **Load preset** lists that folder and can also open a preset file from anywhere else.

## Roadmap
- [x] ~~Demo website~~
- [] Auto update database
- [] Better UI
- [x] ~~Dockerize~~
- [] Better documentation
- [] Negative search
- [x] ~~Search by title, circle and RJ ID~~
- [] Other scopes in DLsite
- [] Advanced tag weightings
- [] Personalized search
- [] ???

## Known issues
- Genres `おやじ`, `少女コミック`, `少年コミック`, `女性コミック`, `青年コミック` cannot be searched. This is because they don't have localized names in DLsite API. 
- Count for some genres may be incorrect. 