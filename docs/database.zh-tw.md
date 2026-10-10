# 作品資料庫
DLfilter 的作品資料庫目錄結構如下：
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
> 這些檔案並沒有包含在本專案中，您需要自行建立或下載。
> 
> 請注意，`dates_table.json` 與 `works_table.json` 不是必要的檔案，但是如果您希望自行建立資料庫，則需要這兩個檔案。

## 資料庫管理
### 初始化資料庫
DLfilter 需要一個作品資料庫才能開始運作。

初次使用時，您可以直接從 **[Mega](https://mega.nz/file/rk4CVbrK#sfJd5F5RX-7wlQjq7PTS4aW5FhmHBKDyc0-HNvG3Jqk)** 下載預先建立好的資料庫（最後更新：2026-10-10；收錄 2000-01-01 起、只有日文標題的原作，約 470 MB，解壓縮後約 3.8 GB）。下載後，請將檔案解壓縮至 `DLfilter/database` 目錄下，或用 `python -m module.fetch_database --file <zip>` 安裝該 zip。它與啟動器、`python -m module.fetch_database` 預設下載的是同一個檔案，不含翻譯作品與翻譯標題，但包含原始目錄（`works_table.json`），因此可以照常用 `initial.py -u` 更新，並用 `initial.py -u EN TC SC` 取得[翻譯](#翻譯版本)。只有要自己建立目錄時才需要 `initial.py -i`。

如果您希望自行建立資料庫，請執行 `initial.py -i` 來初始化資料庫。執行時，請確保您的環境中已經安裝了所需的套件（包含 `update` 額外套件）：
```bash
cd DLfilter
uv sync --extra update             # 或：pip install -r requirements.txt
```
然後
```bash
uv run python initial.py -i        # 或：python initial.py -i
```
程式會詢問您要收集的日期範圍。請依 `YYYY-MM-DD` 格式輸入您希望的一個或一段日期：
- `2022-01-01` 或 
- `2022-01-01 2022-01-31`（以空格分隔）

程式會自動爬取於該日期範圍內發售的所有作品資料，並建立資料庫。失敗的請求會以遞增的間隔重試數次。

首次建立資料庫時，程式會自動下載語言模型以建立標籤的詞向量嵌入，這可能需要一些時間。預設使用 [sonoisa/sentence-luke-japanese-base-lite](https://huggingface.co/sonoisa/sentence-luke-japanese-base-lite)。您可以透過增加 `--model model_name` 引數（或設定 `DLFILTER_MODEL`）來使用 [Hugging Face](https://huggingface.co/) 上的其他語言模型。

若要離線使用，請傳入模型的本機目錄而非名稱，並禁止 Hugging Face 連線：
```bash
HF_HUB_OFFLINE=1 python initial.py -u --model /path/to/sonoisa_sentence-luke-japanese-base-lite
```
預設模型需要 `transformers` 4.x；第 5 版無法載入它的 tokenizer，因此鎖定檔固定為 `transformers<5`。可執行 `python -m module.doctor --model` 確認模型能否載入。

### 安全儲存資料庫
`works.sqlite` 會先寫入 `works.sqlite.tmp` 並經過檢查（完整性、必要欄位、筆數），之後才會將舊檔改名為 `works.sqlite.bak`，再將新檔移入。若過程中發生錯誤，舊資料庫不會被更動。
- 匯出前請先停止伺服器，避免在讀取時替換檔案。
- 請預留約 `works.sqlite` 兩倍大小的磁碟空間（新檔與備份會同時存在）。
- 若要還原，請停止伺服器後將 `works.sqlite.bak` 改名為 `works.sqlite`。

### 更新資料庫
如果您已經有了資料庫，您可以透過使用 `-u` 或 `--update` 引數來更新資料庫至最新狀態：
```bash
python initial.py -u
```
假設今天是 2022-01-01，而更新前的資料庫只收錄至 2021-12-01 發售的作品，則程式會自動收集 2021-12-02 到 2022-01-01 間發售的作品資料至資料庫。同一天再次執行 `-u` 會重新收集昨天的作品，以更新它們的數據。

如果您需要更新特定日期的資料庫，請使用 `-d` 或 `--date` 引數：
```bash
# 更新 2022-01-01 發售的作品
python initial.py -d 2022-01-01 

# 更新 2022-01-01 到 2022-01-31 間發售的作品
python initial.py -d 2022-01-01 2022-01-31
```
使用 `-d` 且範圍超過 31 天時，會先要求確認，因為爬取需要很長的時間。

日期之後，`-u` 與 `-d` 會詢問是否一併取得翻譯（見下）。把語言寫在指令後面（`-u EN TC`、`-d 2022-01-01 EN`）可略過此問題，`NONE` 或 `JA` 表示只更新原作，加上 `-s` 則略過所有問題。

### 翻譯版本
> **警告**：取得翻譯需要很長的時間。首次用 `EN TC SC` 執行可能需要數小時，因為程式要向 DLsite 逐一查詢作品，而 DLsite 會拒絕速度太快的用戶。建議先用 `-k titles` 或 `--limit`；可以中斷並接續，之後的更新只會查詢新作品。

每日作品清單只有各作品的日文標題。官方的英文、繁體中文與簡體中文標題需另外收集，才能以它們搜尋作品。請把語言列在 `-u` 後面，或 `-d` 的日期後面：
```bash
python initial.py -u                  # 日期之後詢問語言
python initial.py -u EN TC SC         # 先更新原作，再取得三種翻譯
python initial.py -u EN -k titles     # 只取得多語言作品的英文標題（快）
python initial.py -u NONE             # 只更新原作，不詢問
python initial.py -d 2022-01-01 2022-01-31 EN TC
python initial.py -u EN --limit 500 --workers 4
```
可使用 `JA`（只更新原作）、`EN`、`TC`、`SC` 與 `NONE`，以空格或逗號分隔。若原作已是最新，`-u` 會直接處理翻譯，這也是為既有資料庫取得翻譯的方法。

共有兩種，以 `-k/--kinds titles editions` 選擇（預設兩者皆做）。`titles`：同一個作品編號下提供多種語言的作品（例如 RJ01722990），各語系顯示不同標題，這些標題記錄於 `title_table.json`，並存入 `name_ENG`、`name_CHI_HANT`、`name_CHI_HANS` 欄位。這是較快的部分，46 萬件作品的資料庫約需 11,000 次請求。`editions`：以獨立作品編號發布的翻譯版本（如「[ENG Ver.]」）依語言列出，記錄於 `translation_table.json`。這是較慢的部分，首次執行需要數萬次請求。

程式會逐一查詢尚未見過的作品，從最新的開始，並以 `--workers` 個並行請求（預設 6）、整體每秒不超過 `--rate` 次請求（預設 4；DLsite 會拒絕速度太快的用戶，請謹慎調高）進行。用來尋找翻譯版本的清單頁面每秒最多取得一次。進度條會顯示速度與剩餘時間。若 DLsite 回應 HTTP 403 或 429，所有請求會先暫停（30 秒，每次加倍），且本次執行的速度減半，連續失敗五次後程式會顯示訊息並停止；請稍後再重新執行。可隨時以 Ctrl-C 中斷；重新執行時會接續進度。中斷或失敗後，程式會詢問是否依已儲存的進度重建 `works.sqlite`（加上 `-s` 則直接重建；沒有終端機時不重建）。也可以之後用 `python initial.py -u NONE --no_genre` 重建，不需要爬取。更新原作時也會重建 `works.sqlite`，因此使用 `--limit` 的部分執行也能讓已收集的標題可被搜尋。

以獨立編號發布的翻譯版本會存成獨立的一列：複製原作的標籤、評分、下載數與簡介，但使用自己的編號、標題、社團、發售日與選項。只有原作在資料庫中時才會加入。

透過翻譯標題找到的卡片上會出現開關，可改看原作標題。在此功能之前建立的資料庫仍可照常使用，只是沒有此開關。

### 移除資料
`-r/--remove` 會先顯示將刪除的內容並要求確認（預設為否）：
```bash
python initial.py -r EN SC   # 移除英文與簡體中文翻譯，然後重建資料庫
python initial.py -r ALL     # 刪除 works.sqlite，即所有作品
python initial.py -r         # 詢問要移除什麼
```
`-r ALL` 會保留 `works.sqlite.bak`、原始目錄、標籤檔案與翻譯表，之後可用 `-u` 重建資料庫。原作無法單獨移除（`-r JA` 會被拒絕），因為翻譯的資料列依賴原作。

### 檢查日期
`-c/--check` 會印出目錄中記錄的日期後結束。它先前是 `-s/--show`；現在 `-s/--skip` 會以預設值回答所有問題，沒有終端機時（例如 Docker 的 `update` 工作）需要使用它。

### 進階選項
使用 `-h` 或 `--help` 引數來查看所有可用的引數：
```bash
python initial.py -h
```
```
usage: initial.py [-h] (-i | -c | -u [LANG ...] | -d DATE|LANG [DATE|LANG ...] | -r [TARGET ...])
       [-k {titles,editions} ...] [-s] [--path PATH]
       [--workers WORKERS] [--rate RATE] [--limit LIMIT] [--model MODEL] [--no_genre] [--raw_only]
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
- `title_table.json`: 記錄同一編號下提供多種語言之作品的官方翻譯標題，以作品編號為鍵：`{"ENG": "...", "CHI_HANT": null}`。`null` 表示與日文標題相同。
- `translation_table.json`: 該檔案記錄了 `initial.py -u EN TC SC` 找到的翻譯版本，以版本的作品編號為鍵：`lang`（`ENG`、`CHI_HANT` 或 `CHI_HANS`）、`originalWorkno`、`originalLang`，以及該版本的 `name`、`maker`、`makerId`、`registDate`、`options` 與 `siteId`。非翻譯版本的作品會記為 `{"lang": null}`，以免重複查詢。
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

- `works.sqlite`: 該檔案是 SQLite 作品資料庫，記錄了作品搜尋所必要的 metadata。相似作品搜尋與作品名／社團／RJ 號搜尋都會讀取它；後者只找得到此處收集的作品（DLsite `maniax`，截至上次更新）。
  翻譯版本的列另有選用欄位 `lang`、`originalWorkno`、`originalLang` 與 `originalName`，其他作品這些欄位為 NULL。選用欄位 `name_ENG`、`name_CHI_HANT`、`name_CHI_HANS` 存放多語言作品的翻譯標題。
- `works_table.json`: 該檔案記錄了所有作品的完整 metadata，由於資料量龐大，因此不建議直接開啟。