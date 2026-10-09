# DLfilter
[English](README.md) | 正體中文

以標籤語意驅動的 DLsite 作品搜尋引擎。
> Demo: [https://dlfilter.moe/](https://dlfilter.moe/)
> (可能隨時下線)

DLfilter 希望為 DLsite 的作品搜尋提供更好的體驗。
它讓使用者可以透過 DLsite 提供的屬性標籤（例如 `癒し`、`オールハッピー`）的詞向量來找到相似的作品。

請在[這裡](docs/description.zh-tw.md)閱讀 DLfilter 的完整說明。

DLfilter 是一個由我的*個人需求*以及為學習網頁開發而生的 Side Project。我不會定期進行更新，請見諒。歡迎 Fork 或 PR。

## 目錄
[特色](#特色) | [安裝](#安裝) | [使用](#使用) | [計畫](#計畫) | [已知問題](#已知問題)

## 特色
DLfilter 提供了以下 DLsite **沒有**的功能：
- 以屬性標籤搜尋與其相似的作品
- 搜尋任意作品的相似作品
- 以標籤的熱門度調整搜尋結果的權重
- 透過下載數與發售日期調整搜尋結果的權重

此外，也可以用作品名、社團名或 RJ 號在本機資料庫中尋找作品，並從任一結果開始相似作品搜尋。

DLfilter *無法*以人氣搜尋作品，因為沒有辦法即時更新這個資料庫（當然，我也進不去 DLsite 的）。不過，人氣高的作品未必是你想要的。

## 安裝
以下的說明是給想自己部署 DLfilter 服務的人用的（尤其是當你發現我的 Demo 掛掉時）。
如果你只是想用 DLfilter，請直接前往 [https://dlfilter.moe/](https://dlfilter.moe/)。

支援 Python 3.11 – 3.14（已在 Linux、macOS 與 Windows 上測試）。

1. 首先複製這個 repository
```bash
git clone https://github.com/snowmeow2/DLfilter
cd DLfilter
```

2. 安裝依賴套件。可以使用 [uv](https://docs.astral.sh/uv/)（推薦，會使用 `uv.lock` 鎖定的版本）：
```bash
uv sync --extra update     # 如果只需要架網站，可以省略 "--extra update"
```
或在虛擬環境中使用 pip：
```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell：.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
`update` 額外套件（已包含在 `requirements.txt` 中）只有 `initial.py` 需要。在 Linux 上會安裝僅支援 CPU 的 PyTorch。

3. 初始化資料庫。有兩種方法可以選擇：
- 從 **[這裡](https://drive.google.com/file/d/1Jod-iFufGW3lIyqttlws9hOqK4k79ha8/view?usp=sharing)** 下載預先建立好的資料庫，並將其解壓縮到 `DLfilter/database/`（約 130 MB，解壓縮後約 1 GB）。
> 這個資料庫只更新到 2023-07-10。你可能之後會想[自己更新](docs/database.zh-tw.md#更新資料庫)。

- 自己建立資料庫。請參考[這裡](docs/database.zh-tw.md#初始化資料庫)的說明。

4. 檢查環境（可選）。會顯示套件版本、路徑與資料庫狀態；加上 `--model` 會同時以離線模式載入詞向量模型：
```bash
uv run python -m module.doctor     # 或：python -m module.doctor
```

5. 啟動伺服器
```bash
uv run python app.py               # 或：python app.py
# 等同於：uvicorn app:app --port 8000
```
你應該可以在 `http://localhost:8000/` 看到網站。

### 設定
以下環境變數皆為可選：

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `DLFILTER_DATA_DIR` | `./database` | 存放 `works.sqlite` 與屬性檔案的目錄 |
| `DLFILTER_HOST` | `127.0.0.1` | `python app.py` 監聽的位址 |
| `DLFILTER_PORT` | `8000` | `python app.py` 監聽的連接埠 |
| `DLFILTER_MODEL` | `sonoisa/sentence-luke-japanese-base-lite` | `initial.py` 使用的詞向量模型：Hugging Face ID 或本機目錄 |

### Docker
映像檔只提供現有的資料庫，啟動時不會下載或爬取任何東西。
```bash
docker compose up -d               # 以唯讀方式掛載 ./database，網址為 http://localhost:8000/
```
若要在容器中使用本機模型更新資料庫，請參考 [compose.yaml](compose.yaml) 中的 `update` 服務。

### 測試
```bash
uv run pytest
```
測試使用小型的暫存資料庫，不需要真正的資料或模型。

## 使用
很簡單。你可以透過**標籤**或是**作品**來尋找相似的作品。一般來說，相似度在 70% 以上的作品通常都是相關的。

### 以作品名、社團名或 RJ 號尋找作品
使用搜尋面板的**尋找作品**分頁。選擇搜尋範圍（全部、作品名、社團或 RJ 號）與年齡分級後按 Enter。
- 每個詞都必須符合，不區分全形半形與大小寫。
- 排序依序為：完全相符的 RJ 號、完全相符的作品名、以輸入文字開頭的作品名、其他。
- 點選結果上的**尋找相似作品**，會在**尋找相似作品**分頁填入它的 RJ 號、屬性與作品類型，調整後即可開始相似作品搜尋。
- 骰子按鈕會依所選的年齡分級隨機顯示作品。重設按鈕會清除所有搜尋並回到歡迎頁。

這只會搜尋**本機資料庫**，因此找不到上次更新後發售的作品，或 DLsite 其他分類的作品（目前只收集 `maniax`）。結果不是依相似度排序，所以不會顯示相似度。

### 以屬性標籤搜尋
> **重要**：這裡加入的標籤*不一定*會出現在搜尋結果中，因為它們只是用來當作搜尋的「種子」。

加入你喜歡的標籤。DLfilter 會將這些標籤的詞向量平均後進行查詢，並回傳跟這些標籤相似的作品。

我推薦使用 2-6 個標籤。太多或太少的標籤都會影響搜尋結果的品質。

![image](docs/images/usage1.png)

### 以作品搜尋
如果你不知道要加入哪些標籤，你可以以作品來搜尋。只要輸入 RJ 號（例如 `RJ123456`），DLfilter 就會自動取得它的標籤並回傳相似的作品。

如果本機資料庫中沒有這個 ID，可能是資料庫未更新、紀錄缺失，或該作品屬於 DLsite 的其他分類。

![image](docs/images/usage2.png)

### 過濾屬性
如果你想要強制包含/排除某些屬性，你可以在「包含」或「排除」的欄位中輸入它們。

![image](docs/images/usage3.png)

這邊設定的屬性*不會*用來搜尋，只會用來過濾結果。

### 預設
**搜尋**左邊的按鈕可以儲存與載入 RJ 號、屬性、作品類型與進階選項。預設會以 JSON 檔存在專案的 `presets/` 資料夾（可用 `DLFILTER_PRESETS_DIR` 改用其他資料夾；Docker 設定則存在 `presets` volume）。**載入預設**會列出該資料夾的內容，也可以開啟其他位置的預設檔。

## 計畫
- [x] ~~Demo 網站~~
- [] 自動更新資料庫
- [] UI 改進
- [x] ~~Dockerize~~
- [] 文檔改進
- [] 負向搜尋
- [x] ~~以作品名、社團與 RJ 號搜尋~~
- [] 搜尋其他 DLsite 的作品
- [] 更好的標籤權重
- [] 個人化搜尋
- [] ???

## 已知問題
- 屬性 `おやじ`、`少女コミック`、`少年コミック`、`女性コミック`、`青年コミック` 無法搜尋。這是因為它們在 DLsite API 中沒有本地化的名稱。
- 有些屬性的數量可能是錯誤的。