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

DLfilter *無法*以人氣搜尋作品，因為沒有辦法即時更新這個資料庫（當然，我也進不去 DLsite 的）。不過，人氣高的作品未必是你想要的。

## 安裝
以下的說明是給想自己部署 DLfilter 服務的人用的（尤其是當你發現我的 Demo 掛掉時）。
如果你只是想用 DLfilter，請直接前往 [https://dlfilter.moe/](https://dlfilter.moe/)。

你需要 Python 3.10 來安裝 DLfilter。

1. 首先複製這個 repository
```bash
git clone https://github.com/snowmeow2/DLfilter
cd DLfilter
```

2. 安裝依賴套件
```bash
pip install -r requirements.txt
```

3. 初始化資料庫。有兩種方法可以選擇：
- 從 **[這裡](https://drive.google.com/file/d/1Jod-iFufGW3lIyqttlws9hOqK4k79ha8/view?usp=sharing)** 下載預先建立好的資料庫，並將其解壓縮到 `DLfilter/database/`（約 130 MB，解壓縮後約 1 GB）。
> 這個資料庫只更新到 2023-07-10。你可能之後會想[自己更新](docs/database.zh-tw.md#更新資料庫)。

- 自己建立資料庫。請參考[這裡](docs/database.zh-tw.md#初始化資料庫)的說明。

4. 啟動伺服器
```bash
uvicorn app:app --port 8000
```
你應該可以在 `http://localhost:8000/` 看到網站。

## 使用
很簡單。你可以透過**標籤**或是**作品**來尋找相似的作品。一般來說，相似度在 70% 以上的作品通常都是相關的。

### 以屬性標籤搜尋
> **重要**：這裡加入的標籤*不一定*會出現在搜尋結果中，因為它們只是用來當作搜尋的「種子」。

加入你喜歡的標籤。DLfilter 會將這些標籤的詞向量平均後進行查詢，並回傳跟這些標籤相似的作品。

我推薦使用 2-6 個標籤。太多或太少的標籤都會影響搜尋結果的品質。

![image](docs/images/usage1.png)

### 以作品搜尋
如果你不知道要加入哪些標籤，你可以以作品來搜尋。只要輸入作品 ID（例如 `RJ123456`），DLfilter 就會自動取得它的標籤並回傳相似的作品。

![image](docs/images/usage2.png)

### 過濾屬性
如果你想要強制包含/排除某些屬性，你可以在「包含」或「排除」的欄位中輸入它們。

![image](docs/images/usage3.png)

這邊設定的屬性*不會*用來搜尋，只會用來過濾結果。

## 計畫
- [x] ~~Demo 網站~~
- [] 自動更新資料庫
- [] UI 改進
- [] Dockerize
- [] 文檔改進
- [] 負向搜尋
- [] 以關鍵字與作者搜尋
- [] 搜尋其他 DLsite 的作品
- [] 更好的標籤權重
- [] 個人化搜尋
- [] ???

## 已知問題
- 屬性 `おやじ`、`少女コミック`、`少年コミック`、`女性コミック`、`青年コミック` 無法搜尋。這是因為它們在 DLsite API 中沒有本地化的名稱。
- 有些屬性的數量可能是錯誤的。