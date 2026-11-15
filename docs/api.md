# Local HTTP API

The native server serves JSON at `http://localhost:8000`. It does not provide Swagger/OpenAPI at `/docs`. It is intended for local use and has no account authentication. Keep the default localhost binding unless access is controlled separately.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/info` | Catalogue work count and last-modified time |
| `GET /api/locale/{locale}` | Translated genre/format labels |
| `GET /api/works?rj_id=RJ123456` | Up to 50 repeated RJ/BJ/VJ IDs; `missing` lists absent records |
| `GET /api/search` | Combined keywords, hard filters, optional similarity ranking and pagination |
| `GET /api/random` | Uniform random results using keywords and hard filters |
| `POST /api/similarity` | Legacy compatibility adapter; up to 240 ID/score pairs |
| `GET /api/presets` | Named preset list |
| `GET /api/presets/{name}` | Read a preset |
| `PUT /api/presets/{name}` | Validate and save a preset |

Search accepts `q`, `field` (`all`, `title`, `artist`, `id`), `ages` (three binary digits; `000` means all), `page`, `page_size` (1–48), `genres`, `rj_id` (reference), `categories`, `included_genres`, `excluded_genres`, `since` (YYYY-MM-DD), `excluded_low_rate`, `excluded_options`, `weight_func` (1–4), and `dlcount` (0–100). List filters use `+` separators; encode the plus as `%2B` in URLs. Random additionally accepts `count` (1–48).

Empty queries browse by release date. Scoring genres enable similarity ranking; keywords still filter candidates first. Without scoring genres, keyword searches retain relevance ordering. Successful search responses contain `state`, `source`, `query`, `field`, `page`, `page_size`, `total`, and `results`. Cards may include `score`, translated-title metadata, and `titleToggle`. Background collected titles participate in search and card hydration.

## Setup controls

`GET /api/setup/status` reports `ready`, `installation`, `titles`, `preferences`, `destination`, `source`, and a per-process `token`. Jobs include `state`, `phase`, `done`, `total`, `added`, and `message`. Transfer counts are bytes; title counts are language/work lookups. States are idle (empty initially), running, complete, error, cancelled, or paused.

Mutation requests require `X-DLFilter-Token` from status and a same-origin browser context. Cross-site requests and foreign Host headers on the local listener are rejected. The token is a local browser-control safeguard, not account authentication.

| Endpoint | Input |
| --- | --- |
| `POST /api/setup/download` | No body; starts configured manifest download |
| `POST /api/setup/import` | Multipart catalogue ZIP; streamed to temporary storage |
| `POST /api/setup/cancel` | No body; cancels download/extraction before activation |
| `POST /api/setup/titles` | JSON: `languages` array of ENG/CHI_HANT/CHI_HANS and `enabled` boolean |
| `POST /api/setup/titles/pause` | No body; pauses collection and disables automatic resume |

Preferences may be saved before a catalogue is ready. Enabling collection explicitly authorizes DLsite access; collection starts after installation and resumes on future launches until paused. Installation is refused while a catalogue is active or another installation is running. Search APIs return 503 before setup completes; the root opens setup instead.
