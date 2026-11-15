# Installation and operation

## Native releases

Extract the full platform ZIP to a writable folder, open its launcher, and complete setup at `http://localhost:8000/`. Windows uses `start.bat`; macOS uses `start.command`; Linux uses `./start.command`. Keep the window open. Stop with Ctrl-C or close it when finished. Nothing is installed globally.

The release must include `bin/dlfilter` (or `.exe`), the matching `bin/dlfilter-titles` helper, templates, and static files. Choose the matching processor architecture. The private helper contains Python but no model or scientific libraries. The project currently does not sign/notarize releases. OS launch policies can vary; consult your platform's official verification guidance rather than disabling security protections globally.

Setup offers a verified download or local ZIP import. The standard download is described by `serving-catalogue.json` on the project's `database` release. Its `version`, `url`, `sha256`, and compressed `size` describe `works-serving.zip`. These new artifacts must be published by a maintainer before automatic downloads work; this code change does not publish them. The older `works-db.zip` is a maintenance archive and may need conversion.

A serving bundle contains `works.sqlite`, `genre_table.json`, `workformat.json`, `genre_vectors.json`, and `genre_vectors.f32`. Import ignores unrelated files, rejects unsafe paths/symlinks/duplicate catalogue files, and validates the catalogue before activation. Installation never crawls DLsite. Downloads and expanded accepted files are limited to 16 GiB. Leave additional room for the archive, extraction, indexes, and any preserved previous installation.

The browser shows progress, cancellation, and errors. Index preparation is a finishing step and is not cancellable; closing the app is safe and preparation is repeated on next launch. If installation replaces an incomplete/incompatible folder, its old contents are retained in `<folder>.before-setup`. A write-ahead journal recovers interrupted folder promotion. An active catalogue cannot be replaced through browser setup.

## Background title collection

Open Catalogue settings, select English, Traditional Chinese and/or Simplified Chinese, then explicitly start collection. Japanese/original and all existing translated titles remain available. Only multilingual existing works advertising the selected language are queried, newest first. There is one sequential worker with at most two requests/second, bounded retries, and longer delays for 403/429 responses. Successful negative results are checkpointed; failed requests are not. Errors stop the job and can be retried from settings.

The private helper contacts DLsite; no embedding model is downloaded. Completed lookups are stored in `titles.sqlite` beside the native search cache. A supplemental search index makes committed titles available without restarting or rebuilding the main catalogue. Preferences in `catalogue-settings.json` record selected languages and whether to resume on launch. Pause keeps completed work. Browser search preferences and named presets remain separate.

Preserve the search cache directory if you want to retain collected titles and automatic collection preferences. Ordinary search indexes within that directory can be regenerated, but deleting the entire directory also deletes these supplementary titles. This location can be set explicitly with `DLFILTER_CACHE_DIR`.

This does not add separately numbered translated editions or refresh product statistics. Full catalogue maintenance remains in [the database guide](database.md). Supplemental titles are local to this catalogue path; moving or replacing the catalogue may require recollection. Stop collection before maintenance.

## Source checkout

```sh
git clone https://github.com/charasleeping/DLfilter
cd DLfilter
cargo build --release --locked
./target/release/dlfilter serve --open
```

On Windows use `target\release\dlfilter.exe serve --open`. Setup and search work without Python. For background title collection in a source checkout either build the private helper or set `DLFILTER_TITLE_PYTHON` to a Python 3.11+ executable; the source helper uses the standard library and system certificates; packaged helpers also include a CA certificate bundle.

To build the helper, use a separate build environment with Python 3.12, `pyinstaller==6.16.0`, and `certifi==2026.7.22`, then run:

```sh
python -m PyInstaller --onefile --name dlfilter-titles --paths . scripts/title_helper.py
python scripts/smoke_helper.py
```

Copy the resulting helper from `dist/` into `bin/`. This build-time Python installation is unnecessary for packaged app users.

### Existing legacy data

Keep your original SQLite and pickle files. Convert only a trusted local pickle:

```sh
uv run --extra convert --no-dev python -m module.export_vectors --trusted-pickle database/genre_vec.pkl --output database
```

Restart the app; it recognizes the existing catalogue. Do not upload a legacy-only archive to setup: it never unpickles imported files. The Python installer remains available for maintenance archives: `python -m module.fetch_database --file works-db.zip`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DLFILTER_ROOT` | App directory | Frontend and private helper location |
| `DLFILTER_DATA_DIR` | App's `database/` | Main catalogue |
| `DLFILTER_PRESETS_DIR` | App's `presets/` | Named preset files |
| `DLFILTER_CACHE_DIR` | OS app cache, keyed by catalogue path | Search indexes, supplemental titles and catalogue settings |
| `DLFILTER_HOST` | `127.0.0.1` | Listening address |
| `DLFILTER_PORT` | `8000` | Listening port |
| `DLFILTER_DB_MANIFEST_URL` | Project database release manifest | Alternate trusted serving-bundle manifest |
| `DLFILTER_TITLE_PYTHON` | Unset | Source-only private helper interpreter fallback |
| `DLFILTER_MODEL` | Default Japanese embedding model | Python maintenance only |

The native commands `prepare`, `serve --open`, and `doctor` prepare indexes, serve the UI, and check main catalogue files. A native executable alone still needs the frontend assets from the release/source checkout. When selecting a different data directory, choose a matching cache directory if retaining supplemental data is important.

## Docker

Install a serving catalogue into `database/` on the host, then:

```sh
docker compose up -d
```

Compose builds the image locally, binds port 8000 to localhost, mounts the catalogue read-only, and stores presets/cache in named volumes. It does not download a catalogue automatically. The serving image includes the private title helper. Browser title collection writes to the cache volume, never to the read-only main catalogue. Full updates use the separate Python `update` profile in `compose.yaml`; stop the serving container first.

## Troubleshooting

- **No release for your processor:** use a matching source build; a binary for another processor will not run.
- **Port already in use:** stop the other instance or choose another `DLFILTER_PORT`.
- **Cannot write to the app folder:** move the extracted app to a user-writable folder, then relaunch.
- **Automatic download fails:** confirm the portable manifest/bundle has been published, check connectivity, or import a compatible local ZIP.
- **Legacy ZIP rejected:** convert trusted local vectors using the instructions above, or use a serving bundle.
- **Title helper missing:** extract the entire native release again. Source users can configure `DLFILTER_TITLE_PYTHON`.
- **Background collection fails:** search still works. Retry from Catalogue settings; completed lookups will be skipped.
- **Browser disconnects:** keep the launcher open. Setup can be reopened at `/setup`.

## Release preparation (maintainers)

Create portable vectors from trusted local data, then build the serving artifact without modifying the source catalogue:

```sh
python scripts/package_catalogue.py --data database --output dist/catalogue
```

Validate the output ZIP through browser import and verify its SHA-256. Publish `works-serving.zip`, `works-serving.zip.sha256`, and `serving-catalogue.json` together on the database release only after review. Full maintenance bundles remain separate. Do not advertise automatic setup before those artifacts exist.

The native release workflow freezes and smoke-tests the helper, builds Rust, packages the app per platform, and attaches `.zip.sha256` files. Release publication is a separate maintainer action. Build/CI test instructions are in [DEVELOPMENT.md](DEVELOPMENT.md).
