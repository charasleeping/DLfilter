"""Local catalogue search over the `maniax` table by title, circle or RJ ID."""

import re
import sqlite3
import unicodedata
from collections.abc import Sequence
from typing import Any

from module.database import TITLE_COLUMNS

FIELDS = ("all", "title", "artist", "id")
MAX_QUERY_LENGTH = 100
MAX_PAGE = 10_000
DEFAULT_PAGE_SIZE = 48
MAX_PAGE_SIZE = 48
RJ_ID = re.compile(r"^RJ(?:\d{8}|\d{6})$")

RESULT_COLUMNS = (
    "index",
    "name",
    "maker",
    "siteId",
    "type",
    "ageCategory",
    "registDate",
    "tags",
    "options",
    "rate",
    "rateCount",
    "dlCount",
    "reviewCount",
    "description",
)

# Absent from databases built before translated editions were supported.
EDITION_COLUMNS = ("lang", "originalWorkno", "originalLang", "originalName")
TOGGLE_LANGS = {"ENG", "JPN", "CHI_HANT", "CHI_HANS"}
COLUMN_KEYS = RESULT_COLUMNS + EDITION_COLUMNS + tuple(TITLE_COLUMNS.values())


def _columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(maniax)")}


def _select_columns(conn: sqlite3.Connection, prefix: str = "") -> list[str]:
    """SQL select expressions for all result columns, with NULL for optional columns the database lacks."""
    present = _columns(conn)
    columns = [f"{prefix}[{column}]" for column in RESULT_COLUMNS]
    optional = EDITION_COLUMNS + tuple(TITLE_COLUMNS.values())
    return columns + [f"{prefix}[{c}]" if c in present else f"NULL AS [{c}]" for c in optional]


def _finish(work: dict[str, Any], terms: Sequence[str] = ()) -> dict[str, Any]:
    """
    Format a result row. If the query matched one of the work's official translated titles rather than its
    original one, show that title as the work's name and keep the original for the card's title switch.
    """
    titles = {lang: work.pop(column) for lang, column in TITLE_COLUMNS.items()}
    format_work(work)
    if terms and not work.get("lang") and not all(term in fold(work["name"]) for term in terms):
        for lang, title in titles.items():
            if title and all(term in fold(title) for term in terms):
                work.update(originalName=work["name"], originalLang="JPN", lang=lang, name=title)
                break
    work["titleToggle"] = _title_toggle(work, terms) if terms else False
    return work


def _title_toggle(work: dict[str, Any], terms: Sequence[str]) -> bool:
    """True if the card can switch between the matched edition title and the original title."""
    original = work.get("originalName")
    if not original or work.get("lang") == work.get("originalLang"):
        return False
    if work.get("lang") not in TOGGLE_LANGS or work.get("originalLang") not in TOGGLE_LANGS:
        return False
    folded = fold(original)
    return not all(term in folded for term in terms)


def fold(text: Any) -> Any:
    """NFKC-normalise and casefold, so full-/half-width forms and letter case compare equal."""
    return unicodedata.normalize("NFKC", text).casefold() if isinstance(text, str) else text


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def format_work(work: dict[str, Any]) -> dict[str, Any]:
    """Split `#`-joined tags/options into lists and trim registDate to YYYY-MM-DD."""
    work["tags"] = [i for i in (work.get("tags") or "").split("#") if i]
    work["options"] = [i for i in (work.get("options") or "").split("#") if i]
    if work.get("registDate"):
        work["registDate"] = str(work["registDate"]).split(" ")[0]
    return work


def _age_values(ages: str) -> list[int]:
    return [i + 1 for i in range(3) if ages[i] == "1"] or [1, 2, 3]


