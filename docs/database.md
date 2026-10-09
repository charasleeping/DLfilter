# Work database
The directory structure of the database is as follows:
```
DLfilter
├── **database**
│   ├── dates_table.json
│   ├── genre_table.json
│   ├── genre_vec.pkl
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

For first-time users, you can directly download the pre-built database from **[here](https://drive.google.com/file/d/1Jod-iFufGW3lIyqttlws9hOqK4k79ha8/view?usp=sharing)** (recorded date: 2000-01-01 - 2023-07-10, ~130 MB, decompressed ~1 GB). Please extract the files to `DLfilter/database`.

If you want to build your own database, please execute `initial.py -i` for initialization. Please make sure that you have installed all the dependencies in your environment:
```bash
cd DLfilter
pip install -r requirements.txt
```
Then
```bash
python initial.py -i
```
The program will ask the date range of the works you want to collect. Please input the date or a date range in the format of `YYYY-MM-DD`. For example, 
- `2022-01-01` or
- `2022-01-01 2022-01-31` (separated by a space)

The program will automatically crawl the works from DLsite in the given date range and store them in the database.

At the first time you create the database, the program will download the language model for calculating genre embeddings. This may take a while. The default model is [sonoisa/sentence-luke-japanese-base-lite](https://huggingface.co/sonoisa/sentence-luke-japanese-base-lite). You can change it by adding the `--model model_name` argument to use models available on [Hugging Face](https://huggingface.co/models).

### Update database
If you already have a database, you can update it by executing `initial.py -u` to the latest date:
```bash
python initial.py -u
```
Assuming today is 2022-01-01, and the previous database only contains works up to 2021-12-01, then the program will automatically crawl the works from 2021-12-02 to 2022-01-01 to the database.

If you need to update the database to a specific date, you can use the `-d` or `--date` argument:
```bash
# Update the works released on 2022-01-01
python initial.py -d 2022-01-01

# Update the works released from 2022-01-01 to 2022-01-31
python initial.py -d 2022-01-01 2022-01-31
```

### Advanced usage
Use `-h` or `--help` argument to see all the available arguments:
```bash
python initial.py -h
```
```
usage: initial.py [-h] (-i | -s | -u | -d DATE [DATE ...]) 
       [--path PATH] [--model MODEL] [--no_genre] [--raw_only]
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

- `works.sqlite`: the SQLite database file, which stores the metadata of the works for searching. 
- `works_table.json`: records the complete metadata of all works. Not recommended to open directly because of the large size of the data.