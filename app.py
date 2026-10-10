from datetime import datetime, timezone
from pydantic import BaseModel, constr
from typing import Any, List
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from module import config, presets, search
from module.database import connect_readonly
from module.dlsite import GenreCatalog
from module.utils import cos_sim, dlCount_weight
import torch
import numpy as np
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
        The target genres. The genres should be separated by `+`. The maximum number of genres is 10.
    rj_id : Optional[str]
        The RJ ID of the reference work. The format is `RJxxxxxxxx` or `RJxxxxxx`.
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
        pattern=r"^[0-9]{3}(?:\+[0-9]{3}){0,9}$",
        description="The target genres. The genres should be separated by `+`. The maximum is 10.",
    )
    rj_id: str | None = Query(
        None,
        pattern=r"^RJ(?:\d{8}|\d{6})$",
        description="The RJ ID of the reference work.",
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


RJ_ID_REGEX = constr(pattern=r"^RJ(?:\d{8}|\d{6})$")


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
    for genre_id, genre in GG.genre_catalogue.items():
        try:
            locale_dict["genres"][genre_id] = {
                "category": genre["category"][locale],
                "name": genre["name"][locale],
                "count": genre["count"],
            }
        except:
            pass
    for work_format_id, work_format in GG.workformat.items():
        try:
            locale_dict["work_formats"][work_format_id] = {
                "category_id": work_format["category"]["en_US"],
                "category": work_format["category"][locale],
                "name": work_format["name"][locale],
            }
        except:
            pass
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


@app.get("/api/search")
async def search_works(
    q: str = "",
    field: str = "all",
    ages: str = "100",
    page: int = 1,
    page_size: int = search.DEFAULT_PAGE_SIZE,
):
    """
    Search the local database by work title, circle name or RJ ID.

    Parameters
    ----------
    q : str
        The search text. Whitespace-separated terms must all match. Width and letter case are ignored.
    field : str
        `all`, `title`, `artist` (circle) or `id`.
    ages : str
        Three `0`/`1` flags for all-ages, R15 and R18. `000` means all ages.
    page : int
        The 1-based page number.
    page_size : int
        The number of works per page, at most 48.

    Returns
    -------
    dict
        The total number of matches and the works on the requested page.
    """
    query = q.strip()
    if not query:
        return search_error("empty_query", "Enter a title, circle name or RJ ID.")
    if len(query) > search.MAX_QUERY_LENGTH:
        return search_error("query_too_long", f"The search text must be at most {search.MAX_QUERY_LENGTH} characters.")
    if field not in search.FIELDS:
        return search_error("invalid_field", f"field must be one of: {', '.join(search.FIELDS)}.")
    if len(ages) != 3 or set(ages) - {"0", "1"}:
        return search_error("invalid_ages", "ages must be three 0/1 flags, e.g. 100.")
    if not 1 <= page <= search.MAX_PAGE:
        return search_error("invalid_page", f"page must be between 1 and {search.MAX_PAGE}.")
    if not 1 <= page_size <= search.MAX_PAGE_SIZE:
        return search_error("invalid_page_size", f"page_size must be between 1 and {search.MAX_PAGE_SIZE}.")

    try:
        with connect_readonly(database_path) as conn:
            total, results = search.search(conn, query, field, ages, page, page_size)
    except Exception:
        logger.exception("Search failed for %r (field=%s)", query, field)
        return search_error("database_error", "Failed to read the database.", status_code=500)

    return {
        "state": "success",
        "source": "local",
        "query": query,
        "field": field,
        "page": page,
        "page_size": page_size,
        "total": total,
        "results": results,
    }


@app.get("/api/random")
def get_random_works(
    ages: str = "100",
    count: int = search.DEFAULT_PAGE_SIZE,
    categories: str | None = Query(None, pattern=r"^[A-Z0-9]{3}(?:\+[A-Z0-9]{3})*$"),
    included_genres: str | None = Query(None, pattern=r"^[0-9]{3}(?:\+[0-9]{3}){0,4}$"),
    excluded_genres: str | None = Query(None, pattern=r"^[0-9]{3}(?:\+[0-9]{3}){0,4}$"),
    since: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    excluded_low_rate: bool = False,
    excluded_options: str | None = Query(None, pattern=r"^(?:AIG|AIP|GRO|MEN)(?:\+(?:AIG|AIP|GRO|MEN))*$"),
):
    """
    Pick random works from the local database.

    Parameters
    ----------
    ages : str
        Three `0`/`1` flags for all-ages, R15 and R18. `000` means all ages.
    count : int
        The number of works, at most 48.
    categories, included_genres, excluded_genres, since, excluded_low_rate, excluded_options
        Optional filters with the same meaning as in the similarity search. `since` is a `YYYY-MM-DD` date.
    """
    if len(ages) != 3 or set(ages) - {"0", "1"}:
        return search_error("invalid_ages", "ages must be three 0/1 flags, e.g. 100.")
    if not 1 <= count <= search.MAX_PAGE_SIZE:
        return search_error("invalid_count", f"count must be between 1 and {search.MAX_PAGE_SIZE}.")

    split = lambda value: value.split("+") if value else []
    try:
        with connect_readonly(database_path) as conn:
            results = search.random_works(
                conn,
                ages,
                count,
                categories=split(categories),
                included_genres=split(included_genres),
                excluded_genres=split(excluded_genres),
                since=since,
                excluded_low_rate=excluded_low_rate,
                excluded_options=split(excluded_options),
            )
    except Exception:
        logger.exception("Failed to pick random works")
        return search_error("database_error", "Failed to read the database.", status_code=500)

    return {"state": "success", "source": "local", "results": results}


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
async def get_similar_works(query: SimilarityQuery):
    start = time.time()

    ### PREPARING THE QUERY ###
    # Set up the SQL query
    sql_query = "SELECT [index], tags, dlCount FROM maniax WHERE ageCategory IN (#QUERY_AGE)"

    # First validate the query
    try:
        genres = set(i for i in query.genres.split("+"))
        included_genres = set(i for i in query.included_genres.split("+")) if query.included_genres else None
        excluded_genres = set(i for i in query.excluded_genres.split("+")) if query.excluded_genres else None

        # check if included / excluded genres are valid
        if included_genres and excluded_genres:
            if any([i in included_genres for i in excluded_genres]):
                return {"state": "error", "message": "Invalid query."}
    except Exception as e:
        return {"state": "error", "message": "Invalid query."}

    # Check if the genres are valid
    if not all([i in GG.genre_catalogue for i in genres]):
        return {"state": "error", "message": "Invalid genres."}
    if included_genres:
        if not all([i in GG.genre_catalogue for i in included_genres]):
            return {"state": "error", "message": "Invalid included genres."}
        else:
            for genre in included_genres:
                sql_query += f" AND tags LIKE '%#{genre}#%'"
    if excluded_genres:
        if not all([i in GG.genre_catalogue for i in excluded_genres]):
            return {"state": "error", "message": "Invalid excluded genres."}
        else:
            for genre in excluded_genres:
                sql_query += f" AND tags NOT LIKE '%#{genre}#%'"

    # if the rj_id is specified, exclude it from the result
    if query.rj_id:
        sql_query += f" AND [index] != '{query.rj_id}'"

    # Set up for the age category
    ages = [str(i + 1) for i in range(3) if query.ages[i] == "1"]
    sql_query = sql_query.replace("#QUERY_AGE", ", ".join(ages) or "1, 2, 3")

    # Set up for the date range
    sql_query += f" AND registDate >= '{query.date}'"

    # Set up for the categories
    if query.categories:
        try:
            categories = set(i for i in query.categories.split("+"))
            if not all([i in GG.workformat for i in categories]):
                return {"state": "error", "message": "Invalid categories."}
            else:
                temp_query = " OR ".join([f"type == '{i}'" for i in categories])
                sql_query += f" AND ({temp_query})"
        except Exception as e:
            return {"state": "error", "message": "Invalid query."}

    # TODO!
    # if query.excluding_interest:
    #     pass

    # Set up for the excluded options
    if query.excluded_low_rate:
        sql_query += " AND rate >= 40"
    excluded_options = set(i for i in query.excluded_options.split("+")) if query.excluded_options else None
    if excluded_options:
        for option in excluded_options:
            sql_query += f" AND options NOT LIKE '%#{option}#%'"

    ### EXECUTING THE QUERY ###
    # Connect to the database
    with connect_readonly(database_path) as conn:
        cur = conn.cursor()
        cur.execute(sql_query)

        # Fetch the result of the query and convert it to a dictionary
        result = cur.fetchall()
        # print(f"Time elapsed in database: {time.time() - start} seconds.")
        if result is None or len(result) == 0:
            return {"state": "error", "message": "No similar works found."}
        else:
            result = [dict(zip([description[0] for description in cur.description], i)) for i in result]
            result_tags = [list(filter(None, work["tags"].split("#"))) for work in result]
    print(f"Time elapsed in database: {time.time() - start} seconds.")
    print(len(result_tags))

    ### CALCULATING THE SIMILARITY ###
    start2 = time.time()

    # Get weights for the genres
    genre_weights = GG.get_weighting(weigth_func_dict[query.weight_func])

    # Calculate the similarity
    # First obtain the embedding of the query and the works
    query_embedding = sum([genre_weights[i] for i in genres]) / len(genres)
    works_embedding = [sum([genre_weights[i] for i in work_tags]) / len(work_tags) for work_tags in result_tags]
    # print(f"Time elapsed in embedding: {time.time() - start2} seconds.")

    # Convert the embeddings to tensors
    query_embedding = torch.tensor(query_embedding, dtype=torch.float32)
    works_embedding = torch.tensor(np.array(works_embedding), dtype=torch.float32)
    # print(f"Time elapsed in converting to tensors: {time.time() - start2} seconds.")

    # Calculate the cosine similarity
    similarity = cos_sim(query_embedding, works_embedding)

    # Weight the similarity by the dlCount if specified
    if query.dlcount != 50:
        weights = dlCount_weight(query.dlcount, np.array([work["dlCount"] for work in result]), mu=2.09, std=1)
        # float64, matching the legacy `tensor *= ndarray` result.
        similarity = similarity.double() * torch.from_numpy(weights)
    top_similar_works = torch.topk(similarity, k=min(240, len(result)))

    similar_work_list = [(result[i]["index"], similarity[i].item()) for i in top_similar_works.indices]
    # similar_work_list = [(result[i["corpus_id"]]["index"], i["score"]) for i in similarity]

    print(f"Time elapsed in calculating similarity: {time.time() - start2} seconds.")

    return {
        "state": "success",
        "result": similar_work_list,
        "info": {"length": len(result), "time": time.time() - start},
    }


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
