<h1 align="center">DLFilter</h1>

<p align="center"><b>Find DLsite works by what they feel like, not only by what they are called.</b></p>

<p align="center">English | <a href="README.jp.md">日本語</a> | <a href="README.zh-tw.md">正體中文</a> | <a href="README.zh-cn.md">简体中文</a></p>

DLFilter searches a catalogue on your own computer. Combine keywords and filters, or select genres to rank works by semantic similarity. It supports RJ, BJ, and VJ product IDs, four interface languages, light/dark themes, saved presets, and random picks.

The search server runs in Rust; the browser interface uses JavaScript. Normal use requires no Python installation, Rust compiler, account, or embedding-model download. Python remains part of the optional catalogue-maintenance tools and is bundled privately for background title collection.

## Install and launch

1. Download the native ZIP matching your computer from [Releases](https://github.com/charasleeping/DLfilter/releases): Windows x64, Linux x64, macOS Apple Silicon (`arm64`), or macOS Intel (`x86_64`). Extract the entire archive to a writable folder.
2. Open `start.bat` on Windows or `start.command` on macOS. On Linux, run `./start.command` from the extracted folder. The launcher opens DLFilter in your browser at **http://localhost:8000/**.
3. On first launch, choose **Download catalogue** or **Import catalogue ZIP** in the browser. After setup prepares the search indexes, select **Start searching**.

These steps apply to native releases containing browser setup and the private title helper; older releases may use different installation instructions. Automatic download additionally requires the portable serving catalogue and its manifest to be available from the database release. If that download is unavailable, import a compatible serving ZIP. See the [installation guide](docs/installation.md) for troubleshooting and legacy database conversion.

Keep the launcher window open while using DLFilter. Closing it stops the server. You can launch again without reinstalling the catalogue. On macOS or Windows, an unsigned download may trigger an operating-system warning; use your platform's normal application-verification process. Releases are not currently signed or notarized.

The app download and catalogue are separate. Setup shows the source, destination, and transfer progress. Ensure you have room for the compressed archive, extracted catalogue, and prepared indexes; import also requires temporary extraction space. First-time indexing takes longer than later launches. No catalogue crawling occurs during installation.

## Choose title languages

In setup or **Catalogue settings**, select English, Traditional Chinese, or Simplified Chinese and choose **Save and collect in background**. Original titles and all translations already in the catalogue remain available.

When selected translations are missing, DLFilter contacts DLsite in the background using its bundled helper. Collection can take hours. You can keep searching with existing titles; newly collected titles become searchable without restarting. A status indicator reports progress, and Catalogue settings lets you pause or resume. Completed work is saved between launches.

This collects officially offered titles for existing works only. It does not translate text itself, add separately numbered translated editions, or update the underlying catalogue. Some works have no translated title.

## Search

- **Search by:** enter words from a title, creator/circle, or product ID. Character width and letter case are ignored. Keywords and active filters apply together.
- **Genres:** select genres to rank matching works by similarity. Use the circular copy button to add genres from an RJ/BJ/VJ ID, or choose **Copy tags** on a result. Copying preserves other filters and does not run a search.
- **Included/excluded genres:** require or reject specific genres. These are hard filters, separate from similarity ranking.
- **Product formats and advanced options:** narrow formats, age ratings, release dates, ratings, and content. With no format selected, all formats are eligible.
- Leave keywords and scoring genres empty to browse newest matching works. **Random** uses current keywords and hard filters. **Reset** restores defaults.

Settings are remembered in the same browser. The download/upload buttons save and load named presets; automatic preferences remain separate. Where available, cards offer an original/translated-title switch.

Supported prefixes do not guarantee local coverage. Search results reflect the installed catalogue and its last update; current DLsite prices, popularity, and availability may differ.

## Advanced use

- [Installation, source builds, configuration, and Docker](docs/installation.md)
- [Build, update, back up, and extend the catalogue](docs/database.md)
- [Local HTTP API](docs/api.md)
- [Development architecture, tests, and measurements](docs/DEVELOPMENT.md)

Catalogue maintenance remains optional and separate from ordinary searching. Stop the server before replacing its main catalogue. Source builds require Rust; collection/model tools additionally require Python and their maintenance dependencies.

## Credits and license

Revived by [charasleeping](https://github.com/charasleeping/DLfilter), based on [snowmeow2's DLfilter](https://github.com/snowmeow2/DLfilter). The original author developed the semantic genre-search idea and implementation. Contributions and forks are welcome; maintenance may be intermittent. [MIT license](LICENSE).
