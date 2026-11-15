from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Annotated, Any, List
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from module import config
from . import search, presets
from module.database import connect_readonly
from module.products import PRODUCT_PATTERN, normalize_id
from pydantic import BeforeValidator, StringConstraints
ProductId = Annotated[str, StringConstraints(pattern=PRODUCT_PATTERN), BeforeValidator(normalize_id)]
from module.dlsite import GenreCatalog
import logging
import time
import os

logger = logging.getLogger("dlfilter")

app = FastAPI()
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


def asset_url(path: str) -> str:
    """URL of a static file with its modification time, so an edited file is never served from the browser cache."""
    return f"{app.url_path_for('static', path=path)}?v={int((config.STATIC_DIR / path).stat().st_mtime)}"


templates.env.globals["asset_url"] = asset_url
database_path = config.DATABASE_PATH
GG = GenreCatalog(target="", path=config.DATA_DIR)

weigth_func_dict = {
    1: "r_logistic",
    2: "logistic",
    3: "gaussian",
    4: "linear",
}


class SimilarityQuery(BaseModel):
    """
    The query model for the similarity search API.

    Attributes
    ----------
    genres : str
        The target genres. The genres should be separated by `+`. All selected known genres are used.
    rj_id : Optional[str]
        The RJ, BJ or VJ ID of the reference work. The format is `RJxxxxxxxx` or `RJxxxxxx`.
    date : datetime
        The release date of the work. The format is `YYYY-MM-DD`.
    dlcount : int
        The weight of the popularity based on the download count. The weight should be in the range of `[0, 100]`.
    weight_func : int
        The weight function. The weight function should be in the range of `[1, 4]`.
    ages : str
        The indicator of the age restriction, where the first char represents the all age, the second char represents the R15, and the third char represents the R18, i.e, "111" means all age, R15, and R18 are all included, and "100" means only all age is included.
    excluded_low_rate : bool
        Whether to exclude the works with low rate. Default is `True`.
    excluded_options : Optional[str]
        The excluded options. The options should be separated by `+`, and the options can be `AIG`, `AIP`, `GRO`, and `MEN`.
    excluding_interest : bool
        Whether to exclude the works with low interest. Default is `False`.
    categories : Optional[str]
        The target categories. The categories should be separated by `+`.
    included_genres : Optional[str]
        The included genres. The genres should be separated by `+`. Maximum is 5.
    excluded_genres : Optional[str]
        The excluded genres. The genres should be separated by `+`. Maximum is 5.
    """

    genres: str = Query(
        ...,
        pattern=r"^[0-9]{3}(?:\+[0-9]{3}){0,999}$",
        description="The target genres. The genres should be separated by `+`. All selected known genres are used.",
    )
    rj_id: ProductId | None = Query(
        None,
        pattern=PRODUCT_PATTERN,
        description="The RJ, BJ or VJ ID of the reference work.",
    )
    date: datetime = datetime(2000, 1, 1)
    dlcount: int = Query(
        50,
        ge=0,
        le=100,
        description="The weight of the popularity based on the download count. The weight should be in the range of `[0, 100]`.",
    )
    weight_func: int = Query(
        1, ge=1, le=4, description="The weight function. The weight function should be in the range of `[1, 4]`."
    )
    ages: str = Query(
        "100",
        pattern=r"^[01]{3}$",
        description="The indicator of the age restriction, where the first char represents the all age, the second char represents the R15, and the third char represents the R18, i.e, `111` means all age, R15, and R18 are all included.",
    )
    excluded_low_rate: bool = True
    excluded_options: str | None = Query(
        "AIG+AIP+GRO+MEN",
        pattern=r"^(?:AIG|AIP|GRO|MEN)(?:\+(?:AIG|AIP|GRO|MEN))*$",
        description="The excluded options. The options should be separated by `+`, and the options can be `AIG`, `AIP`, `GRO`, and `MEN`.",
    )
    # excluding_interest: bool = False # TODO: Add this option
    categories: str | None = Query(
        None,
        pattern=r"^[A-Z0-9]{3}(\+[A-Z0-9]{3})*$",
        description="The target categories. The categories should be separated by `+`.",
    )
    included_genres: str | None = Query(
        None,
        pattern=r"^[0-9]{3}(?:\+[0-9]{3}){0,4}$",
        description="The included genres. The genres should be separated by `+`. Maximum is 5.",
    )
    excluded_genres: str | None = Query(
        None,
        pattern=r"^[0-9]{3}(?:\+[0-9]{3}){0,4}$",
        description="The excluded genres. The genres should be separated by `+`. Maximum is 5.",
    )


