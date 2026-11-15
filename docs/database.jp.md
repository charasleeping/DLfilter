# 作品データベース

通常の導入は [インストールガイド](installation.md) のブラウザー設定を使ってください。検索用 ZIP に元の履歴や pickle は不要です。「カタログ設定」でタイトルをバックグラウンド収集できます。以下はカタログ全体の保守向けです。

## ネイティブサーバーと移植可能なベクトル

通常の起動は Rust 実行ファイルを使います。配布版は `start.command` / `start.bat`、ソース版は先に `cargo build --release --locked` を実行してください。収集と埋め込み生成は引き続き Python の保守機能です。旧 Python HTTP 実装は開発テスト専用です。

既存データでは、信頼できるローカルの pickle を一度だけ変換します。

```sh
uv run --extra convert --no-dev python -m module.export_vectors --trusted-pickle database/genre_vec.pkl --output database
```

`genre_vectors.json` と `genre_vectors.f32` が追加され、元の pickle と作品データは保持されます。新しい埋め込み生成では自動出力されます。Rust は pickle を読み込みません。インストーラーは旧アーカイブと追加ファイル付きの両方に対応します。

保守後は `dlfilter prepare`、起動は `dlfilter serve --open`、診断は `dlfilter doctor` を使います。ソース版では `./target/release/` を付け、Windows では `.exe` を使います。検索キャッシュは OS のキャッシュ領域に保存し、`DLFILTER_CACHE_DIR` で変更できます。データは読み取り専用でも使えます。初回準備は通常起動より長くかかります。更新前にサーバーを止め、完了後に再起動してください。配信用 Docker はネイティブで、Compose の更新プロファイルのみ Python を使います。


## 統合検索と RJ BJ VJ の収集

検索はキーワード・タグ・すべての条件を組み合わせます。キーワードと検索タグが空なら新着順で表示し、作品形式の選択も任意です。選択した検索タグはすべて類似度に使います。タグのコピーは既存の選択に追加し、ほかの条件は変更しません。最後にコピーした参照作品は類似検索から除外します。設定は同じブラウザで自動復元され、名前付きプリセットとは別に保存されます。

収集元は `maniax`（RJ）、`books`（BJ）、`pro` と `soft`（VJ）です。既存の RJ のみのデータに BJ/VJ が自動で追加されるわけではありません。期間を明示して収集してください。

```sh
python initial.py -d 2026-09-25 2026-09-25 NONE --sources books pro soft
python initial.py -u NONE --sources maniax books pro soft -s
```

`--sources` の既定は4つすべてです。通常の更新は履歴のある収集元のみを進め、未収集の元には期間指定の案内を表示します。最後の記録日を含め、昨日まで収集します。翻訳の保存内容を反映する更新でも収集が走る場合があります。`--no_genre` はタグ更新のみを省略します。既存の生データに対する `-i` は日付を表示して終了します。

従来の `dates_table.json` は maniax の履歴のみです。`source_dates_table.json` は収集元ごとの日付を記録します。`catalogue_updates.sqlite` は作品と収集済み日付を同じトランザクションで保存し、中断後は JSON の保存前でも復元します。新しい2ファイルも生データと一緒にバックアップし、更新の同時実行は避けてください。

SQLite のテーブル名は互換性のため `maniax` のままです。タグのない作品もキーワード検索・閲覧用に保持します。任意列 `imageUrl` はサムネイルを保存し、旧データは番号の接頭辞で画像を補います。再構築前にサーバーを止め、完了後に再起動してください。旧 `comic` は DLsite 外へ転送されるため収集しません。

DLfilter の作品データベースのディレクトリ構成は次のとおりです。
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
> これらのファイルは本プロジェクトに含まれていません。自分で作成するかダウンロードしてください。
> 
> `dates_table.json` と `works_table.json` は必須ではありませんが、データベースを自分で作成する場合には必要です。

## データベースの管理
### データベースの初期化
DLfilter を動かすには作品データベースが必要です。

