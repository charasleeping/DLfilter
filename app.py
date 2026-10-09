from datetime import datetime
from pydantic import BaseModel, constr
from typing import Any, List
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sentence_transformers import util
from module.dlsite import GenreCatalog
from module.utils import dlCount_weight
import torch
import numpy as np
import time
import os
import sqlite3

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
database_path = os.path.join("database", "works.sqlite")
GG = GenreCatalog(target="", path="database")

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
        regex=r"^[0-9]{3}(?:\+[0-9]{3}){0,9}$",
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
        regex=r"^[01]{3}$",
        description="The indicator of the age restriction, where the first char represents the all age, the second char represents the R15, and the third char represents the R18, i.e, `111` means all age, R15, and R18 are all included.",
    )
    excluded_low_rate: bool = True
    excluded_options: str | None = Query(
        "AIG+AIP+GRO+MEN",
        regex=r"^(?:AIG|AIP|GRO|MEN)(?:\+(?:AIG|AIP|GRO|MEN))*$",
        description="The excluded options. The options should be separated by `+`, and the options can be `AIG`, `AIP`, `GRO`, and `MEN`.",
    )
    # excluding_interest: bool = False # TODO: Add this option
    categories: str | None = Query(
        None,
        regex=r"^[A-Z0-9]{3}(\+[A-Z0-9]{3})*$",
        description="The target categories. The categories should be separated by `+`.",
    )
    included_genres: str | None = Query(
        None,
        regex=r"^[0-9]{3}(?:\+[0-9]{3}){0,4}$",
        description="The included genres. The genres should be separated by `+`. Maximum is 5.",
    )
    excluded_genres: str | None = Query(
        None,
        regex=r"^[0-9]{3}(?:\+[0-9]{3}){0,4}$",
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
        lmt = datetime.utcfromtimestamp(lmt).strftime("%Y-%m-%d %H:%M:%S")

        # Connect to the database
        with sqlite3.connect(database_path) as conn:
            # Create a cursor object to execute SQL queries
            cur = conn.cursor()

            # Execute a query to count the number of rows in the 'maniax' table
            cur.execute("SELECT COUNT([index]) FROM maniax")

            # Fetch the result of the query
            length = cur.fetchone()[0]

        # Return a dictionary containing the length of the database and the last modified time
        return {"state": "success", "length": length, "time": lmt}

    except Exception as e:
        return {"state": "error", "message": str(e)}


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
    List[dict]
        The information of the works.
    """
    if len(rj_id) > 50:
        return {"state": "error", "message": "The maximum number of requesting works is 50."}

    try:
        # Connect to the database
        with sqlite3.connect(database_path) as conn:
            # Create a cursor object to execute SQL queries
            cur = conn.cursor()

            # Execute a query to get the information of the work
            cur.execute("SELECT * FROM maniax WHERE [INDEX] IN ({})".format(",".join(["?"] * len(rj_id))), rj_id)
            result = cur.fetchall()

            result_dict = {index: {} for index in rj_id}

            # Check if the works exists
            for work in result:
                work = dict(zip([description[0] for description in cur.description], work))
                work["tags"] = [i for i in work["tags"].split("#") if i]
                work["options"] = [i for i in work["options"].split("#") if i]
                work["registDate"] = work["registDate"].split(" ")[0]
                result_dict[work["index"]] = work

        # Return a dictionary containing the information of the work
        return {"state": "success", "works": result_dict}

    except Exception as e:
        return {"state": "error", "message": str(e)}


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
    with sqlite3.connect(database_path) as conn:
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
    # top_k = min(240, len(result))
    # similarity = util.semantic_search(query_embedding, works_embedding, top_k=len(result), query_chunk_size=1)[0]
    similarity = util.cos_sim(query_embedding, works_embedding)[0]

    # Weight the similarity by the dlCount if specified
    if query.dlcount != 50:
        similarity *= dlCount_weight(query.dlcount, np.array([work["dlCount"] for work in result]), mu=2.09, std=1)
    top_similar_works = torch.topk(similarity, k=min(240, len(result)))

    similar_work_list = [(result[i]["index"], similarity[i].item()) for i in top_similar_works.indices]
    # similar_work_list = [(result[i["corpus_id"]]["index"], i["score"]) for i in similarity]

    print(f"Time elapsed in calculating similarity: {time.time() - start2} seconds.")

    return {
        "state": "success",
        "result": similar_work_list,
        "info": {"length": len(result), "time": time.time() - start},
    }