RJ_ID_REGEX = ProductId


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    The root page of the website.

    Parameters
    ----------
    request : Request
        The request object.

    Returns
    -------
    HTMLResponse
        The HTML response.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )

@app.get("/api/info")
async def get_info() -> dict[str, Any]:
    """
    Get the information of the database.

    Returns
    -------
    dict
        The length of the database and the last modified time.
    """
    try:
        # Get the last modified time of the database file
        lmt = os.path.getmtime(database_path)

        # Convert the timestamp to a human-readable format
        lmt = datetime.fromtimestamp(lmt, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Connect to the database
        with connect_readonly(database_path) as conn:
            # Create a cursor object to execute SQL queries
            cur = conn.cursor()

            # Execute a query to count the number of rows in the 'maniax' table
            cur.execute("SELECT COUNT([index]) FROM maniax")

            # Fetch the result of the query
            length = cur.fetchone()[0]

        # Return a dictionary containing the length of the database and the last modified time
        return {"state": "success", "length": length, "time": lmt}

    except Exception:
        logger.exception("Failed to read database info from %s", database_path)
        return {"state": "error", "message": "The database is unavailable."}


@app.get("/api/locale/{locale}")
async def get_genres(locale: str) -> dict[str, Any]:
    """
    Get the genre localization for the specified locale.

    Parameters
    ----------
    locale : str
        The locale. Available locales are: `ja_JP`, `en_US`, `zh_TW`, `zh_CN`, `ko_KR`.
        See GenreCatalog.locales for more information.

    Returns
    -------
    dict
        The genre localization.
    """
    # Check if the locale is available, otherwise use en_US.
    if locale in GG.locales:
        pass
    else:
        locale = "en_US"

    locale_dict = {
        "genres": {},
        "work_formats": {},
    }
    def label(values, fallback):
        return values.get(locale) or values.get("en_US") or values.get("ja_JP") or fallback

    for genre_id, genre in GG.genre_catalogue.items():
        locale_dict["genres"][genre_id] = {
            "category": label(genre.get("category", {}), "Other"),
            "name": label(genre.get("name", {}), genre_id),
            "count": genre.get("count", 0),
        }
    for work_format_id, work_format in GG.workformat.items():
        category = work_format.get("category", {})
        locale_dict["work_formats"][work_format_id] = {
            "category_id": category.get("en_US", "Miscellaneous"),
            "category": label(category, "Other"),
            "name": label(work_format.get("name", {}), work_format_id),
        }
    return {"state": "success", "locale": locale_dict}


@app.get("/api/works")
async def get_works(rj_id: List[RJ_ID_REGEX] = Query(..., description="The RJ IDs of the works.")) -> dict[str, Any]:
    """
    Get the information of the specified works.

    Parameters
    ----------
    rj_id : List[str]
        The RJ IDs of the works. The format is `RJxxxxxxxx` or `RJxxxxxx`, separated by the `&` character.

    Returns
    -------
    dict
        `works` maps every requested ID to its information (`{}` when it is not in the local database),
        and `missing` lists the requested IDs that were not found.
    """
    if len(rj_id) > 50:
        return {"state": "error", "message": "The maximum number of requesting works is 50."}

    try:
        # Connect to the database
        with connect_readonly(database_path) as conn:
            # Create a cursor object to execute SQL queries
            cur = conn.cursor()

            # Execute a query to get the information of the work
            cur.execute("SELECT * FROM maniax WHERE [INDEX] IN ({})".format(",".join(["?"] * len(rj_id))), rj_id)
            result = cur.fetchall()

            result_dict = {index: {} for index in rj_id}

            # Check if the works exists
            for work in result:
                work = search.format_work(dict(zip([description[0] for description in cur.description], work)))
                result_dict[work["index"]] = work

        missing = [index for index, work in result_dict.items() if not work]

        # Return a dictionary containing the information of the work
        return {"state": "success", "works": result_dict, "missing": missing}

    except Exception:
        logger.exception("Failed to look up works %s", rj_id)
        return {"state": "error", "message": "Failed to read the database."}


def search_error(code: str, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"state": "error", "code": code, "message": message})


