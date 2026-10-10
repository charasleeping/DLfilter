# Work database
The directory structure of the database is as follows:
```
DLfilter
├── **database**
│   ├── dates_table.json
│   ├── genre_table.json
│   ├── genre_vec.pkl
│   ├── title_table.json
│   ├── translation_table.json
│   ├── workformat.json
│   ├── works.sqlite
│   └── works_table.json
...
```
> These files are not included in the repository. You need to build or download them yourself.
>
> Please note that `dates_table.json` and `works_table.json` are not necessary files, but they are required if you want to build your own database.

## Management
### Initialize database
A work database is required for DLfilter to run. 

For first-time users, you can directly download the pre-built database from **[Mega](https://mega.nz/file/rk4CVbrK#sfJd5F5RX-7wlQjq7PTS4aW5FhmHBKDyc0-HNvG3Jqk)** (latest update: 2026-10-10; original works from 2000-01-01 with their Japanese titles only, ~190 MB, decompressed ~1.2 GB). Please extract the files to `DLfilter/database`, or install the zip with `python -m module.fetch_database --file <zip>`. It is the same file the launchers and `python -m module.fetch_database` download by default. It has no translated works or translated titles, and no raw catalogue (`works_table.json`), so it cannot be updated with `initial.py -u`, nor extended with [translations](#translated-editions): build your own with `initial.py -i` for that.

If you want to build your own database, please execute `initial.py -i` for initialization. Please make sure that you have installed all the dependencies in your environment, including the `update` extra:
```bash
cd DLfilter
uv sync --extra update             # or: pip install -r requirements.txt
```
Then
```bash
uv run python initial.py -i        # or: python initial.py -i
```
The program will ask the date range of the works you want to collect. Please input the date or a date range in the format of `YYYY-MM-DD`. For example, 
- `2022-01-01` or
- `2022-01-01 2022-01-31` (separated by a space)

The program will automatically crawl the works from DLsite in the given date range and store them in the database. Failed requests are retried a few times with increasing delays.

At the first time you create the database, the program will download the language model for calculating genre embeddings. This may take a while. The default model is [sonoisa/sentence-luke-japanese-base-lite](https://huggingface.co/sonoisa/sentence-luke-japanese-base-lite). You can change it by adding the `--model model_name` argument (or setting `DLFILTER_MODEL`) to use models available on [Hugging Face](https://huggingface.co/models).

To work offline, pass a local copy of the model instead of a name, and stop Hugging Face from going online:
```bash
HF_HUB_OFFLINE=1 python initial.py -u --model /path/to/sonoisa_sentence-luke-japanese-base-lite
```
The default model needs `transformers` 4.x; version 5 cannot load its tokenizer, so the lockfile pins `transformers<5`. Run `python -m module.doctor --model` to check that the model loads.

### Saving the database safely
`works.sqlite` is written to `works.sqlite.tmp` first and checked (integrity, required columns, row count). Only then is the old file renamed to `works.sqlite.bak` and the new one moved into place. If anything fails, the old database is left untouched.
- Stop the server before exporting, so the file is not replaced while it is being read.
- Keep free disk space of about twice the size of `works.sqlite` (the new file and the backup exist at the same time).
- To roll back, stop the server and rename `works.sqlite.bak` to `works.sqlite`.

### Update database
If you already have a database, you can update it by executing `initial.py -u` to the latest date:
```bash
python initial.py -u
```
Assuming today is 2022-01-01, and the previous database only contains works up to 2021-12-01, then the program will automatically crawl the works from 2021-12-02 to 2022-01-01 to the database. Running `-u` again on the same day crawls yesterday's works once more, which refreshes their counts.

If you need to update the database to a specific date, you can use the `-d` or `--date` argument:
```bash
# Update the works released on 2022-01-01
python initial.py -d 2022-01-01

# Update the works released from 2022-01-01 to 2022-01-31
python initial.py -d 2022-01-01 2022-01-31
```
A `-d` range longer than 31 days asks for confirmation first, as crawling it takes a long time.

After the dates, `-u` and `-d` ask which translations to fetch too (see below). Name the languages after the command (`-u EN TC`, `-d 2022-01-01 EN`) to skip that question, use `NONE` or `JA` for originals only, or pass `-s` to skip every question.

### Translated editions
> **Warning**: fetching translations takes a long time. A first run with `EN TC SC` can take several hours, because DLsite is asked about one work at a time and refuses clients that go too fast. Start with `-k titles` or `--limit`; it can be interrupted and resumed, and later updates only look up new works.

The daily work lists hold only the Japanese title of each work. The official English, Traditional Chinese and Simplified Chinese titles are collected separately, so that works can be found by them. Choose the languages by listing them after `-u` or after the dates of `-d`:
```bash
python initial.py -u                  # asks for languages after the dates
python initial.py -u EN TC SC         # originals, then all three translations
python initial.py -u EN -k titles     # only English titles of multi-language works (fast)
python initial.py -u NONE             # originals only, no question
python initial.py -d 2022-01-01 2022-01-31 EN TC
python initial.py -u EN --limit 500 --workers 4
```
`JA` (originals only), `EN`, `TC`, `SC` and `NONE` are accepted, separated by spaces or commas. If the originals are already up to date, `-u` goes straight to the translations, which is how you fetch them for an existing database.

There are two kinds, selected with `-k/--kinds titles editions` (default: both). `titles`: a work that offers several languages under one ID (for example RJ01722990) shows a different title per locale; these titles are recorded in `title_table.json` and stored in the columns `name_ENG`, `name_CHI_HANT` and `name_CHI_HANS`. This is the fast part, about 11,000 requests for a database with 460,000 works. `editions`: a translation published as its own work ID (such as a "[ENG Ver.]" edition) is listed per language and recorded in `translation_table.json`. This is the slow part, tens of thousands of requests on a first run.

The program looks up every work it has not seen before, newest first, with `--workers` parallel requests (default 6) and at most `--rate` requests per second in total (default 4; DLsite refuses clients that go much faster, so raise it with care). The listing pages used to find editions are fetched at most once per second. Progress bars show the speed and the remaining time. If DLsite answers with HTTP 403 or 429, every request pauses (30 seconds, doubling each time) and the speed is halved for the rest of the run, and the run stops with a message after five failures; wait a while and rerun. Interrupt it at any time (Ctrl-C); a rerun resumes. After an interrupt or a failure it offers to rebuild `works.sqlite` from what is saved so far (with `-s` it just does; without a terminal it does not). You can also rebuild later with `python initial.py -u NONE --no_genre`, which needs no crawling. `works.sqlite` is also rebuilt when the originals were updated, so a run with `--limit` already makes the collected titles searchable.

An edition with its own work ID is stored as its own row that copies its original work (genres, rating, download count, description) and has its own ID, title, circle, release date and options. It is added only if its original work is in the database.

The search results show a switch on cards that matched through a translated title, to read the original title instead. Databases built before this feature work as before, without the switch.

### Remove data
`-r/--remove` deletes data after showing what will go and asking for confirmation (default: no):
```bash
python initial.py -r EN SC   # translations in English and Simplified Chinese, then rebuild the database
python initial.py -r ALL     # delete works.sqlite, that is, every work
python initial.py -r         # asks what to remove
```
`-r ALL` keeps `works.sqlite.bak`, the raw catalogue, the genre files and the translation tables, so the database can be rebuilt with `-u`. Original works cannot be removed on their own (`-r JA` is refused), because translated rows depend on them.

### Checking the dates
`-c/--check` prints the dates recorded in the catalogue and exits. It was `-s/--show` before; `-s/--skip` now answers every question with the default, which is needed when there is no terminal, for example in the Docker `update` job.

### Advanced usage
Use `-h` or `--help` argument to see all the available arguments:
```bash
python initial.py -h
```
```
usage: initial.py [-h] (-i | -c | -u [LANG ...] | -d DATE|LANG [DATE|LANG ...] | -r [TARGET ...])
       [-k {titles,editions} ...] [-s] [--path PATH]
       [--workers WORKERS] [--rate RATE] [--limit LIMIT] [--model MODEL] [--no_genre] [--raw_only]
```

## Database files description
Here are the descriptions of the files in the database directory.
- `dates_table.json`: records the time when each work was crawled. Use for calculating the time for next crawling. The structure is as follows:
```json
{
    "2000-01-01": "2022-01-01 00:00:00",
}
```
where `2000-01-01` is the release date of the work, and `2022-01-01 00:00:00` is the time when the work was crawled.

- `genre_table.json`: records the ID, name, count, and category of all the genres. The structure is as follows:
```json
{
       "509": {
       "category": {
              "ja_JP": "こだわり/アピール",
              ...
       },
       "name": {
              "ja_JP": "3D作品",
              ...
       },
       "count": 12714
       }
}
```
where `509` is the ID of the genre, `category` is the category of the genre, `name` is the name of the genre, and `count` is the number of works in the genre. The `category` and `name` have multiple languages, and should be specified by the language code (e.g., `ja_JP`). Please also refer to [module.dlsite.GenreCatalog](../module/dlsite.py).

- `genre_vec.pkl`: records the genre embeddings. 
- `title_table.json`: records the official translated titles of works that offer several languages under one ID, keyed by work ID: `{"ENG": "...", "CHI_HANT": null}`. `null` means the title is the same as the Japanese one.
- `translation_table.json`: records the translated editions found by `initial.py -u EN TC SC`, keyed by the edition's work ID: `lang` (`ENG`, `CHI_HANT` or `CHI_HANS`), `originalWorkno`, `originalLang`, and the edition's `name`, `maker`, `makerId`, `registDate`, `options` and `siteId`. Works that are not editions are recorded as `{"lang": null}` so that they are not looked up again.
- `workformat.json`: records the ID, name, and father category of all the work formats. The structure is as follows:
```json
{
       "ACN": {
       "category": { 
              "ja_JP": "ゲーム",
              ...
       },
       "name": {
              "ja_JP": "アクション",
              ...
       }
       }
}
```
where `ACN` is the ID of the work format, `category` is the father category of the work format, and `name` is the name of the work format. The `category` and `name` have multiple languages, and should be specified by the language code (e.g., `ja_JP`). 

- `works.sqlite`: the SQLite database file, which stores the metadata of the works for searching. Both the similarity search and the title / circle / RJ ID search read it; the latter only knows the works collected here (DLsite `maniax`, up to the last update).
  Edition rows add the optional columns `lang`, `originalWorkno`, `originalLang` and `originalName`, which are NULL for all other works. The optional columns `name_ENG`, `name_CHI_HANT` and `name_CHI_HANS` hold the translated titles of multi-language works.
- `works_table.json`: records the complete metadata of all works. Not recommended to open directly because of the large size of the data.