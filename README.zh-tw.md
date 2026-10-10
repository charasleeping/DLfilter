<h1 align="center">DLfilter</h1>

<p align="center">
  <b>依作品給人的感覺，而不只是名稱，來尋找 DLsite 作品。</b><br>
  DLsite 的標籤語義搜尋引擎，附帶快速的本機作品搜尋、四種語言與一鍵 Docker。
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
  <a href="README.md">English</a> | <a href="README.jp.md">日本語</a> | 正體中文 | <a href="README.zh-cn.md">简体中文</a>
</p>

DLfilter 將 DLsite 的標籤（類型，例如 `治癒`、`純愛`）當作詞語做嵌入，因此即使兩部作品沒有任何相同標籤，也能找到類型在*語意上相近*的作品。它也能依標題（日文、英文或中文）、社團名稱或 RJ 編號搜尋本機資料庫，並能從任何一筆結果開始相似作品搜尋。

本儲存庫是 [charasleeping](https://github.com/charasleeping/DLfilter) 對 [snowmeow2 的 DLfilter](https://github.com/snowmeow2/DLfilter) 的重啟分支。相似度搜尋與構想皆出自原作者；本分支讓它能在目前的 Python 與函式庫上運作，並加入了[本分支的新功能](#本分支的新功能)中列出的項目。

不一定會定期維護。歡迎自由 fork 或發 PR。

目前尚未支援 BJ 與 VJ 作品編號，預計在 2026 年 11 月底前支援。

## 目錄
[功能](#功能) | [本分支的新功能](#本分支的新功能) | [安裝](#安裝) | [使用方式](#使用方式) | [HTTP API](#http-api) | [開發藍圖](#開發藍圖) | [已知問題](#已知問題) | [致謝](#致謝)

## 功能

### 搜尋
| | |
| --- | --- |
| **尋找作品** | 依標題、社團名稱或 RJ 編號搜尋本機資料庫。不分全形半形與大小寫，且每個詞都必須符合。 |
| **以翻譯標題尋找** | 也能用官方的英文、正體中文與簡體中文標題找到作品。以此找到的卡片上有一個小開關，可改看原作標題。 |
| **尋找相似作品** | 依一組類型或指定作品搜尋，並依類型的語義相似度排序。 |
| **隨機作品** | 從資料庫隨機抽出作品，可依年齡分級篩選（在**尋找相似作品**分頁則套用其所有篩選條件）。 |
| **從任何結果尋找相似作品** | 點一下結果即可把其 RJ 編號、類型與作品形式帶入**尋找相似作品**分頁。 |

### 調整結果
- 依熱門程度加權類型（偏好冷門或熱門的類型）。
- 依下載數與發售日期加權結果。
- 納入或排除特定類型，並可依作品形式篩選。
- 依年齡分級篩選，並可排除 AI 生成、部分 AI 生成、低評價、獵奇或男同性戀作品。

### 好用的細節
- **預設組**：儲存整組搜尋設定（RJ 編號、類型、作品形式、進階選項），之後再載入，也可從任何位置開啟預設組檔案。
- **四種語言**：一鍵切換英文、日文、正體中文與簡體中文。類型與作品形式名稱採用 DLsite 官方翻譯，介面用詞也依循 DLsite。
- **亮色與暗色主題**，附平滑轉場。語言與主題都會由瀏覽器記住。
- 在自己的電腦上以本機 SQLite 資料庫執行，也提供 Docker 設定。

DLfilter *無法*依熱門程度搜尋作品，因為那需要即時更新的資料庫，而這是不可能的（顯然無法存取 DLsite 的資料庫）。但是，我相信熱門的不一定是你想要的。

## 本分支的新功能
與 [snowmeow2/DLfilter](https://github.com/snowmeow2/DLfilter) 相比：

| 項目 | 原版 | 本分支 |
| --- | --- | --- |
| **搜尋** | 僅有相似度搜尋 | 新增**尋找作品**（標題 / 社團 / RJ 編號，含排序）、**隨機作品**，以及從任何結果**尋找相似作品** |
| **介面** | 單一搜尋面板；語言依瀏覽器 | 分頁式搜尋面板、重設與隨機按鈕、**語言切換**（EN / JA / zh-TW / zh-CN，採用 DLsite 用詞）、亮暗主題、預設組 |
| **預設組** | 無 | 以 JSON 檔儲存、載入與匯入搜尋設定（含驗證，最多 200 個） |
| **Python** | 3.10 | **3.11 - 3.14**，支援 Linux、macOS 與 Windows |
| **相依套件** | 未鎖定版本的 `requirements.txt` | `pyproject.toml` + `uv.lock`（鎖定版本）、供 pip 使用的自動產生 `requirements.txt`、Linux 使用僅 CPU 的 PyTorch |
| **執行方式** | `uvicorn app:app` | 另可用 `python app.py`、以 `DLFILTER_*` 環境變數設定、路徑不受工作目錄影響 |
| **Docker** | 無 | `Dockerfile` 與 `compose.yaml`（非 root、唯讀資料庫、預設組磁碟區、可選的離線 `update` 工作） |
| **資料庫安全** | 直接就地寫入 | 網站使用唯讀連線；匯出先寫入暫存檔、檢查後再以 `.bak` 備份換入 |
| **爬取** | 無限重試 | 請求逾時、有上限的指數退避、爬取超過 31 天前需要確認 |
| **翻譯** | 只有日文標題 | 可用官方的英文 / 正體中文 / 簡體中文標題搜尋，涵蓋同一編號下提供多種語言的作品，以及有獨立編號的翻譯版本，卡片上有標題切換開關。以 `initial.py -u EN TC SC` 收集 |
| **翻譯爬取** | 無 | 並行查詢並限制速率，DLsite 回應 403 或 429 時自動放慢；進度條、可接續的執行，以及中斷後詢問是否重建資料庫 |
| **`initial.py` 選項** | `-i`、`-s`、`-u`、`-d` | `-c` 檢查日期，`-u` 可在同一天重複執行，`-r` 移除翻譯或所有作品，`-u` 與 `-d` 接受語言，`-k` 選擇種類，`-s` 略過所有問題，`--workers`、`--rate`、`--limit` 調整爬取 |
| **模型** | 需要時才下載 | 可從本機模型資料夾完全離線執行；為預設模型的 tokenizer 固定 `transformers<5` |
| **執行時負擔** | 匯入 `sentence-transformers` | 網站不再匯入它（以 PyTorch 計算餘弦相似度），只有 `initial.py` 需要 |
| **診斷** | 無 | `python -m module.doctor` 檢查版本、路徑、資料，加上 `--model` 時還會檢查嵌入模型 |
| **測試** | 無 | 以小型暫存資料庫執行的超過 120 個 `pytest` 測試，由 GitHub Actions 在 Linux、macOS 與 Windows（Python 3.11 - 3.14）上執行 |
| **修正** | 使用已棄用的 Pydantic / FastAPI / pandas 呼叫 | 更新至目前版本；靜態檔案依修改時間更新快取；錯誤回應不再洩漏內部訊息 |

`recover_works_table_download.py` 還能在不動原檔的情況下，從被截斷的 `works_table.json`（例如下載中斷後）中救回完整的記錄。

## 安裝
以下說明適合想在自己的電腦或伺服器上架設 DLfilter 的人。

支援 Python 3.11 – 3.14（已在 Linux、macOS 與 Windows 測試）。

#### 快速開始（發行版 zip）
1. 從 [Releases](https://github.com/charasleeping/DLfilter/releases) 頁面下載 `DLfilter-vX.Y.Z.zip` 並解壓縮。
2. 按兩下 `start.bat`（Windows）或 `start.command`（macOS；第一次請在檔案上按右鍵並選擇**打開**；Linux 請執行 `./start.command`）。

啟動器會先詢問再安裝 [uv](https://docs.astral.sh/uv/)，接著安裝函式庫（第一次約 1 GB）、下載預先建好的資料庫（只有原作，約 470 MB），並在瀏覽器中開啟網站。不含翻譯（只有日文標題的原作）：如何自行取得翻譯，請見[管理資料庫](#管理資料庫)。設定 `DLFILTER_DB_URL` 可從其他位置下載資料庫；已有 zip 時可執行 `python -m module.fetch_database --file works-db.zip` 安裝。

#### 從原始碼安裝
1. 複製儲存庫：
```bash
git clone https://github.com/charasleeping/DLfilter
cd DLfilter
```

2. 安裝相依套件。可使用 [uv](https://docs.astral.sh/uv/)（建議，使用 `uv.lock` 中鎖定的版本）：
```bash
uv sync --extra update     # 只執行網站的話可省略 "--extra update"
```
或在虛擬環境中使用 pip：
```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell：.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
`update` 額外套件（已包含在 `requirements.txt`）只有 `initial.py` 會用到。Linux 上會安裝僅 CPU 的 PyTorch。

3. 初始化資料庫。有兩種方式：
- 從 [Mega](https://mega.nz/file/D4Q3jJYR#UrUQep6zSEqHJ0dZh2LUuGOF6YhO4p07YAjtxbRyaXw) 下載預先建好的資料庫（最後更新：2026-10-10），並將內容解壓縮到 `DLfilter/database/`（只有原作，約 470 MB，解壓縮後約 1.2 GB），或用 `python -m module.fetch_database --file <zip>` 安裝該 zip
> 下載內容包含截至 2026-10-10 的原作，只有日文標題，因此沒有翻譯作品，也不能用翻譯標題搜尋。它包含原始目錄，所以可以照常用 `python initial.py -u` 更新，並用 `python initial.py -u EN TC SC` 取得翻譯；取得翻譯可能需要很長的時間，請見[管理資料庫](#管理資料庫)。

- 自行初始化資料庫。請參閱[這裡](docs/database.zh-tw.md#初始化資料庫)。

4. 檢查設定（選用）。會顯示版本、路徑與資料庫狀態；加上 `--model` 還會離線載入嵌入模型：
```bash
uv run python -m module.doctor     # 或：python -m module.doctor
```

5. 啟動伺服器
```bash
uv run python app.py               # 或：python app.py
# 等同於：uvicorn app:app --port 8000
```
接著就能在 `http://localhost:8000/` 開啟網站。

### 設定
所有設定都是選用的環境變數：

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `DLFILTER_DATA_DIR` | `./database` | 存放 `works.sqlite` 與類型檔案的目錄 |
| `DLFILTER_PRESETS_DIR` | `./presets` | 儲存預設組的目錄 |
| `DLFILTER_HOST` | `127.0.0.1` | `python app.py` 監聽的位址 |
| `DLFILTER_PORT` | `8000` | `python app.py` 監聽的連接埠 |
| `DLFILTER_MODEL` | `sonoisa/sentence-luke-japanese-base-lite` | `initial.py` 使用的嵌入模型：Hugging Face ID 或本機目錄 |

### Docker
映像檔只提供既有的資料庫，啟動時不會下載或爬取任何東西。它以非 root 使用者執行，以唯讀方式掛載 `./database`，並把預設組存放在具名磁碟區。
```bash
docker compose up -d               # 於 http://localhost:8000/ 提供服務（綁定 127.0.0.1）
```
若要在容器中使用本機模型（不下載模型）更新資料庫，請參閱 [compose.yaml](compose.yaml) 中的 `update` 服務。該服務執行 `initial.py -u -s`，因此所有問題都用預設值回答（只更新原作，不取得翻譯）。

### 測試
```bash
uv run pytest
```
測試使用小型暫存資料庫，不需要真實資料或模型。GitHub Actions 會在 Linux、macOS 與 Windows 上以 Python 3.11 與 3.14 執行（Linux 另含 3.12 與 3.13）。

## 使用方式
DLfilter 有兩種找作品的方式：依**名稱**（標題、社團或 RJ 編號，支援日文、英文與中文），或依**相似度**（一組類型或指定作品）。經驗上，相似度超過 70% 的作品通常彼此相關。

### 啟動網站
按兩下 `start.bat`（Windows）或 `start.command`（macOS、Linux），或在專案資料夾執行：
```bash
python app.py            # 在 http://localhost:8000/ 提供服務
python app.py --open     # 並在瀏覽器中開啟
uv run python app.py     # 使用 uv 時的同等指令
```
設定 `DLFILTER_HOST` 與 `DLFILTER_PORT` 可改變監聽位置（見[設定](#設定)）。

### 以標題、社團或 RJ 編號尋找作品
使用搜尋面板的**尋找作品**分頁。選擇搜尋範圍（全部、標題、社團或 RJ 編號）與年齡分級，然後按 Enter。
- 每個詞都必須符合。不分全形半形與大小寫。
- 完全符合的 RJ 編號排最前，其次是完全相同的標題、以輸入文字開頭的標題，最後是其餘結果。
- 對結果按**尋找相似作品**，會把它的 RJ 編號、類型與作品形式帶入**尋找相似作品**分頁，你可以調整後再開始相似度搜尋。
- **骰子**按鈕會依所選年齡分級顯示隨機作品。重設按鈕會清除所有搜尋並回到歡迎頁面。

此搜尋*僅限本機資料庫*，因此不會知道上次更新後才發售的作品，也不含 DLsite 其他分類的作品（只收集 `maniax`）。結果不是依相似度排序，所以不顯示相似度分數。

### 依翻譯標題尋找作品
也能用官方的英文、正體中文與簡體中文標題找到作品；例如搜尋 `Interactive Mii` 可以找到 `ふれあいミイちゃん`。透過翻譯找到的卡片會顯示那個標題，縮圖右上角有一個小小的半透明開關。滑動它即可改看原作標題；開關上的字元與語言按鈕相同（A、あ、繁、简）。若你是以原作的語言搜尋，就不會出現這個開關。

這需要包含翻譯的資料庫，例如預先建好的那份（見[管理資料庫](#管理資料庫)）。在此功能之前建立的資料庫仍可照常使用，只是沒有翻譯標題。

### 依相似類型
> **重要**：在此加入的類型*不一定*會出現在搜尋結果中，因為它們是搜尋的「種子」。

加入你喜歡的類型。DLfilter 會把它們當作搜尋查詢（取所加入類型詞嵌入的平均值），並回傳類型相近的作品。

建議加入 2-6 個類型。太多或太少都可能得不到最好的結果。

### 依指定作品
如果你不知道要加入哪些類型，可以改用作品搜尋。只要輸入 RJ 編號（例如 `RJ123456`），DLfilter 就會自動取得它的類型並回傳相似作品。

若該編號不在本機資料庫中，可能是資料庫過舊、記錄遺失，或該作品屬於 DLsite 的其他分類。

### 篩選類型
如果有些類型必須包含或排除在結果中，可以在「包含的類型」與「排除的類型」欄位設定。

請注意，在此設定的類型*不是*用來搜尋的類型，只用來篩選結果。

### 預設組
**尋找相似作品**分頁中**搜尋**旁的按鈕可儲存與載入 RJ 編號、類型、作品形式與進階選項。預設組是專案 `presets/` 資料夾中的 JSON 檔（設定 `DLFILTER_PRESETS_DIR` 可改用其他資料夾；Docker 設定把它們存放在 `presets` 磁碟區）。**載入預設組**會列出該資料夾的內容，也能從其他位置開啟預設組檔案。

### 隨機作品
在**搜尋**下方，**隨機**會依你所在分頁的篩選條件顯示隨機作品，**重設**則會清除所有內容並回到歡迎頁面。

### 語言與主題
右上角的圓形按鈕可切換語言（英文、日文、正體中文、簡體中文，然後回到英文）與亮暗主題。若沒有儲存過選擇，DLfilter 會使用瀏覽器的語言。語言按鈕會顯示目前的語言，按下後滑動切換到下一個語言。

### 管理資料庫
請在專案資料夾執行以下指令（使用 uv 時在前面加上 `uv run`）。`initial.py` 需要 `update` 額外套件（`uv sync --extra update` 或 `pip install -r requirements.txt`）；啟動器腳本不會安裝它。

> 更新需要原始目錄 `database/works_table.json`（約 2.6 GB），預先建好的下載已包含它，所以安裝後可直接用 `-u`，並以 `-u EN TC SC` 加入翻譯。只有要自己建立目錄時才需要 `python initial.py -i`；它會爬取你輸入的起始日期之後的每一天，需要數小時以上。

> **警告**：取得翻譯需要很長的時間。首次執行時，光是用 `EN TC SC` 更新一次就可能需要數小時，因為程式要向 DLsite 逐一查詢作品，而 DLsite 會拒絕速度太快的用戶，所以預設速度刻意設得保守。建議先用 `-k titles` 或 `--limit` 開始，然後讓它跑；可以中斷並接續。之後的更新只會查詢新作品，會短很多。

| 想做的事 | 指令 |
| --- | --- |
| 下載並安裝預先建好的資料庫 | `python -m module.fetch_database`（`--file works-db.zip` 安裝已有的 zip，`--force` 覆蓋） |
| 檢查設定 | `python -m module.doctor`（加上 `--model` 還會載入嵌入模型） |
| 從頭建立資料庫 | `python initial.py -i`（會詢問日期範圍） |
| 查看已記錄的日期 | `python initial.py -c` |
| 更新到昨天 | `python initial.py -u`（會詢問是否一併取得翻譯） |
| 更新，並取得英文與中文標題 | `python initial.py -u EN TC SC` |
| 只更新原作 | `python initial.py -u NONE` |
| 只取得翻譯中較快的部分 | `python initial.py -u EN TC SC -k titles` |
| 只爬取一天 | `python initial.py -d 2026-10-01` |
| 爬取一段範圍並取得翻譯 | `python initial.py -d 2026-10-01 2026-10-10 EN TC SC` |
| 分次小量進行 | `python initial.py -u EN --limit 500 --workers 4 --rate 2` |
| 依已儲存的資料重建資料庫 | `python initial.py -u NONE --no_genre` |
| 移除某些語言的翻譯 | `python initial.py -r EN SC` |
| 移除資料庫中的所有作品 | `python initial.py -r ALL` |
| 不詢問直接執行（腳本、Docker） | `python initial.py -u EN TC SC -s`，或 `docker compose run --rm update -u EN TC SC -s` |
| 用本機模型離線更新 | `HF_HUB_OFFLINE=1 python initial.py -u --model /path/to/model` |
| 救回被截斷的 `works_table.json` | `python recover_works_table_download.py` |

語言可用 `JA`（原作，不需額外取得）、`EN`、`TC`、`SC` 與 `NONE`，以空格或逗號分隔。`-u` 與 `-d` 會先更新原作，再取得你指定的翻譯；沒有指定語言時會詢問。使用 `-d` 時，語言寫在日期之後。

| 選項 | 意思 |
| --- | --- |
| `-k`、`--kinds` | `titles`（同一編號下提供多種語言的作品，較快）和或 `editions`（有獨立編號的翻譯版本，較慢）；預設兩者皆做 |
| `-s`、`--skip` | 以預設值回答所有問題（沒有終端機時需要） |
| `--workers`、`--rate`、`--limit` | 並行請求數（6）、整體每秒請求數（4）、每次執行最多查詢的作品數 |
| `--path`、`--model`、`--no_genre`、`--raw_only` | 資料庫資料夾、嵌入模型、略過類型更新、略過重建 `works.sqlite` |

執行時會顯示進度條，可以 Ctrl-C 中斷並接續，在 DLsite 回應 403 或 429 時會自動放慢，中斷後也會詢問是否重建資料庫。同一天執行兩次 `-u` 沒有問題。重建前請先停止網站，並預留約 `works.sqlite` 兩倍大小的磁碟空間。詳見 [docs/database.zh-tw.md](docs/database.zh-tw.md)。

## HTTP API
網站是 JSON API 的輕量用戶端，因此你可以用腳本呼叫它。伺服器執行時，互動式文件位於 `/docs`。

| 端點 | 說明 |
| --- | --- |
| `GET /api/info` | 資料庫的作品數量與最後更新時間 |
| `GET /api/locale/{locale}` | 類型與作品形式名稱（`en_US`、`ja_JP`、`zh_TW`、`zh_CN`、`ko_KR`） |
| `GET /api/works?rj_id=...` | 最多 50 部作品的詳細資料；未知的編號列在 `missing` |
| `GET /api/search` | 含年齡篩選與分頁的標題 / 社團 / RJ 編號搜尋；透過翻譯標題找到的結果會附帶 `lang`、`originalName`、`originalLang` 與 `titleToggle` |
| `GET /api/random` | 隨機作品，可搭配相似度搜尋的篩選條件 |
| `POST /api/similarity` | 依類型或指定作品的相似度搜尋 |
| `GET /api/presets`、`GET` / `PUT /api/presets/{name}` | 列出、讀取與儲存預設組 |