class SearchFilters(BaseModel):
    q: str = ""
    field: str = "all"
    ages: str = "100"
    page: int = 1
    page_size: int = 48
    count: int = 48
    genres: str | None = None
    rj_id: ProductId | None = None
    categories: str | None = None
    included_genres: str | None = None
    excluded_genres: str | None = None
    since: str | None = None
    excluded_low_rate: bool = False
    excluded_options: str | None = None
    weight_func: int = 4
    dlcount: int = 50


def validate_filters(f):
    import re
    if len(f.q.strip()) > search.MAX_QUERY_LENGTH:
        return search_error("query_too_long", "The search text must be at most 100 characters.")
    if f.field not in search.FIELDS:
        return search_error("invalid_field", "Choose all, title, artist or id.")
    if not re.fullmatch(r"[01]{3}", f.ages):
        return search_error("invalid_ages", "ages must be three 0/1 flags.")
    if not 1 <= f.page <= search.MAX_PAGE:
        return search_error("invalid_page", "Invalid page.")
    if not 1 <= f.page_size <= 48:
        return search_error("invalid_page_size", "page_size must be between 1 and 48.")
    if not 1 <= f.count <= 48:
        return search_error("invalid_count", "count must be between 1 and 48.")
    for key, table, maximum in (("genres", GG.genre_catalogue, 1000),
                                ("included_genres", GG.genre_catalogue, 5),
                                ("excluded_genres", GG.genre_catalogue, 5),
                                ("categories", GG.workformat, 1000),
                                ("excluded_options", {x: 1 for x in ("AIG", "AIP", "GRO", "MEN")}, 4)):
        ids = split_ids(getattr(f, key))
        if len(ids) > maximum or any(i not in table for i in ids):
            return search_error("invalid_" + key, "Invalid " + key + ".", 422)
    if set(split_ids(f.included_genres)) & set(split_ids(f.excluded_genres)):
        return search_error("conflicting_genres", "A genre cannot be both required and excluded.")
    if f.since:
        try:
            datetime.strptime(f.since, "%Y-%m-%d")
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", f.since):
                raise ValueError()
        except ValueError:
            return search_error("invalid_since", "Use a valid YYYY-MM-DD date.", 422)
    if f.weight_func not in weigth_func_dict or not 0 <= f.dlcount <= 100:
        return search_error("invalid_weight", "Invalid popularity weighting.", 422)


def split_ids(value):
    return list(dict.fromkeys(value.split("+"))) if value else []


def hard_filters(f):
    return dict(categories=split_ids(f.categories), included_genres=split_ids(f.included_genres),
                excluded_genres=split_ids(f.excluded_genres), since=f.since,
                excluded_low_rate=f.excluded_low_rate, excluded_options=split_ids(f.excluded_options))


@app.get("/api/search")
def search_works(filters: Annotated[SearchFilters, Query()]):
    """Filter keywords and catalogue metadata together, optionally ranking by genre similarity."""
    if error := validate_filters(filters):
        return error
    try:
        with connect_readonly(database_path) as conn:
            total, results = search.search(conn, filters.q.strip(), filters.field, filters.ages,
                                          filters.page, filters.page_size, genres=split_ids(filters.genres),
                                          rj_id=filters.rj_id, catalogue=GG,
                                          weight_func=weigth_func_dict[filters.weight_func], dlcount=filters.dlcount,
                                          **hard_filters(filters))
    except Exception:
        logger.exception("Unified search failed")
        return search_error("database_error", "Failed to read the database.", 500)
    return dict(state="success", source="local", query=filters.q.strip(), field=filters.field,
                page=filters.page, page_size=filters.page_size, total=total, results=results)


