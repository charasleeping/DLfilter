# 作品資料庫
DLfilter 的作品資料庫目錄結構如下：
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
> 這些檔案並沒有包含在本專案中，您需要自行建立或下載。
> 
> 請注意，`dates_table.json` 與 `works_table.json` 不是必要的檔案，但是如果您希望自行建立資料庫，則需要這兩個檔案。

## 資料庫管理
### 初始化資料庫
DLfilter 需要一個作品資料庫才能開始運作。

初次使用時，您可以直接於 **[這裡](https://drive.google.com/file/d/1Jod-iFufGW3lIyqttlws9hOqK4k79ha8/view?usp=sharing)** 下載預先建立好的資料庫（收錄日期：2000-01-01 - 2023-07-10，約 130 MB，解壓縮後約 1 GB）。下載後，請將檔案解壓縮至 `DLfilter/database` 目錄下。

如果您希望自行建立資料庫，請執行 `initial.py -i` 來初始化資料庫。執行時，請確保您的環境中已經安裝了所需的套件：
```bash
cd DLfilter
pip install -r requirements.txt
```
然後
```bash
python initial.py -i
```
程式會詢問您要收集的日期範圍。請依 `YYYY-MM-DD` 格式輸入您希望的一個或一段日期：
- `2022-01-01` 或 
- `2022-01-01 2022-01-31`（以空格分隔）

程式會自動爬取於該日期範圍內發售的所有作品資料，並建立資料庫。

首次建立資料庫時，程式會自動下載語言模型以建立標籤的詞向量嵌入，這可能需要一些時間。預設使用 [sonoisa/sentence-luke-japanese-base-lite](https://huggingface.co/sonoisa/sentence-luke-japanese-base-lite)。您可以透過增加 `--model model_name` 引數來使用 [Hugging Face](https://huggingface.co/) 上的其他語言模型。

### 更新資料庫
如果您已經有了資料庫，您可以透過使用 `-u` 或 `--update` 引數來更新資料庫至最新狀態：
```bash
python initial.py -u
```
假設今天是 2022-01-01，而更新前的資料庫只收錄至 2021-12-01 發售的作品，則程式會自動收集 2021-12-02 到 2022-01-01 間發售的作品資料至資料庫。

如果您需要更新特定日期的資料庫，請使用 `-d` 或 `--date` 引數：
```bash
# 更新 2022-01-01 發售的作品
python initial.py -d 2022-01-01 

# 更新 2022-01-01 到 2022-01-31 間發售的作品
python initial.py -d 2022-01-01 2022-01-31
```

### 進階選項
使用 `-h` 或 `--help` 引數來查看所有可用的引數：
```bash
python initial.py -h
```
```
usage: initial.py [-h] (-i | -s | -u | -d DATE [DATE ...]) 
       [--path PATH] [--model MODEL] [--no_genre] [--raw_only]
```

## 資料庫檔案說明
茲說明各檔案的用途。
- `dates_table.json`: 該檔案記錄了資料庫爬取各作品的時間，以便於計算下次爬取的時間。其結構如下：
```json
{
    "2000-01-01": "2022-01-01 00:00:00",
}
```
其中，`2000-01-01`是作品發售日，`2022-01-01 00:00:00`是上次爬取的時間。

- `genre_table.json`: 該檔案記錄了所有屬性標籤的編號、名稱、數量、以及所屬的類別。其結構如下：
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
其中，`509`是標籤的編號，`category`是標籤的類別，`name`是標籤的名稱，`count`是標籤的數量。標籤的類別與名稱有多種語言，需透過語言代碼（如`ja_JP`）選擇。請同時參閱 [module.dlsite.GenreCatalog](../module/dlsite.py)。

- `genre_vec.pkl`: 該檔案記錄了所有屬性標籤的向量嵌入。
- `workformat.json`: 該檔案記錄了所有作品類別的代號、名稱與所屬的父類別。其結構如下：
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
其中，`ACN`是作品類別的代號，`category`是作品類別的父類別，`name`是作品類別的名稱。作品類別的父類別與名稱有多種語言，需透過語言代碼（如`ja_JP`）選擇。

- `works.sqlite`: 該檔案是 SQLite 作品資料庫，記錄了作品搜尋所必要的 metadata。
- `works_table.json`: 該檔案記錄了所有作品的完整 metadata，由於資料量龐大，因此不建議直接開啟。