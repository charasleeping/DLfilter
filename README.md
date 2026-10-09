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

DLfilter *cannot* search works by popularity as it requires real-time update of the database, which is not possible (obviously I don't have the access to DLsite's database). But - I believe - what's popular is not always what you want. 

## Installation
The following instructions are for people who want to deploy on their own service (especially when my demo is down).
If you just want to use DLfilter, please visit [https://dlfilter.moe/](https://dlfilter.moe/).

Python 3.10 is required. 

1. Clone the repository:
```bash
git clone https://github.com/snowmeow2/DLfilter
cd DLfilter
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Initialize database. There are two ways to do this:
- Download the pre-built database from **[here](https://drive.google.com/file/d/1Jod-iFufGW3lIyqttlws9hOqK4k79ha8/view?usp=sharing)** and extract the content to `DLfilter/database/` (~130 MB, decompressed ~1 GB)
> The pre-built database is updated to 2023-07-10. You may want to [update it by yourself](docs/database.md#update-database) later.

- Initialize the database by yourself. See [here](docs/database.md#initialize-database) for the instructions.

1. Start the server
```bash
uvicorn app:app --port 8000
```
You should be able to access the website at `http://localhost:8000/`.

## Usage
The usage of DLfilter very easy. You can search similar works by **genres** or by **a given work**. As a rule of thumb, works with >70% similarity are usually related.

### By similar genres
> **Important**: The genres added here do *not nessarily* appear in the search results, as they are considered as the "seed" for searching.

Add genres you like. DLfilter will take this as the search query (by averaging the word embedding of the genres you added) and return works with similar genres.

2-6 genres are recommended. Too many or too few genres may not give you the best results.

![image](docs/images/usage1.png)

### By a given work
If you don't know what genres to add, you can search by work. Simply type the work ID (e.g. `RJ123456`) and DLfilter will automatically fetch its genres and return similar works.

![image](docs/images/usage2.png)

### Filter genres
If you have some genres that must be included/excluded in the results, you can set them in the "Included genres" and "Excluded genres" fields.

![image](docs/images/usage3.png)

Please note that the genres you set here are *not* the genres for searching. They are only used to filter the results.

## Roadmap
- [x] ~~Demo website~~
- [] Auto update database
- [] Better UI
- [] Dockerize
- [] Better documentation
- [] Negative search
- [] Search by keywords and artists
- [] Other scopes in DLsite
- [] Advanced tag weightings
- [] Personalized search
- [] ???

## Known issues
- Genres `おやじ`, `少女コミック`, `少年コミック`, `女性コミック`, `青年コミック` cannot be searched. This is because they don't have localized names in DLsite API. 
- Count for some genres may be incorrect. 