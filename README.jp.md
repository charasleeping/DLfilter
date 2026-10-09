<h1 align="center">DLfilter</h1>

<p align="center">
  <b>名前だけでなく、作品の「雰囲気」から DLsite の作品を探す。</b><br>
  DLsite のタグをセマンティック検索するエンジン。高速なローカル作品検索、4言語対応、ワンコマンドで動く Docker 付き。
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
  <a href="README.md">English</a> | 日本語 | <a href="README.zh-tw.md">正體中文</a> | <a href="README.zh-cn.md">简体中文</a> | <a href="https://dlfilter.moe/">Demo</a>
</p>

> デモ: [https://dlfilter.moe/](https://dlfilter.moe/)（いつでも停止する可能性があります）

DLfilter は DLsite のタグ（ジャンル。例: `癒し`、`純愛`）を単語として埋め込みます。そのため、同じタグを一つも共有していなくても、ジャンルの*意味が近い*作品を見つけられます。タイトル、サークル名、RJ 番号でローカルデータベースを検索することもでき、どの検索結果からでも類似作品検索を始められます。

このリポジトリは、[snowmeow2 の DLfilter](https://github.com/snowmeow2/DLfilter) を [charasleeping](https://github.com/charasleeping/DLfilter) が復活させたフォークです。類似度検索とそのアイデアは原作者によるものです。このフォークは現在の Python とライブラリで動くようにし、[このフォークの新機能](#このフォークの新機能)に挙げた機能を追加しています。

DLfilter は*個人利用*と学習目的のサイドプロジェクトで、定期的にメンテナンスされるとは限りません。フォークや PR はご自由にどうぞ。

## 目次
[機能](#機能) | [このフォークの新機能](#このフォークの新機能) | [インストール](#インストール) | [使い方](#使い方) | [HTTP API](#http-api) | [ロードマップ](#ロードマップ) | [既知の問題](#既知の問題) | [クレジット](#クレジット)

## 機能

### 検索
| | |
| --- | --- |
| **作品を探す** | タイトル、サークル名、RJ 番号でローカルデータベースを検索します。全角・半角と大文字・小文字は区別せず、すべての語に一致する必要があります。 |
| **似た作品を探す** | ジャンルの組み合わせ、または指定した作品から、ジャンルの意味的な類似度順に検索します。 |
| **ランダムな作品** | データベースからランダムに作品を選びます。年齢区分で絞り込めます（**似た作品を探す**タブでは、そのタブのすべての絞り込みが適用されます）。 |
| **どの結果からでも似た作品を探す** | 結果をワンクリックすると、その RJ 番号・ジャンル・作品形式が**似た作品を探す**タブに入力されます。 |

### 結果の調整
- 人気度でジャンルに重み付け（ニッチなジャンルを優先、または人気のジャンルを優先）。
- ダウンロード数と発売日で結果に重み付け。
- 特定のジャンルを含める・除外する、作品形式で絞り込む。
- 年齢区分で絞り込み、AI 生成、一部 AI 生成、低評価、グロ、男性同性愛の作品を除外。

### 使いやすさ
- **プリセット**: 検索設定一式（RJ 番号、ジャンル、作品形式、詳細オプション）を保存して後で読み込めます。プリセットファイルを任意の場所から開くこともできます。
- **4言語対応**: ワンクリックで英語、日本語、繁体字中国語、簡体字中国語を切り替えられます。ジャンルと作品形式の名称は DLsite 公式の翻訳で、ラベルも DLsite の表記に合わせています。
- **ライトテーマとダークテーマ**: なめらかな切り替え付き。言語とテーマはブラウザに記憶されます。
- ローカルの SQLite データベースを使って自分のマシンで動作し、Docker 構成も用意されています。

DLfilter は人気順の検索*ができません*。それにはデータベースのリアルタイム更新が必要ですが、DLsite のデータベースにはアクセスできないためです。ただ、人気のものが必ずしもあなたの求めるものとは限らないと思っています。

## このフォークの新機能
[snowmeow2/DLfilter](https://github.com/snowmeow2/DLfilter) との比較:

| 項目 | オリジナル | このフォーク |
| --- | --- | --- |
| **検索** | 類似度検索のみ | **作品を探す**（タイトル / サークル / RJ 番号、順位付き）、**ランダムな作品**、どの結果からでも**似た作品を探す**を追加 |
| **インターフェース** | 検索パネルは1つ。言語はブラウザ依存 | タブ式の検索パネル、リセットとランダムのボタン、**言語切り替え**（EN / JA / zh-TW / zh-CN、DLsite の表記）、ライト/ダークテーマ、プリセット |
| **プリセット** | なし | 検索設定を JSON ファイルとして保存・読み込み・インポート（検証あり、最大 200 件） |
| **Python** | 3.10 | **3.11 - 3.14**（Linux、macOS、Windows） |
| **依存関係** | バージョン固定なしの `requirements.txt` | `pyproject.toml` + `uv.lock`（固定）、pip 用に生成した `requirements.txt`、Linux では CPU 専用の PyTorch |
| **起動方法** | `uvicorn app:app` | `python app.py` も可。`DLFILTER_*` 環境変数で設定でき、パスは作業ディレクトリに依存しない |
| **Docker** | なし | `Dockerfile` と `compose.yaml`（非 root、読み取り専用データベース、プリセット用ボリューム、任意のオフライン `update` ジョブ） |
| **データベースの安全性** | その場で書き込み | サイトは読み取り専用接続。エクスポートは一時ファイルに書き出して検証し、`.bak` バックアップを残して入れ替え |
| **クロール** | 無制限にリトライ | リクエストのタイムアウト、上限付きの指数バックオフ、31 日を超えるクロールの前に確認 |
| **モデル** | 必要時にダウンロード | ローカルのモデルフォルダから完全オフラインで実行可能。既定モデルのトークナイザのため `transformers<5` に固定 |
| **実行時の重さ** | `sentence-transformers` をインポート | サイトはインポートしない（コサイン類似度は PyTorch で計算）。必要なのは `initial.py` のみ |
| **診断** | なし | `python -m module.doctor` がバージョン、パス、データを確認し、`--model` を付けると埋め込みモデルも確認 |
| **テスト** | なし | 小さな一時データベースを使う 75 件の `pytest` テスト。GitHub Actions が Linux、macOS、Windows（Python 3.11 - 3.14）で実行 |
| **修正** | 非推奨の Pydantic / FastAPI / pandas の呼び出し | 現行バージョンに更新。静的ファイルは更新時刻でキャッシュ更新。エラー応答が内部メッセージを漏らさない |

`recover_works_table_download.py` は、途中で切れた `works_table.json`（ダウンロード中断後など）から、元のファイルを変更せずに完全なレコードだけを救出できます。

## インストール
以下は、自分でデプロイしたい方（特にデモが停止しているとき）向けの手順です。
DLfilter を使うだけなら [https://dlfilter.moe/](https://dlfilter.moe/) をご利用ください。

Python 3.11 – 3.14 に対応しています（Linux、macOS、Windows でテスト済み）。

1. リポジトリをクローンします:
```bash
git clone https://github.com/charasleeping/DLfilter
cd DLfilter
```

2. 依存関係をインストールします。[uv](https://docs.astral.sh/uv/)（推奨。`uv.lock` で固定されたバージョンを使用）を使う場合:
```bash
uv sync --extra update     # Web サイトだけ動かすなら "--extra update" は不要
```
または、仮想環境で pip を使う場合:
```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
`update` エクストラ（`requirements.txt` に含まれます）が必要なのは `initial.py` だけです。Linux では CPU 専用の PyTorch がインストールされます。

3. データベースを初期化します。方法は2つあります:
- ビルド済みのデータベースを**[こちら](https://drive.google.com/file/d/1Jod-iFufGW3lIyqttlws9hOqK4k79ha8/view?usp=sharing)**からダウンロードし、中身を `DLfilter/database/` に展開します（約 130 MB、展開後は約 1 GB）。
> ビルド済みデータベースは 2026-10-09 時点のものです。後で[自分で更新](docs/database.md#update-database)することをおすすめします（英語のドキュメント）。

- 自分でデータベースを初期化します。手順は[こちら](docs/database.md#initialize-database)（英語のドキュメント）。

4. セットアップを確認します（任意）。バージョン、パス、データベースの状態を表示します。`--model` を付けると埋め込みモデルもオフラインで読み込みます:
```bash
uv run python -m module.doctor     # または: python -m module.doctor
```

5. サーバーを起動します
```bash
uv run python app.py               # または: python app.py
# 同等: uvicorn app:app --port 8000
```
`http://localhost:8000/` でサイトにアクセスできます。

### 設定
設定はすべて任意の環境変数です:

| 変数 | 既定値 | 説明 |
| --- | --- | --- |
| `DLFILTER_DATA_DIR` | `./database` | `works.sqlite` とジャンルファイルがあるディレクトリ |
| `DLFILTER_PRESETS_DIR` | `./presets` | プリセットを保存するディレクトリ |
| `DLFILTER_HOST` | `127.0.0.1` | `python app.py` が待ち受けるアドレス |
| `DLFILTER_PORT` | `8000` | `python app.py` が待ち受けるポート |
| `DLFILTER_MODEL` | `sonoisa/sentence-luke-japanese-base-lite` | `initial.py` の埋め込みモデル（Hugging Face の ID またはローカルディレクトリ） |

### Docker
イメージは既存のデータベースを提供するだけで、起動時に何もダウンロードやクロールをしません。非 root ユーザーで動作し、`./database` を読み取り専用でマウントし、プリセットは名前付きボリュームに保存します。
```bash
docker compose up -d               # http://localhost:8000/ で提供（127.0.0.1 にバインド）
```
コンテナ内でローカルのモデルを使ってデータベースを更新する（モデルをダウンロードしない）方法は、[compose.yaml](compose.yaml) の `update` サービスを参照してください。

### テスト
```bash
uv run pytest
```
テストは小さな一時データベースを使い、実データやモデルは不要です。GitHub Actions が Linux、macOS、Windows で Python 3.11 と 3.14（Linux では 3.12 と 3.13 も）で実行します。

## 使い方
DLfilter の使い方はとても簡単です。**ジャンル**または**指定した作品**から類似作品を検索できます。目安として、類似度が 70% を超える作品は多くの場合関連しています。

### タイトル、サークル、RJ 番号で作品を探す
検索パネルの**作品を探す**タブを使います。検索対象（すべて、タイトル、サークル、RJ 番号）と年齢区分を選び、Enter を押します。
- すべての語に一致する必要があります。全角・半角と大文字・小文字は区別しません。
- 完全一致する RJ 番号が最初に、次に完全一致するタイトル、入力で始まるタイトル、その他の順に表示されます。
- 結果の**似た作品を探す**を押すと、その RJ 番号・ジャンル・作品形式が**似た作品を探す**タブに入力されます。調整してから類似度検索を始められます。
- **サイコロ**ボタンは、選んだ年齢区分でランダムな作品を表示します。リセットボタンはすべての検索を消去してウェルカムページに戻ります。

この検索は**ローカルデータベースのみ**が対象です。そのため、最後の更新以降に発売された作品や、DLsite の他のカテゴリの作品（収集しているのは `maniax` のみ）は分かりません。結果は類似度順ではないので、類似度のスコアは表示されません。

### 似たジャンルから
> **重要**: ここで追加したジャンルが検索結果に表示されるとは*限りません*。これらは検索の「種」として扱われるためです。

好きなジャンルを追加します。DLfilter はそれを検索クエリとして（追加したジャンルの単語埋め込みの平均を取って）使い、似たジャンルを持つ作品を返します。

ジャンルは 2〜6 個がおすすめです。多すぎても少なすぎても、最良の結果にならないことがあります。

![image](docs/images/usage1.png)

### 指定した作品から
どのジャンルを追加すればよいか分からない場合は、作品から検索できます。RJ 番号（例: `RJ123456`）を入力するだけで、DLfilter が自動的にそのジャンルを取得し、似た作品を返します。

その ID がローカルデータベースにない場合は、データベースが古い、レコードが欠けている、または作品が DLsite の別カテゴリにある可能性があります。

![image](docs/images/usage2.png)

### ジャンルの絞り込み
結果に必ず含めたい・除外したいジャンルがある場合は、「含めるジャンル」「除外するジャンル」の欄で設定できます。

![image](docs/images/usage3.png)

ここで設定したジャンルは検索用のジャンルでは*ありません*。結果の絞り込みにだけ使われます。

### プリセット
**似た作品を探す**タブの**検索**の隣にあるボタンで、RJ 番号、ジャンル、作品形式、詳細オプションを保存・読み込みできます。プリセットはプロジェクトの `presets/` フォルダにある JSON ファイルです（`DLFILTER_PRESETS_DIR` で別のフォルダも指定できます。Docker 構成では `presets` ボリュームに保存されます）。**プリセットを読み込む**はそのフォルダの内容を一覧表示し、他の場所にあるプリセットファイルも開けます。

### ランダムな作品
**検索**の下にある**ランダム**は、今いるタブの絞り込み条件に合うランダムな作品を表示します。**リセット**はすべてを消去してウェルカムページに戻ります。

### 言語とテーマ
右上の丸いボタンで、言語（英語、日本語、繁体字中国語、簡体字中国語、そして英語に戻る）とライト/ダークテーマを切り替えられます。保存された選択がない場合は、ブラウザの言語が使われます。

## HTTP API
サイトは JSON API の薄いクライアントなので、スクリプトから利用できます。サーバー実行中は `/docs` で対話式のドキュメントを見られます。

| エンドポイント | 説明 |
| --- | --- |
| `GET /api/info` | データベースの作品数と最終更新日時 |
| `GET /api/locale/{locale}` | ジャンルと作品形式の名称（`en_US`、`ja_JP`、`zh_TW`、`zh_CN`、`ko_KR`） |
| `GET /api/works?rj_id=...` | 最大 50 件の作品の詳細。不明な ID は `missing` に列挙 |
| `GET /api/search` | 年齢絞り込みとページング付きのタイトル / サークル / RJ 番号検索 |
| `GET /api/random` | ランダムな作品。類似度検索の絞り込みも指定可能 |
| `POST /api/similarity` | ジャンルまたは指定した作品による類似度検索 |
| `GET /api/presets`、`GET` / `PUT /api/presets/{name}` | プリセットの一覧、読み込み、保存 |