def random_works(
    conn: sqlite3.Connection,
    ages: str,
    count: int,
    *,
    categories: Sequence[str] = (),
    included_genres: Sequence[str] = (),
    excluded_genres: Sequence[str] = (),
    since: str | None = None,
    excluded_low_rate: bool = False,
    excluded_options: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Pick `count` random works. The filters match those of the similarity search; `ages` `000` means all."""
    age_values = _age_values(ages)
    where = [f"ageCategory IN ({', '.join('?' * len(age_values))})"]
    params: list[Any] = list(age_values)
    if categories:
        where.append(f"type IN ({', '.join('?' * len(categories))})")
        params += categories
    for genre in included_genres:
        where.append("tags LIKE ?")
        params.append(f"%#{genre}#%")
    for genre in excluded_genres:
        where.append("tags NOT LIKE ?")
        params.append(f"%#{genre}#%")
    if since:
        where.append("registDate >= ?")
        params.append(since)
    if excluded_low_rate:
        where.append("rate >= 40")
    for option in excluded_options:
        where.append("options NOT LIKE ?")
        params.append(f"%#{option}#%")

    columns = ", ".join(_select_columns(conn))
    rows = conn.execute(
        f"SELECT {columns} FROM maniax WHERE {' AND '.join(where)} ORDER BY RANDOM() LIMIT ?",
        params + [count],
    ).fetchall()
    return [_finish(dict(zip(COLUMN_KEYS, row))) for row in rows]


def search(
    conn: sqlite3.Connection, query: str, field: str, ages: str, page: int, page_size: int
) -> tuple[int, list[dict[str, Any]]]:
    """
    Search works whose title/circle contains every whitespace-separated term, or whose RJ ID starts with it.

    Ranking: exact RJ ID, exact title (circle for `artist`), title prefix, then everything else;
    ties are broken by title and RJ ID.

    Parameters
    ----------
    ages : str
        Three `0`/`1` flags for all-ages, R15 and R18, as in `/api/similarity`. `000` means all.

    Returns
    -------
    tuple[int, list[dict]]
        The total number of matches and the works on the requested page.
    """
    conn.create_function("fold", 1, fold, deterministic=True)
    folded = " ".join(fold(query).split())
    rj_id = folded.upper() if RJ_ID.match(folded.upper()) else None
    present = _columns(conn)
    name_columns = ["name"] + [c for c in TITLE_COLUMNS.values() if c in present]
    text_columns = {
        "all": name_columns + ["maker"],
        "title": name_columns,
        "artist": ["maker"],
        "id": [],
    }[field]

    where, where_params = [], []
    for term in folded.split():
        pattern = _escape_like(term)
        clauses = [f"fold({column}) LIKE ? ESCAPE '\\'" for column in text_columns]
        where_params += [f"%{pattern}%"] * len(clauses)
        if field in ("all", "id"):
            # IDs are ASCII, so SQLite's case-insensitive LIKE needs no fold().
            clauses.append("[index] LIKE ? ESCAPE '\\'")
            where_params.append(f"{pattern}%")
        where.append("(" + " OR ".join(clauses) + ")")

    age_values = _age_values(ages)
    where.append(f"ageCategory IN ({', '.join('?' * len(age_values))})")
    where_params += age_values
    where_sql = " AND ".join(where)

    rank_columns = ["maker"] if field == "artist" else name_columns
    exact_sql = " OR ".join(f"fold({c}) = ?" for c in rank_columns)
    prefix_sql = " OR ".join(f"fold({c}) LIKE ? ESCAPE '\\'" for c in rank_columns)
    rank_sql = f"CASE WHEN [index] = ? THEN 0 WHEN {exact_sql} THEN 1 WHEN {prefix_sql} THEN 2 ELSE 3 END"
    rank_params = [rj_id] + [folded] * len(rank_columns) + [f"{_escape_like(folded)}%"] * len(rank_columns)

    columns = ", ".join(_select_columns(conn, "m."))
    sql = f"""
        WITH hits AS (
            SELECT [index] AS id, name AS title, {rank_sql} AS hit_rank, COUNT(*) OVER () AS total
            FROM maniax
            WHERE {where_sql}
            ORDER BY hit_rank, title, id
            LIMIT ? OFFSET ?
        )
        SELECT {columns}, hits.total FROM hits JOIN maniax AS m ON m.[index] = hits.id
        ORDER BY hits.hit_rank, hits.title, hits.id
    """
    rows = conn.execute(sql, rank_params + where_params + [page_size, (page - 1) * page_size]).fetchall()

    if rows:
        total = rows[0][-1]
    else:
        total = conn.execute(f"SELECT COUNT(*) FROM maniax WHERE {where_sql}", where_params).fetchone()[0]

    terms = folded.split()
    return total, [_finish(dict(zip(COLUMN_KEYS, row[:-1])), terms) for row in rows]
