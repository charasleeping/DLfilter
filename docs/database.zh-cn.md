# 作品数据库
DLfilter 的作品数据库目录结构如下：
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
> 这些文件并未包含在本项目中，您需要自行创建或下载。
> 
> 请注意，`dates_table.json` 与 `works_table.json` 不是必需的文件，但是如果您希望自行创建数据库，则需要这两个文件。

## 数据库管理
### 初始化数据库
DLfilter 需要一个作品数据库才能开始运行。

初次使用时，您可以直接从 **[Mega](https://mega.nz/file/rk4CVbrK#sfJd5F5RX-7wlQjq7PTS4aW5FhmHBKDyc0-HNvG3Jqk)** 下载预先创建好的数据库（最后更新：2026-10-10；收录 2000-01-01 起、只有日文标题的原作，约 190 MB，解压后约 1.2 GB）。下载后，请将文件解压到 `DLfilter/database` 目录下，或用 `python -m module.fetch_database --file <zip>` 安装该 zip。它与启动器、`python -m module.fetch_database` 默认下载的是同一个文件，不含翻译作品与翻译标题，也不含原始目录（`works_table.json`），因此无法用 `initial.py -u` 更新，也无法加入[翻译](#翻译版本)；若要如此，请用 `initial.py -i` 自行创建。

如果您希望自行创建数据库，请运行 `initial.py -i` 来初始化数据库。运行时，请确保您的环境中已经安装了所需的包（包含 `update` 额外依赖）：
```bash
cd DLfilter
uv sync --extra update             # 或：pip install -r requirements.txt
```
然后
```bash
uv run python initial.py -i        # 或：python initial.py -i
```
程序会询问您要收集的日期范围。请按 `YYYY-MM-DD` 格式输入您希望的一个或一段日期：
- `2022-01-01` 或 
- `2022-01-01 2022-01-31`（以空格分隔）

程序会自动爬取该日期范围内发售的所有作品数据，并创建数据库。失败的请求会以递增的间隔重试数次。

首次创建数据库时，程序会自动下载语言模型以生成标签的词向量嵌入，这可能需要一些时间。默认使用 [sonoisa/sentence-luke-japanese-base-lite](https://huggingface.co/sonoisa/sentence-luke-japanese-base-lite)。您可以通过增加 `--model model_name` 参数（或设置 `DLFILTER_MODEL`）来使用 [Hugging Face](https://huggingface.co/) 上的其他语言模型。

若要离线使用，请传入模型的本地目录而非名称，并禁止 Hugging Face 联网：
```bash
HF_HUB_OFFLINE=1 python initial.py -u --model /path/to/sonoisa_sentence-luke-japanese-base-lite
```
默认模型需要 `transformers` 4.x；第 5 版无法加载它的 tokenizer，因此锁定文件固定为 `transformers<5`。可运行 `python -m module.doctor --model` 确认模型能否加载。

### 安全保存数据库
`works.sqlite` 会先写入 `works.sqlite.tmp` 并经过检查（完整性、必需列、条数），之后才会将旧文件改名为 `works.sqlite.bak`，再将新文件移入。若过程中发生错误，旧数据库不会被改动。
- 导出前请先停止服务器，避免在读取时替换文件。
- 请预留约 `works.sqlite` 两倍大小的磁盘空间（新文件与备份会同时存在）。
- 若要还原，请停止服务器后将 `works.sqlite.bak` 改名为 `works.sqlite`。

### 更新数据库
如果您已经有了数据库，可以使用 `-u` 或 `--update` 参数将数据库更新至最新状态：
```bash
python initial.py -u
```
假设今天是 2022-01-01，而更新前的数据库只收录到 2021-12-01 发售的作品，则程序会自动收集 2021-12-02 到 2022-01-01 间发售的作品数据到数据库。同一天再次运行 `-u` 会重新收集昨天的作品，以更新它们的数据。

如果您需要更新特定日期的数据库，请使用 `-d` 或 `--date` 参数：
```bash
# 更新 2022-01-01 发售的作品
python initial.py -d 2022-01-01 

# 更新 2022-01-01 到 2022-01-31 间发售的作品
python initial.py -d 2022-01-01 2022-01-31
```
使用 `-d` 且范围超过 31 天时，会先要求确认，因为爬取需要很长的时间。

日期之后，`-u` 与 `-d` 会询问是否一并获取翻译（见下）。把语言写在命令后面（`-u EN TC`、`-d 2022-01-01 EN`）可跳过此问题，`NONE` 或 `JA` 表示只更新原作，加上 `-s` 则跳过所有问题。

### 翻译版本
> **警告**：获取翻译需要很长的时间。首次用 `EN TC SC` 运行可能需要数小时，因为程序要向 DLsite 逐一查询作品，而 DLsite 会拒绝速度过快的用户。建议先用 `-k titles` 或 `--limit`；可以中断并继续，之后的更新只会查询新作品。

每日作品列表只有各作品的日文标题。官方的英文、繁体中文与简体中文标题需另外收集，才能用它们搜索作品。请把语言列在 `-u` 后面，或 `-d` 的日期后面：
```bash
python initial.py -u                  # 日期之后询问语言
python initial.py -u EN TC SC         # 先更新原作，再获取三种翻译
python initial.py -u EN -k titles     # 只获取多语言作品的英文标题（快）
python initial.py -u NONE             # 只更新原作，不询问
python initial.py -d 2022-01-01 2022-01-31 EN TC
python initial.py -u EN --limit 500 --workers 4
```
可使用 `JA`（只更新原作）、`EN`、`TC`、`SC` 与 `NONE`，以空格或逗号分隔。若原作已是最新，`-u` 会直接处理翻译，这也是为已有数据库获取翻译的方法。

共有两种，以 `-k/--kinds titles editions` 选择（默认两者都做）。`titles`：同一个作品编号下提供多种语言的作品（例如 RJ01722990），各语言显示不同标题，这些标题记录在 `title_table.json`，并存入 `name_ENG`、`name_CHI_HANT`、`name_CHI_HANS` 列。这是较快的部分，46 万件作品的数据库约需 11,000 次请求。`editions`：以独立作品编号发布的翻译版本（如「[ENG Ver.]」）按语言列出，记录在 `translation_table.json`。这是较慢的部分，首次运行需要数万次请求。

程序会逐一查询尚未见过的作品，从最新的开始，并以 `--workers` 个并行请求（默认 6）、整体每秒不超过 `--rate` 次请求（默认 4；DLsite 会拒绝速度过快的用户，请谨慎调高）进行。用来查找翻译版本的列表页面每秒最多获取一次。进度条会显示速度与剩余时间。若 DLsite 返回 HTTP 403 或 429，所有请求会先暂停（30 秒，每次加倍），且本次运行的速度减半，连续失败五次后程序会显示消息并停止；请稍后再重新运行。可随时用 Ctrl-C 中断；重新运行时会继续进度。中断或失败后，程序会询问是否按已保存的进度重建 `works.sqlite`（加上 `-s` 则直接重建；没有终端时不重建）。也可以之后用 `python initial.py -u NONE --no_genre` 重建，不需要爬取。更新原作时也会重建 `works.sqlite`，因此使用 `--limit` 的部分运行也能让已收集的标题可被搜索。

以独立编号发布的翻译版本会存成独立的一行：复制原作的标签、评分、下载数与简介，但使用自己的编号、标题、社团、发售日与选项。只有原作在数据库中时才会加入。

通过翻译标题找到的卡片上会出现开关，可改看原作标题。在此功能之前创建的数据库仍可照常使用，只是没有此开关。

### 移除数据
`-r/--remove` 会先显示将删除的内容并要求确认（默认为否）：
```bash
python initial.py -r EN SC   # 移除英文与简体中文翻译，然后重建数据库
python initial.py -r ALL     # 删除 works.sqlite，即所有作品
python initial.py -r         # 询问要移除什么
```
`-r ALL` 会保留 `works.sqlite.bak`、原始目录、标签文件与翻译表，之后可用 `-u` 重建数据库。原作无法单独移除（`-r JA` 会被拒绝），因为翻译的数据行依赖原作。

### 检查日期
`-c/--check` 会打印出目录中记录的日期后退出。它此前是 `-s/--show`；现在 `-s/--skip` 会以默认值回答所有问题，没有终端时（例如 Docker 的 `update` 任务）需要使用它。

### 高级选项
使用 `-h` 或 `--help` 参数来查看所有可用的参数：
```bash
python initial.py -h
```
```
usage: initial.py [-h] (-i | -c | -u [LANG ...] | -d DATE|LANG [DATE|LANG ...] | -r [TARGET ...])
       [-k {titles,editions} ...] [-s] [--path PATH]
       [--workers WORKERS] [--rate RATE] [--limit LIMIT] [--model MODEL] [--no_genre] [--raw_only]
```

## 数据库文件说明
下面说明各文件的用途。
- `dates_table.json`: 该文件记录了数据库爬取各作品的时间，以便计算下次爬取的时间。其结构如下：
```json
{
    "2000-01-01": "2022-01-01 00:00:00",
}
```
其中，`2000-01-01`是作品发售日，`2022-01-01 00:00:00`是上次爬取的时间。

- `genre_table.json`: 该文件记录了所有属性标签的编号、名称、数量、以及所属的类别。其结构如下：
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
其中，`509`是标签的编号，`category`是标签的类别，`name`是标签的名称，`count`是标签的数量。标签的类别与名称有多种语言，需通过语言代码（如`ja_JP`）选择。请同时参阅 [module.dlsite.GenreCatalog](../module/dlsite.py)。

- `genre_vec.pkl`: 该文件记录了所有属性标签的向量嵌入。
- `title_table.json`: 记录同一编号下提供多种语言之作品的官方翻译标题，以作品编号为键：`{"ENG": "...", "CHI_HANT": null}`。`null` 表示与日文标题相同。
- `translation_table.json`: 该文件记录了 `initial.py -u EN TC SC` 找到的翻译版本，以版本的作品编号为键：`lang`（`ENG`、`CHI_HANT` 或 `CHI_HANS`）、`originalWorkno`、`originalLang`，以及该版本的 `name`、`maker`、`makerId`、`registDate`、`options` 与 `siteId`。非翻译版本的作品会记为 `{"lang": null}`，以免重复查询。
- `workformat.json`: 该文件记录了所有作品类别的代号、名称与所属的父类别。其结构如下：
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
其中，`ACN`是作品类别的代号，`category`是作品类别的父类别，`name`是作品类别的名称。作品类别的父类别与名称有多种语言，需通过语言代码（如`ja_JP`）选择。

- `works.sqlite`: 该文件是 SQLite 作品数据库，记录了作品搜索所必需的 metadata。相似作品搜索与作品名／社团／RJ 号搜索都会读取它；后者只能找到此处收集的作品（DLsite `maniax`，截至上次更新）。
  翻译版本的行另有可选列 `lang`、`originalWorkno`、`originalLang` 与 `originalName`，其他作品这些列为 NULL。可选列 `name_ENG`、`name_CHI_HANT`、`name_CHI_HANS` 存放多语言作品的翻译标题。
- `works_table.json`: 该文件记录了所有作品的完整 metadata，由于数据量庞大，因此不建议直接打开。
