"""Local catalogue search over the `maniax` table by title, circle or RJ ID."""

import re
import sqlite3
import unicodedata
from collections.abc import Sequence
from typing import Any

from module.database import TITLE_COLUMNS
from module.products import PRODUCT_ID, normalize_id

FIELDS = ("all", "title", "artist", "id")
MAX_QUERY_LENGTH = 100
MAX_PAGE = 2_147_483_647
DEFAULT_PAGE_SIZE = 48
MAX_PAGE_SIZE = 48
RJ_ID = PRODUCT_ID

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
OPTIONAL_COLUMNS = EDITION_COLUMNS + ("imageUrl",) + tuple(TITLE_COLUMNS.values())
COLUMN_KEYS = RESULT_COLUMNS + OPTIONAL_COLUMNS


def _columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(maniax)")}


def _select_columns(conn: sqlite3.Connection, prefix: str = "") -> list[str]:
    """SQL select expressions for all result columns, with NULL for optional columns the database lacks."""
    present = _columns(conn)
    columns = [f"{prefix}[{column}]" for column in RESULT_COLUMNS]
    optional = OPTIONAL_COLUMNS
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


def conditions(conn, query="", field="all", ages="100", *, categories=(), included_genres=(),
               excluded_genres=(), since=None, excluded_low_rate=False, excluded_options=()):
    """One parameterized predicate for keyword, browse, similarity and random discovery."""
    conn.create_function("fold", 1, fold, deterministic=True)
    folded = " ".join(fold(query).split())
    names = ["name"] + [c for c in TITLE_COLUMNS.values() if c in _columns(conn)]
    text_columns = {"all": names + ["maker"], "title": names, "artist": ["maker"], "id": []}[field]
    where, params = [], []
    for term in folded.split():
        pattern = _escape_like(term)
        clauses = [f"fold({c}) LIKE ? ESCAPE '\\'" for c in text_columns]
        params += [f"%{pattern}%"] * len(clauses)
        if field in ("all", "id"):
            clauses.append("[index] LIKE ? ESCAPE '\\'")
            params.append(f"{pattern}%")
        where.append("(" + " OR ".join(clauses) + ")")
    values = _age_values(ages)
    where.append(f"ageCategory IN ({','.join('?' for _ in values)})")
    params += values
    if categories:
        where.append(f"type IN ({','.join('?' for _ in categories)})")
        params += list(categories)
    for ids, operator in ((included_genres, "LIKE"), (excluded_genres, "NOT LIKE")):
        for genre in ids:
            where.append(f"COALESCE(tags, '') {operator} ?")
            params.append(f"%#{genre}#%")
    if since:
        where.append("registDate >= ?")
        params.append(since)
    if excluded_low_rate:
        where.append("rate >= 40")
    for option in excluded_options:
        where.append("COALESCE(options, '') NOT LIKE ?")
        params.append(f"%#{option}#%")
    return " AND ".join(where), params, names, folded


def random_works(conn, ages, count, *, query="", field="all", **filters):
    where, params, _, folded = conditions(conn, query, field, ages, **filters)
    rows = conn.execute(f"SELECT {', '.join(_select_columns(conn))} FROM maniax WHERE {where} "
                        "ORDER BY RANDOM() LIMIT ?", params + [count]).fetchall()
    return [_finish(dict(zip(COLUMN_KEYS, row)), folded.split()) for row in rows]


def search(conn, query, field, ages, page, page_size, *, genres=(), rj_id=None,
           catalogue=None, weight_func="linear", dlcount=50, **filters):
    where, params, names, folded = conditions(conn, query, field, ages, **filters)
    if genres:
        import numpy as np
        import torch
        from .utils import cos_sim, dlCount_weight
        weights = catalogue.get_weighting(weight_func)
        selected = list(dict.fromkeys(genres))
        if any(g not in weights for g in selected):
            raise ValueError("Unknown scoring genre")
        if rj_id:
            where += " AND [index] != ?"
            params.append(normalize_id(rj_id))
        candidates = conn.execute(f"SELECT [index], tags, dlCount FROM maniax WHERE {where} ORDER BY [index]", params)
        ids, vectors, downloads = [], [], []
        for workno, tags, count in candidates:
            tags = [g for g in (tags or "").split("#") if g]
            if not tags or any(g not in weights for g in tags):
                continue
            vector = np.mean([weights[g] for g in tags], axis=0)
            if not np.isfinite(vector).all() or not np.linalg.norm(vector):
                continue
            ids.append(workno); vectors.append(vector); downloads.append(count or 0)
        if not ids:
            return 0, []
        query_vector = np.mean([weights[g] for g in selected], axis=0)
        scores = cos_sim(torch.tensor(query_vector, dtype=torch.float32),
                         torch.tensor(np.array(vectors), dtype=torch.float32)).numpy()
        if dlcount != 50:
            scores = scores.astype(float) * dlCount_weight(dlcount, np.array(downloads), 2.09, 1)
        order = sorted(range(len(ids)), key=lambda i: (-float(scores[i]), ids[i]))
        chosen = order[(page - 1) * page_size:page * page_size]
        if not chosen:
            return len(ids), []
        page_ids = [ids[i] for i in chosen]
        rows = conn.execute(f"SELECT {', '.join(_select_columns(conn))} FROM maniax WHERE [index] IN "
                            f"({','.join('?' for _ in page_ids)})", page_ids).fetchall()
        works = {row[0]: _finish(dict(zip(COLUMN_KEYS, row)), folded.split()) for row in rows}
        return len(ids), [dict(works[ids[i]], score=float(scores[i])) for i in chosen]
    total = conn.execute(f"SELECT COUNT(*) FROM maniax WHERE {where}", params).fetchone()[0]
    if folded:
        rank_columns = ["maker"] if field == "artist" else names
        exact = " OR ".join(f"fold({c}) = ?" for c in rank_columns)
        prefix = " OR ".join(f"fold({c}) LIKE ? ESCAPE '\\'" for c in rank_columns)
        order = f"CASE WHEN [index] = ? THEN 0 WHEN {exact} THEN 1 WHEN {prefix} THEN 2 ELSE 3 END, name, [index]"
        rank_params = [normalize_id(folded) if PRODUCT_ID.fullmatch(normalize_id(folded)) else None]
        rank_params += [folded] * len(rank_columns) + [f"{_escape_like(folded)}%"] * len(rank_columns)
    else:
        order, rank_params = "registDate DESC, [index]", []
    rows = conn.execute(f"SELECT {', '.join(_select_columns(conn))} FROM maniax WHERE {where} ORDER BY {order} "
                        "LIMIT ? OFFSET ?", params + rank_params + [page_size, (page - 1) * page_size]).fetchall()
    return total, [_finish(dict(zip(COLUMN_KEYS, row)), folded.split()) for row in rows]