初めて使う場合は、作成済みのデータベースを **[Mega](https://mega.nz/file/rk4CVbrK#sfJd5F5RX-7wlQjq7PTS4aW5FhmHBKDyc0-HNvG3Jqk)** からダウンロードできます（最終更新：2026-10-10。2000-01-01 以降の原作を日本語タイトルのみで収録。約 470 MB、展開後は約 3.8 GB）。ダウンロード後、ファイルを `DLfilter/database` に展開するか、`python -m module.fetch_database --file <zip>` で zip をインストールしてください。`python -m module.fetch_database` が既定でダウンロードするのと同じファイルです。ネイティブのランチャーを使う前にデータベースをインストールしてください。翻訳作品や翻訳タイトルは含まれませんが、元のカタログ（`works_table.json`）が含まれているため、これまでどおり `initial.py -u` で更新し、`initial.py -u EN TC SC` で[翻訳版](#翻訳版)を取得できます。自分でカタログを作る場合だけ `initial.py -i` が必要です。

自分で作成する場合は `initial.py -i` を実行します。実行前に、必要なパッケージ（`update` extra を含む）をインストールしてください。
```bash
cd DLfilter
uv sync --extra update             # または: pip install -r requirements.txt
```
続いて
```bash
uv run python initial.py -i        # または: python initial.py -i
```
収集する日付の範囲を尋ねられます。`YYYY-MM-DD` 形式で、1 日または期間を入力してください。
- `2022-01-01` または 
- `2022-01-01 2022-01-31`（スペース区切り）

その期間に発売された全作品のデータを自動で収集し、データベースを作成します。失敗したリクエストは、間隔を延ばしながら数回再試行されます。

初回の作成時には、タグの埋め込みベクトルを作るための言語モデルが自動でダウンロードされるため、時間がかかることがあります。既定では [sonoisa/sentence-luke-japanese-base-lite](https://huggingface.co/sonoisa/sentence-luke-japanese-base-lite) を使います。`--model model_name` 引数（または `DLFILTER_MODEL`）で、[Hugging Face](https://huggingface.co/) 上の別のモデルを指定できます。

オフラインで使う場合は、モデル名の代わりにモデルのローカルディレクトリを指定し、Hugging Face への接続を禁止してください。
```bash
HF_HUB_OFFLINE=1 python initial.py -u --model /path/to/sonoisa_sentence-luke-japanese-base-lite
```
既定のモデルには `transformers` 4.x が必要です。5 系ではトークナイザを読み込めないため、ロックファイルは `transformers<5` に固定されています。`python -m module.doctor --model` でモデルを読み込めるか確認できます。

### データベースの安全な保存
`works.sqlite` はまず `works.sqlite.tmp` に書き出され、検査（整合性・必須列・件数）を通った後で、古いファイルが `works.sqlite.bak` に改名され、新しいファイルが移されます。途中でエラーが起きても、古いデータベースは変更されません。
- エクスポート前にサーバーを停止し、読み込み中にファイルが置き換わらないようにしてください。
- `works.sqlite` の約 2 倍の空き容量を確保してください（新ファイルとバックアップが同時に存在します）。
- 元に戻すには、サーバーを停止して `works.sqlite.bak` を `works.sqlite` に改名します。

### データベースの更新
既にデータベースがある場合は、`-u` または `--update` で最新の状態に更新できます。
```bash
python initial.py -u
```

特定の日付だけを更新したい場合は、`-d` または `--date` を使います。
```bash
# 2022-01-01 発売の作品を更新
python initial.py -d 2022-01-01 

# 2022-01-01 から 2022-01-31 に発売された作品を更新
python initial.py -d 2022-01-01 2022-01-31
```
`-d` で 31 日を超える範囲を指定すると、収集に長い時間がかかるため、先に確認を求められます。

日付の後、`-u` と `-d` は翻訳も取得するか尋ねます（下記参照）。コマンドの後ろに言語を書く（`-u EN TC`、`-d 2022-01-01 EN`）とこの質問を省略でき、`NONE` または `JA` は原作のみの更新、`-s` を付けるとすべての質問を省略します。

### 翻訳版
> **警告**：翻訳の取得にはとても長い時間がかかります。`EN TC SC` での初回実行には数時間かかることがあります。作品を 1 件ずつ DLsite に問い合わせる必要があり、DLsite は速すぎるアクセスを拒否するためです。まず `-k titles` や `--limit` を試すことをおすすめします。中断して再開でき、以降の更新では新しい作品だけを問い合わせます。

日次の作品リストには日本語タイトルしかありません。公式の英語・繁体字中国語・簡体字中国語のタイトルで作品を検索できるようにするには、別途収集が必要です。`-u` の後ろ、または `-d` の日付の後ろに言語を並べてください。
```bash
python initial.py -u                  # 日付の後に言語を尋ねる
python initial.py -u EN TC SC         # 原作を更新してから、3 つの翻訳を取得
python initial.py -u EN -k titles     # 多言語作品の英語タイトルのみ取得（速い）
python initial.py -u NONE             # 原作のみ更新、質問なし
python initial.py -d 2022-01-01 2022-01-31 EN TC
python initial.py -u EN --limit 500 --workers 4
```
使えるのは `JA`（原作のみ更新）、`EN`、`TC`、`SC`、`NONE` で、スペースまたはカンマで区切ります。原作が既に最新なら、`-u` は翻訳だけを処理します。既存のデータベースに翻訳を追加する方法でもあります。

種類は 2 つあり、`-k/--kinds titles editions` で選びます（既定は両方）。`titles`：1 つの作品番号で複数の言語を提供する作品（例：RJ01722990）で、言語ごとにタイトルが異なります。これらは `title_table.json` に記録され、`name_ENG`、`name_CHI_HANT`、`name_CHI_HANS` 列に入ります。こちらは速く、46 万件のデータベースで約 11,000 リクエストです。`editions`：独自の作品番号で公開された翻訳版（例：「[ENG Ver.]」）を言語ごとに列挙し、`translation_table.json` に記録します。こちらは遅く、初回は数万リクエストが必要です。

未確認の作品を新しいものから順に 1 件ずつ問い合わせます。`--workers` 本の並列リクエスト（既定 6）、全体で毎秒 `--rate` リクエストまで（既定 4。速すぎると DLsite に拒否されるため、上げる場合は慎重に）で動作します。翻訳版を探すための一覧ページは毎秒 1 回までです。進捗バーに速度と残り時間が表示されます。DLsite が HTTP 403 または 429 を返すと、全リクエストが一時停止し（30 秒、そのつど倍増）、この実行の速度が半分になります。5 回連続で失敗するとメッセージを表示して停止するので、しばらくしてからやり直してください。Ctrl-C でいつでも中断でき、再実行すると続きから再開します。中断や失敗の後は、保存済みの内容で `works.sqlite` を再構築するか尋ねられます（`-s` ならそのまま再構築、ターミナルがなければ再構築しません）。後から `python initial.py -u NONE --no_genre` で再構築できますが、記録が古い場合は収集も行います。原作の更新でも `works.sqlite` は再構築されるため、`--limit` による部分的な実行でも収集済みのタイトルが検索できるようになります。

独自の番号で公開された翻訳版は独立した 1 行として保存されます。原作のタグ・評価・DL 数・あらすじをコピーし、番号・タイトル・サークル・発売日・オプションは翻訳版自身のものを使います。原作がデータベースにある場合にのみ追加されます。

翻訳タイトルで見つかったカードにはスイッチが表示され、原作のタイトルに切り替えられます。この機能より前に作成されたデータベースもそのまま使えますが、スイッチは表示されません。

### データの削除
`-r/--remove` は、削除される内容を表示して確認を求めます（既定は「いいえ」）。
```bash
python initial.py -r EN SC   # 英語と簡体字中国語の翻訳を削除し、データベースを再構築
python initial.py -r ALL     # works.sqlite、つまりすべての作品を削除
python initial.py -r         # 何を削除するか尋ねる
```
`-r ALL` は `works.sqlite.bak`、元のカタログ、タグファイル、翻訳テーブルを残すので、後で `-u` でデータベースを再構築できます。翻訳の行は原作に依存するため、原作だけを削除することはできません（`-r JA` は拒否されます）。

### 日付の確認
`-c/--check` は、カタログに記録された日付を表示して終了します。以前は `-s/--show` でした。現在の `-s/--skip` はすべての質問に既定値で答えるもので、ターミナルがない場合（Docker の `update` ジョブなど）に必要です。

### 詳細オプション
`-h` または `--help` で、使用できる引数をすべて確認できます。
```bash
python initial.py -h
```
```
usage: initial.py [-h] (-i | -c | -u [LANG ...] | -d DATE|LANG [DATE|LANG ...] | -r [TARGET ...])
       [-k {titles,editions} ...] [-s] [--path PATH]
       [--workers WORKERS] [--rate RATE] [--limit LIMIT] [--model MODEL] [--no_genre] [--raw_only]
```

## データベースファイルの説明
各ファイルの役割を説明します。
- `dates_table.json`: 各作品をいつ収集したかを記録し、次回の収集時期の計算に使います。構造は次のとおりです。
```json
{
    "2000-01-01": "2022-01-01 00:00:00",
}
```
`2000-01-01` は作品の発売日、`2022-01-01 00:00:00` は前回収集した日時です。

- `genre_table.json`: すべての属性タグの番号・名前・件数・所属カテゴリを記録します。構造は次のとおりです。
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
`509` はタグの番号、`category` はタグのカテゴリ、`name` はタグの名前、`count` はタグの件数です。カテゴリと名前は複数の言語で持っており、言語コード（`ja_JP` など）で選びます。[module.dlsite.GenreCatalog](../module/dlsite.py) も参照してください。

- `genre_vec.pkl`: すべての属性タグの埋め込みベクトルを記録します。
- `title_table.json`: 1 つの番号で複数の言語を提供する作品の公式翻訳タイトルを、作品番号をキーにして記録します：`{"ENG": "...", "CHI_HANT": null}`。`null` は日本語タイトルと同じであることを表します。
- `translation_table.json`: `initial.py -u EN TC SC` が見つけた翻訳版を、翻訳版の作品番号をキーにして記録します：`lang`（`ENG`、`CHI_HANT`、`CHI_HANS`）、`originalWorkno`、`originalLang`、そして翻訳版の `name`、`maker`、`makerId`、`registDate`、`options`、`siteId`。翻訳版でない作品は、再度問い合わせないよう `{"lang": null}` として記録されます。
- `workformat.json`: すべての作品形式のコード・名前・親カテゴリを記録します。構造は次のとおりです。
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
`ACN` は作品形式のコード、`category` は親カテゴリ、`name` は作品形式の名前です。親カテゴリと名前は複数の言語で持っており、言語コード（`ja_JP` など）で選びます。

- `works.sqlite`: 作品検索に必要なメタデータを記録した SQLite データベースです。類似作品検索と、作品名／サークル／RJ 番号による検索の両方がこれを読み込みます。後者で見つかるのは、ここに収集された作品（DLsite `maniax`、前回の更新時点まで）だけです。
  翻訳版の行には、任意の列 `lang`、`originalWorkno`、`originalLang`、`originalName` が追加され、他の作品ではこれらは NULL です。任意の列 `name_ENG`、`name_CHI_HANT`、`name_CHI_HANS` には、多言語作品の翻訳タイトルが入ります。
- `works_table.json`: すべての作品の完全なメタデータを記録します。データ量が非常に大きいため、直接開くことはおすすめしません。
