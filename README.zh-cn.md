<h1 align="center">DLfilter</h1>

<p align="center">
  <b>按作品给人的感觉，而不只是名称，来寻找 DLsite 作品。</b><br>
  DLsite 的标签语义搜索引擎，附带快速的本地作品搜索、四种语言与一键 Docker。
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
  <a href="README.md">English</a> | <a href="README.jp.md">日本語</a> | <a href="README.zh-tw.md">正體中文</a> | 简体中文
</p>

DLfilter 将 DLsite 的标签（类型，例如 `治愈`、`纯爱`）当作词语做嵌入，因此即使两部作品没有任何相同标签，也能找到类型在*语义上相近*的作品。它也能按标题（日文、英文或中文）、社团名称或 RJ 编号搜索本地数据库，并能从任何一条结果开始相似作品搜索。

本仓库是 [charasleeping](https://github.com/charasleeping/DLfilter) 对 [snowmeow2 的 DLfilter](https://github.com/snowmeow2/DLfilter) 的重启分支。相似度搜索与构想均出自原作者；本分支让它能在当前的 Python 与库上运行，并加入了[本分支的新功能](#本分支的新功能)中列出的内容。

不一定会定期维护。欢迎随意 fork 或提 PR。

目前尚未支持 BJ 与 VJ 作品编号，预计在 2026 年 11 月底前支持。

## 目录
[功能](#功能) | [本分支的新功能](#本分支的新功能) | [安装](#安装) | [使用方法](#使用方法) | [HTTP API](#http-api) | [路线图](#路线图) | [已知问题](#已知问题) | [致谢](#致谢)

## 功能

### 搜索
| | |
| --- | --- |
| **查找作品** | 按标题、社团名称或 RJ 编号搜索本地数据库。不区分全角半角与大小写，且每个词都必须匹配。 |
| **按翻译标题查找** | 也能用官方的英文、繁体中文与简体中文标题找到作品。以此找到的卡片上有一个小开关，可改看原作标题。 |
| **查找相似作品** | 按一组类型或指定作品搜索，并按类型的语义相似度排序。 |
| **随机作品** | 从数据库随机抽出作品，可按年龄分级筛选（在**查找相似作品**标签页则应用其所有筛选条件）。 |
| **从任何结果查找相似作品** | 点击一下结果即可把其 RJ 编号、类型与作品形式带入**查找相似作品**标签页。 |

### 调整结果
- 按热门程度加权类型（偏好冷门或热门的类型）。
- 按下载数与发售日期加权结果。
- 包含或排除特定类型，并可按作品形式筛选。
- 按年龄分级筛选，并可排除 AI 生成、部分 AI 生成、低评价、猎奇或男同性恋作品。

### 好用的细节
- **预设**：保存整组搜索设置（RJ 编号、类型、作品形式、高级选项），之后再加载，也可从任何位置打开预设文件。
- **四种语言**：一键切换英文、日文、繁体中文与简体中文。类型与作品形式名称采用 DLsite 官方翻译，界面用词也遵循 DLsite。
- **亮色与暗色主题**，带平滑过渡。语言与主题都会由浏览器记住。
- 在自己的电脑上以本地 SQLite 数据库运行，也提供 Docker 配置。

DLfilter *无法*按热门程度搜索作品，因为那需要实时更新的数据库，而这是不可能的（显然无法访问 DLsite 的数据库）。但是，我相信热门的不一定是你想要的。

## 本分支的新功能
与 [snowmeow2/DLfilter](https://github.com/snowmeow2/DLfilter) 相比：

| 项目 | 原版 | 本分支 |
| --- | --- | --- |
| **搜索** | 仅有相似度搜索 | 新增**查找作品**（标题 / 社团 / RJ 编号，含排序）、**随机作品**，以及从任何结果**查找相似作品** |
| **界面** | 单一搜索面板；语言跟随浏览器 | 标签页式搜索面板、重置与随机按钮、**语言切换**（EN / JA / zh-TW / zh-CN，采用 DLsite 用词）、亮暗主题、预设 |
| **预设** | 无 | 以 JSON 文件保存、加载与导入搜索设置（含校验，最多 200 个） |
| **Python** | 3.10 | **3.11 - 3.14**，支持 Linux、macOS 与 Windows |
| **依赖** | 未锁定版本的 `requirements.txt` | `pyproject.toml` + `uv.lock`（锁定版本）、供 pip 使用的自动生成 `requirements.txt`、Linux 使用仅 CPU 的 PyTorch |
| **运行方式** | `uvicorn app:app` | 另可用 `python app.py`、以 `DLFILTER_*` 环境变量配置、路径不受工作目录影响 |
| **Docker** | 无 | `Dockerfile` 与 `compose.yaml`（非 root、只读数据库、预设卷、可选的离线 `update` 任务） |
| **数据库安全** | 直接原地写入 | 网站使用只读连接；导出先写入临时文件、检查后再以 `.bak` 备份换入 |
| **爬取** | 无限重试 | 请求超时、有上限的指数退避、爬取超过 31 天前需要确认 |
| **翻译** | 只有日文标题 | 可用官方的英文 / 繁体中文 / 简体中文标题搜索，涵盖同一编号下提供多种语言的作品，以及有独立编号的翻译版本，卡片上有标题切换开关。用 `initial.py -u EN TC SC` 收集 |
| **翻译爬取** | 无 | 并行查询并限制速率，DLsite 返回 403 或 429 时自动放慢；进度条、可继续的运行，以及中断后询问是否重建数据库 |
| **`initial.py` 选项** | `-i`、`-s`、`-u`、`-d` | `-c` 检查日期，`-u` 可在同一天重复运行，`-r` 移除翻译或所有作品，`-u` 与 `-d` 接受语言，`-k` 选择种类，`-s` 跳过所有问题，`--workers`、`--rate`、`--limit` 调整爬取 |
| **模型** | 需要时才下载 | 可从本地模型文件夹完全离线运行；为默认模型的 tokenizer 固定 `transformers<5` |
| **运行时负担** | 导入 `sentence-transformers` | 网站不再导入它（用 PyTorch 计算余弦相似度），只有 `initial.py` 需要 |
| **诊断** | 无 | `python -m module.doctor` 检查版本、路径、数据，加上 `--model` 时还会检查嵌入模型 |
| **测试** | 无 | 基于小型临时数据库的超过 120 个 `pytest` 测试，由 GitHub Actions 在 Linux、macOS 与 Windows（Python 3.11 - 3.14）上运行 |
| **修复** | 使用已弃用的 Pydantic / FastAPI / pandas 调用 | 更新至当前版本；静态文件按修改时间更新缓存；错误响应不再泄露内部信息 |

`recover_works_table_download.py` 还能在不改动原文件的情况下，从被截断的 `works_table.json`（例如下载中断后）中挽救完整的记录。

## 安装
以下说明适合想在自己的电脑或服务器上部署 DLfilter 的人。

支持 Python 3.11 – 3.14（已在 Linux、macOS 与 Windows 测试）。

#### 快速开始（发行版 zip）
1. 从 [Releases](https://github.com/charasleeping/DLfilter/releases) 页面下载 `DLfilter-vX.Y.Z.zip` 并解压。
2. 双击 `start.bat`（Windows）或 `start.command`（macOS；第一次请右键点击并选择**打开**；Linux 请运行 `./start.command`）。

启动器会先询问再安装 [uv](https://docs.astral.sh/uv/)，接着安装依赖（第一次约 1 GB）、下载预先建好的数据库（只有原作，约 470 MB），并在浏览器中打开网站。不含翻译（只有日文标题的原作）：如何自行获取翻译，请见[管理数据库](#管理数据库)。设置 `DLFILTER_DB_URL` 可从其他位置下载数据库；已有 zip 时可运行 `python -m module.fetch_database --file works-db.zip` 安装。

#### 从源码安装
1. 克隆仓库：
```bash
git clone https://github.com/charasleeping/DLfilter
cd DLfilter
```

2. 安装依赖。可使用 [uv](https://docs.astral.sh/uv/)（推荐，使用 `uv.lock` 中锁定的版本）：
```bash
uv sync --extra update     # 只运行网站的话可省略 "--extra update"
```
或在虚拟环境中使用 pip：
```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell：.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
`update` 额外依赖（已包含在 `requirements.txt`）只有 `initial.py` 会用到。Linux 上会安装仅 CPU 的 PyTorch。

3. 初始化数据库。有两种方式：
- 从 [Mega](https://mega.nz/file/D4Q3jJYR#UrUQep6zSEqHJ0dZh2LUuGOF6YhO4p07YAjtxbRyaXw) 下载预先建好的数据库（最后更新：2026-10-10），并将内容解压到 `DLfilter/database/`（只有原作，约 470 MB，解压后约 1.2 GB），或用 `python -m module.fetch_database --file <zip>` 安装该 zip
> 下载内容包含截至 2026-10-10 的原作，只有日文标题，因此没有翻译作品，也不能用翻译标题搜索。它包含原始目录，所以可以照常用 `python initial.py -u` 更新，并用 `python initial.py -u EN TC SC` 获取翻译；获取翻译可能需要很长的时间，请见[管理数据库](#管理数据库)。

- 自行初始化数据库。请参阅[这里](docs/database.zh-cn.md#初始化数据库)。

4. 检查配置（可选）。会显示版本、路径与数据库状态；加上 `--model` 还会离线加载嵌入模型：
```bash
uv run python -m module.doctor     # 或：python -m module.doctor
```

5. 启动服务器
```bash
uv run python app.py               # 或：python app.py
# 等同于：uvicorn app:app --port 8000
```
接着就能在 `http://localhost:8000/` 打开网站。

### 配置
所有设置都是可选的环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DLFILTER_DATA_DIR` | `./database` | 存放 `works.sqlite` 与类型文件的目录 |
| `DLFILTER_PRESETS_DIR` | `./presets` | 保存预设的目录 |
| `DLFILTER_HOST` | `127.0.0.1` | `python app.py` 监听的地址 |
| `DLFILTER_PORT` | `8000` | `python app.py` 监听的端口 |
| `DLFILTER_MODEL` | `sonoisa/sentence-luke-japanese-base-lite` | `initial.py` 使用的嵌入模型：Hugging Face ID 或本地目录 |

### Docker
镜像只提供已有的数据库，启动时不会下载或爬取任何东西。它以非 root 用户运行，以只读方式挂载 `./database`，并把预设保存在具名卷中。
```bash
docker compose up -d               # 在 http://localhost:8000/ 提供服务（绑定 127.0.0.1）
```
若要在容器中使用本地模型（不下载模型）更新数据库，请参阅 [compose.yaml](compose.yaml) 中的 `update` 服务。该服务运行 `initial.py -u -s`，因此所有问题都用默认值回答（只更新原作，不获取翻译）。

### 测试
```bash
uv run pytest
```
测试使用小型临时数据库，不需要真实数据或模型。GitHub Actions 会在 Linux、macOS 与 Windows 上以 Python 3.11 与 3.14 运行（Linux 另含 3.12 与 3.13）。

## 使用方法
DLfilter 有两种找作品的方式：按**名称**（标题、社团或 RJ 编号，支持日文、英文与中文），或按**相似度**（一组类型或指定作品）。经验上，相似度超过 70% 的作品通常彼此相关。

### 启动网站
双击 `start.bat`（Windows）或 `start.command`（macOS、Linux），或在项目文件夹运行：
```bash
python app.py            # 在 http://localhost:8000/ 提供服务
python app.py --open     # 并在浏览器中打开
uv run python app.py     # 使用 uv 时的等同命令
```
设置 `DLFILTER_HOST` 与 `DLFILTER_PORT` 可改变监听位置（见[配置](#配置)）。

### 按标题、社团或 RJ 编号查找作品
使用搜索面板的**查找作品**标签页。选择搜索范围（全部、标题、社团或 RJ 编号）与年龄分级，然后按 Enter。
- 每个词都必须匹配。不区分全角半角与大小写。
- 完全匹配的 RJ 编号排最前，其次是完全相同的标题、以输入文字开头的标题，最后是其余结果。
- 对结果点**查找相似作品**，会把它的 RJ 编号、类型与作品形式带入**查找相似作品**标签页，你可以调整后再开始相似度搜索。
- **骰子**按钮会按所选年龄分级显示随机作品。重置按钮会清除所有搜索并回到欢迎页面。

此搜索*仅限本地数据库*，因此不会知道上次更新后才发售的作品，也不含 DLsite 其他分类的作品（只收集 `maniax`）。结果不是按相似度排序，所以不显示相似度分数。

### 按翻译标题查找作品
也能用官方的英文、繁体中文与简体中文标题找到作品；例如搜索 `Interactive Mii` 可以找到 `ふれあいミイちゃん`。通过翻译找到的卡片会显示那个标题，缩略图右上角有一个小小的半透明开关。滑动它即可改看原作标题；开关上的字符与语言按钮相同（A、あ、繁、简）。若你是以原作的语言搜索，就不会出现这个开关。

这需要包含翻译的数据库，例如预先建好的那份（见[管理数据库](#管理数据库)）。在此功能之前建立的数据库仍可照常使用，只是没有翻译标题。

### 按相似类型
> **重要**：在此添加的类型*不一定*会出现在搜索结果中，因为它们是搜索的“种子”。

添加你喜欢的类型。DLfilter 会把它们当作搜索查询（取所添加类型词嵌入的平均值），并返回类型相近的作品。

建议添加 2-6 个类型。太多或太少都可能得不到最好的结果。

### 按指定作品
如果你不知道要添加哪些类型，可以改用作品搜索。只要输入 RJ 编号（例如 `RJ123456`），DLfilter 就会自动获取它的类型并返回相似作品。

若该编号不在本地数据库中，可能是数据库过旧、记录缺失，或该作品属于 DLsite 的其他分类。

### 筛选类型
如果有些类型必须包含或排除在结果中，可以在“包含的类型”与“排除的类型”字段设置。

请注意，在此设置的类型*不是*用来搜索的类型，只用来筛选结果。

### 预设
**查找相似作品**标签页中**搜索**旁的按钮可保存与加载 RJ 编号、类型、作品形式与高级选项。预设是项目 `presets/` 文件夹中的 JSON 文件（设置 `DLFILTER_PRESETS_DIR` 可改用其他文件夹；Docker 配置把它们保存在 `presets` 卷）。**加载预设**会列出该文件夹的内容，也能从其他位置打开预设文件。

### 随机作品
在**搜索**下方，**随机**会按你所在标签页的筛选条件显示随机作品，**重置**则会清除所有内容并回到欢迎页面。

### 语言与主题
右上角的圆形按钮可切换语言（英文、日文、繁体中文、简体中文，然后回到英文）与亮暗主题。若没有保存过选择，DLfilter 会使用浏览器的语言。语言按钮会显示当前的语言，按下后滑动切换到下一个语言。

### 管理数据库
请在项目文件夹运行以下命令（使用 uv 时在前面加上 `uv run`）。`initial.py` 需要 `update` 额外依赖（`uv sync --extra update` 或 `pip install -r requirements.txt`）；启动器脚本不会安装它。

> 更新需要原始目录 `database/works_table.json`（约 2.6 GB），预先建好的下载已包含它，所以安装后可直接用 `-u`，并以 `-u EN TC SC` 添加翻译。只有要自己建立目录时才需要 `python initial.py -i`；它会爬取你输入的起始日期之后的每一天，需要数小时以上。

> **警告**：获取翻译需要很长的时间。首次运行时，光是用 `EN TC SC` 更新一次就可能需要数小时，因为程序要向 DLsite 逐一查询作品，而 DLsite 会拒绝速度太快的用户，所以默认速度刻意设得保守。建议先用 `-k titles` 或 `--limit` 开始，然后让它跑；可以中断并继续。之后的更新只会查询新作品，会短很多。

| 想做的事 | 命令 |
| --- | --- |
| 下载并安装预先建好的数据库 | `python -m module.fetch_database`（`--file works-db.zip` 安装已有的 zip，`--force` 覆盖） |
| 检查配置 | `python -m module.doctor`（加上 `--model` 还会加载嵌入模型） |
| 从头建立数据库 | `python initial.py -i`（会询问日期范围） |
| 查看已记录的日期 | `python initial.py -c` |
| 更新到昨天 | `python initial.py -u`（会询问是否一并获取翻译） |
| 更新，并获取英文与中文标题 | `python initial.py -u EN TC SC` |
| 只更新原作 | `python initial.py -u NONE` |
| 只获取翻译中较快的部分 | `python initial.py -u EN TC SC -k titles` |
| 只爬取一天 | `python initial.py -d 2026-10-01` |
| 爬取一段范围并获取翻译 | `python initial.py -d 2026-10-01 2026-10-10 EN TC SC` |
| 分次小量进行 | `python initial.py -u EN --limit 500 --workers 4 --rate 2` |
| 按已保存的数据重建数据库 | `python initial.py -u NONE --no_genre` |
| 移除某些语言的翻译 | `python initial.py -r EN SC` |
| 移除数据库中的所有作品 | `python initial.py -r ALL` |
| 不询问直接运行（脚本、Docker） | `python initial.py -u EN TC SC -s`，或 `docker compose run --rm update -u EN TC SC -s` |
| 用本地模型离线更新 | `HF_HUB_OFFLINE=1 python initial.py -u --model /path/to/model` |
| 救回被截断的 `works_table.json` | `python recover_works_table_download.py` |

语言可用 `JA`（原作，不需额外获取）、`EN`、`TC`、`SC` 与 `NONE`，用空格或逗号分隔。`-u` 与 `-d` 会先更新原作，再获取你指定的翻译；没有指定语言时会询问。使用 `-d` 时，语言写在日期之后。

| 选项 | 含义 |
| --- | --- |
| `-k`、`--kinds` | `titles`（同一编号下提供多种语言的作品，较快）和或 `editions`（有独立编号的翻译版本，较慢）；默认两者都做 |
| `-s`、`--skip` | 以默认值回答所有问题（没有终端时需要） |
| `--workers`、`--rate`、`--limit` | 并行请求数（6）、整体每秒请求数（4）、每次运行最多查询的作品数 |
| `--path`、`--model`、`--no_genre`、`--raw_only` | 数据库文件夹、嵌入模型、跳过类型更新、跳过重建 `works.sqlite` |

运行时会显示进度条，可以按 Ctrl-C 中断并继续，在 DLsite 返回 403 或 429 时会自动放慢，中断后也会询问是否重建数据库。同一天运行两次 `-u` 没有问题。重建前请先停止网站，并预留约 `works.sqlite` 两倍大小的磁盘空间。详见 [docs/database.zh-cn.md](docs/database.zh-cn.md)。

## HTTP API
网站是 JSON API 的轻量客户端，因此你可以用脚本调用它。服务器运行时，交互式文档位于 `/docs`。

| 端点 | 说明 |
| --- | --- |
| `GET /api/info` | 数据库的作品数量与最后更新时间 |
| `GET /api/locale/{locale}` | 类型与作品形式名称（`en_US`、`ja_JP`、`zh_TW`、`zh_CN`、`ko_KR`） |
| `GET /api/works?rj_id=...` | 最多 50 部作品的详细信息；未知的编号列在 `missing` |
| `GET /api/search` | 含年龄筛选与分页的标题 / 社团 / RJ 编号搜索；通过翻译标题找到的结果会附带 `lang`、`originalName`、`originalLang` 与 `titleToggle` |
| `GET /api/random` | 随机作品，可搭配相似度搜索的筛选条件 |
| `POST /api/similarity` | 按类型或指定作品的相似度搜索 |
| `GET /api/presets`、`GET` / `PUT /api/presets/{name}` | 列出、读取与保存预设 |