@app.get("/api/random")
def get_random_works(filters: Annotated[SearchFilters, Query()]):
    if error := validate_filters(filters):
        return error
    try:
        with connect_readonly(database_path) as conn:
            results = search.random_works(conn, filters.ages, filters.count, query=filters.q.strip(),
                                          field=filters.field, **hard_filters(filters))
    except Exception:
        logger.exception("Random search failed")
        return search_error("database_error", "Failed to read the database.", 500)
    return dict(state="success", source="local", results=results)


def invalid_preset_name() -> JSONResponse:
    return search_error("invalid_name", "Use up to 60 letters, digits, spaces, - or _.")


@app.get("/api/presets")
def get_presets():
    """List the presets saved in the presets folder, newest first."""
    return {"state": "success", "folder": config.PRESETS_DIR.name, "presets": presets.list_presets(config.PRESETS_DIR)}


@app.get("/api/presets/{name}")
def get_preset(name: str):
    """Read one preset."""
    if not presets.valid_name(name):
        return invalid_preset_name()
    try:
        preset = presets.load_preset(config.PRESETS_DIR, name)
    except FileNotFoundError:
        return search_error("not_found", "No preset has this name.", status_code=404)
    except (ValueError, OSError):
        logger.exception("Failed to read preset %r", name)
        return search_error("invalid_preset", "The preset file could not be read.", status_code=422)
    return {"state": "success", "name": name, "preset": preset.model_dump()}


@app.put("/api/presets/{name}")
def put_preset(name: str, preset: presets.Preset):
    """Save a preset, replacing any preset with the same name."""
    if not presets.valid_name(name):
        return invalid_preset_name()
    try:
        presets.save_preset(config.PRESETS_DIR, name, preset)
    except presets.TooManyPresets:
        return search_error(
            "too_many_presets", f"At most {presets.MAX_PRESETS} presets can be saved.", status_code=409
        )
    except OSError:
        logger.exception("Failed to save preset %r", name)
        return search_error("save_failed", "The preset could not be saved.", status_code=500)
    return {"state": "success", "name": name}


@app.post("/api/similarity")
def get_similar_works(query: SimilarityQuery):
    """Compatibility endpoint: the unified scorer with the original 240-result response."""
    started = time.time()
    filters = SearchFilters(**query.model_dump(exclude={"date"}), since=query.date.strftime("%Y-%m-%d"))
    if error := validate_filters(filters):
        return error
    try:
        with connect_readonly(database_path) as conn:
            total, results = search.search(conn, "", "all", filters.ages, 1, 240,
                                          genres=split_ids(filters.genres), rj_id=filters.rj_id,
                                          catalogue=GG, weight_func=weigth_func_dict[filters.weight_func],
                                          dlcount=filters.dlcount, **hard_filters(filters))
    except Exception:
        logger.exception("Similarity search failed")
        return search_error("database_error", "Failed to read the database.", 500)
    if not results:
        return {"state": "error", "message": "No similar works found."}
    return {"state": "success", "result": [(w["index"], w["score"]) for w in results],
            "info": {"length": total, "time": time.time() - started}}


def open_browser_when_ready(host: str, port: int) -> None:
    """Open the site in the default browser once the server accepts connections."""
    import socket
    import webbrowser

    for _ in range(240):
        try:
            socket.create_connection((host, port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.5)
    else:
        return
    webbrowser.open(f"http://{f'[{host}]' if ':' in host else host}:{port}/")


if __name__ == "__main__":
    import sys
    import threading

    import uvicorn

    if "--open" in sys.argv[1:]:
        threading.Thread(target=open_browser_when_ready, args=(config.HOST, config.PORT), daemon=True).start()
    uvicorn.run(app, host=config.HOST, port=config.PORT)
