import time
import os
import re
import json
import threading
import requests
import pandas as pd
import numpy as np
import pickle
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timedelta
from typing import Any


headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/22.0"}
REQUEST_TIMEOUT = 30
MAX_ATTEMPTS = 5
TRANSLATION_LANGS = ("ENG", "CHI_HANT", "CHI_HANS")
# DLsite returns an edition's own title only when asked for the matching locale.
EDITION_LOCALES = {"ENG": "en_US", "CHI_HANT": "zh_TW", "CHI_HANS": "zh_CN"}
LISTING_PAGE_SIZE = 100
CHECKPOINT_EVERY = 200
DEFAULT_WORKERS = 6
DEFAULT_RATE = 4.0
# The search listing is stricter than the product API: at 4 requests per second it answered 403.
LISTING_RATE = 1.0
MAX_INTERVAL = 4.0
THROTTLE_PAUSE = 30

# Language names accepted on the command line; JA is the original language, so it needs nothing fetched.
LANGUAGE_ALIASES = {
    "JA": None,
    "JPN": None,
    "EN": "ENG",
    "ENG": "ENG",
    "TC": "CHI_HANT",
    "CHI_HANT": "CHI_HANT",
    "SC": "CHI_HANS",
    "CHI_HANS": "CHI_HANS",
}


def _tokens(values: Iterable[str]) -> list[str]:
    return [token.upper() for value in values for token in re.split(r"[,\s]+", value) if token]


def parse_languages(values: Iterable[str]) -> list[str]:
    """
    Turn `JA EN TC SC NONE` (or `en,tc`) into the DLsite translation languages to fetch, in a fixed order.
    JA and NONE select no translations.

    Raises
    ------
    ValueError
        If a name is unknown or NONE is combined with other names.
    """
    tokens = _tokens(values)
    if "NONE" in tokens:
        if len(tokens) > 1:
            raise ValueError("NONE cannot be combined with other languages.")
        return []
    langs = set()
    for token in tokens:
        if token not in LANGUAGE_ALIASES:
            raise ValueError(f"Unknown language {token!r}. Use JA, EN, TC, SC or NONE.")
        if LANGUAGE_ALIASES[token]:
            langs.add(LANGUAGE_ALIASES[token])
    return [lang for lang in TRANSLATION_LANGS if lang in langs]


def parse_remove_targets(values: Iterable[str]) -> str | list[str]:
    """
    Turn the values of `--remove` into `"ALL"` or a list of translation languages.

    Raises
    ------
    ValueError
        If originals are named (translated rows depend on them, so only ALL removes them) or ALL is mixed in.
    """
    tokens = _tokens(values)
    if "ALL" in tokens:
        if len(tokens) > 1:
            raise ValueError("ALL cannot be combined with other targets.")
        return "ALL"
    if "JA" in tokens or "JPN" in tokens:
        raise ValueError("Original works cannot be removed on their own; use ALL to remove every work.")
    return parse_languages(tokens)


class RateLimiter:
    """
    Spaces requests from all threads at most `rate` per second, and can hold every thread back for a while.
    Each new pause also doubles the spacing (up to MAX_INTERVAL), so a run settles at a speed DLsite accepts.
    """

    def __init__(self, rate: float):
        self.interval = 1 / rate
        self._lock = threading.Lock()
        self._next = 0.0
        self._blocked_until = 0.0

    def wait(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                start = max(self._next, self._blocked_until)
                if start <= now:
                    self._next = now + self.interval
                    return
            time.sleep(start - now)

    def pause(self, seconds: float) -> None:
        with self._lock:
            now = time.monotonic()
            if now >= self._blocked_until:
                # Only the first of several simultaneous refusals slows the run down.
                self.interval = min(self.interval * 2, max(MAX_INTERVAL, self.interval))
                print(f"DLsite is refusing requests; pausing {seconds:g} s and slowing to {1 / self.interval:.2g}/s.")
            self._blocked_until = max(self._blocked_until, now + seconds)


_local = threading.local()


def _session() -> requests.Session:
    session = getattr(_local, "session", None)
    if session is None:
        session = _local.session = requests.Session()
        session.headers.update(headers)
    return session


def _retry_after(response: requests.Response, attempt: int) -> float:
    """Seconds to back off after HTTP 403/429: Retry-After if sent, else THROTTLE_PAUSE doubling per attempt."""
    try:
        return max(float(response.headers.get("Retry-After", "")), 1)
    except ValueError:
        return THROTTLE_PAUSE * 2 ** (attempt - 1)


def _request_json(url: str, label: str, limiter: RateLimiter | None = None) -> Any:
    """
    GET `url` as JSON, retrying with exponential backoff and raising after MAX_ATTEMPTS failures.
    HTTP 403 and 429 make the limiter hold every thread back for the backoff time.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if limiter:
            limiter.wait()
        delay = 5 * 2 ** (attempt - 1)
        try:
            response = _session().get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code in (403, 429):
                delay = _retry_after(response, attempt)
                if limiter:
                    limiter.pause(delay)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"Failed to fetch {label} after {MAX_ATTEMPTS} attempts ({e}).") from e
            print(f"Error fetching {label}: {e}. Retrying in {delay:g} seconds ({attempt}/{MAX_ATTEMPTS})...")
            time.sleep(delay)


def run_parallel(
    tasks: Iterable[Any],
    work: Callable[[Any], Any],
    on_result: Callable[[Any], None],
    workers: int,
    desc: str,
    limit: int | None = None,
    checkpoint: Callable[[], None] | None = None,
    unit: str = "work",
) -> int:
    """
    Run `work(task)` on a thread pool and pass every result to `on_result` on the calling thread, so the caller's
    tables need no locks. At most `limit` tasks run. `checkpoint` is called every CHECKPOINT_EVERY results and
    once more when the run ends for any reason, including Ctrl-C and errors, which are re-raised.

    Returns
    -------
    int
        The number of tasks completed.
    """
    from tqdm import tqdm

    tasks = list(tasks)
    if limit is not None:
        tasks = tasks[:limit]
    done = 0
    pending: set = set()
    queue = iter(tasks)
    executor = ThreadPoolExecutor(max_workers=workers)
    bar = tqdm(total=len(tasks), desc=desc, unit=unit, disable=None)
    try:
        while True:
            while len(pending) < workers * 8:
                task = next(queue, None)
                if task is None:
                    break
                pending.add(executor.submit(work, task))
            if not pending:
                break
            finished, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in finished:
                on_result(future.result())
                done += 1
                bar.update(1)
                if checkpoint and done % CHECKPOINT_EVERY == 0:
                    checkpoint()
        executor.shutdown()
    except BaseException:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        bar.close()
        if checkpoint and done:
            checkpoint()
    return done


def remove_translation_data(path: str, langs: Sequence[str], dry_run: bool = False) -> tuple[int, int]:
    """
    Delete the editions and the localised titles of `langs` from `translation_table.json` and `title_table.json`.

    Returns
    -------
    tuple[int, int]
        The number of editions and of title entries removed (or that would be, for a dry run).
    """
    counts = [0, 0]
    for index, name in enumerate(("translation_table.json", "title_table.json")):
        file = os.path.join(path, name)
        if not os.path.isfile(file):
            continue
        with open(file, "r", encoding="utf-8") as f:
            table = json.load(f)

        if index == 0:
            for workno in [k for k, v in table.items() if v.get("lang") in langs]:
                del table[workno]
                counts[0] += 1
        else:
            for workno in list(table):
                for lang in [lang for lang in langs if lang in table[workno]]:
                    del table[workno][lang]
                    counts[1] += 1
                if not table[workno]:
                    del table[workno]

        if not dry_run and counts[index]:
            with open(file + ".tmp", "w", encoding="utf-8") as f:
                json.dump(table, f, ensure_ascii=False)
            os.replace(file + ".tmp", file)
    return counts[0], counts[1]


class DLsiteCatalog:
    """
    This class is used to create and manage the catalogue of DLsite works.
    The catalogue is saved in two tables: `works_table` and `dates_table`.

    The `works_table` is a dictionary containing data of all the works, with the work ID as the key.
    The `dates_table` is a dictionary containing all the dates that the catalogue has been updated.

    ### Usage example
    ```
    # Initialize a new catalogue
    DL = DLsiteCatalog()

    # Or load an existing catalogue from `path`
    DL = DLsiteCatalog(path)

    # Print the dates recorded in the catalogue
    DL.print_date()

    # Get the work data of a day
    DL.get_data_one_day("2020-01-01")

    # Get the work data from `date1` to `date2`
    DL.get_data_duration("2020-01-01", "2020-01-31")

    # Save the catalogues
    DL.save_tables("path/to/save")
    ```
    """

    def __init__(self, path: str = ""):
        """
        Initialize the DLsiteCatalog.
        If path is specified, load the catalogue from the path, otherwise create a new one.

        Parameters
        ----------
        path : str, optional
            The path of the catalogue. If `path` is "", create a new catalogue. The default is "".
        """
        self.translation_table = {}
        self.title_table = {}
        if path == "":
            self.works_table = {}
            self.dates_table = {}
        else:
            with open(os.path.join(path, "works_table.json"), "r", encoding="utf-8") as f:
                self.works_table = json.load(f)
            with open(os.path.join(path, "dates_table.json"), "r", encoding="utf-8") as f:
                self.dates_table = json.load(f)
            translation_path = os.path.join(path, "translation_table.json")
            if os.path.isfile(translation_path):
                with open(translation_path, "r", encoding="utf-8") as f:
                    self.translation_table = json.load(f)
            title_path = os.path.join(path, "title_table.json")
            if os.path.isfile(title_path):
                with open(title_path, "r", encoding="utf-8") as f:
                    self.title_table = json.load(f)

    def get_data_duration(self, date1: str, date2: str):
        """
        Get the work data from `date1` to `date2`, both included. Will call get_data_one_day() for updating `self.works_table`.
        Raise error if `date2` is earlier than `date1`; the same day is allowed and crawls that day again.

        Parameters
        ----------
        date1 : str
            The start date. Format: YYYY-MM-DD
        date2 : str
            The end date. Format: YYYY-MM-DD
        """
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        duration = (d2 - d1).days
        if duration < 0:
            print("Error: date2 must not be earlier than date1.")
        else:
            for i in range(duration + 1):
                date = (d1 + timedelta(i)).strftime("%Y-%m-%d")
                self.get_data_one_day(date)

    def get_data_one_day(self, date: str):
        """
        Get the work data of `date`. Will call get_outline() for updating `self.works_table`.
        Retries with exponential backoff and raises after MAX_ATTEMPTS failures.

        Parameters
        ----------
        date : str
            The date. Format: YYYY-MM-DD
        """
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                print(f"Fetching data for {date}...", end="")
                table = self.get_outline(date)
                break
            except Exception as e:
                print(f"Error: {e}")
                if attempt == MAX_ATTEMPTS:
                    raise RuntimeError(f"Failed to fetch {date} after {MAX_ATTEMPTS} attempts.") from e
                delay = 5 * 2 ** (attempt - 1)
                print(f"Retrying in {delay} seconds ({attempt}/{MAX_ATTEMPTS})...")
                time.sleep(delay)

        now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        self.works_table.update({work["id"]: work for work in table})
        self.dates_table.update({date: now})
        print(f"Success ({len(table)} records)")

    def save_tables(self, path: str):
        """
        Save the catalogues to JSON files.

        Parameters
        ----------
        path : str
            The path to save the catalogues.
        """
        with open(os.path.join(path, "works_table.json"), "w", encoding="utf-8") as f:
            json.dump(self.works_table, f)
        with open(os.path.join(path, "dates_table.json"), "w", encoding="utf-8") as f:
            json.dump(self.dates_table, f)
        self.save_translations(path)

    def save_translations(self, path: str):
        """Save only the translation and title tables, so long crawls can checkpoint without rewriting `works_table`."""
        for name, table in (("translation_table.json", self.translation_table), ("title_table.json", self.title_table)):
            target = os.path.join(path, name)
            with open(target + ".tmp", "w", encoding="utf-8") as f:
                json.dump(table, f, ensure_ascii=False)
            os.replace(target + ".tmp", target)

    def title_tasks(self, langs: Sequence[str] = TRANSLATION_LANGS) -> list[tuple[str, list[str]]]:
        """
        The works whose localised titles in `langs` are not recorded yet, newest first, as (work ID, languages).
        Only works offered in Japanese plus the language are included, because only they have one ID per language.
        """
        tasks = []
        for workno, work in self.works_table.items():
            options = work.get("options") or []
            if "JPN" not in options:
                continue
            recorded = self.title_table.get(workno, {})
            missing = [lang for lang in langs if lang in options and lang not in recorded]
            if missing:
                tasks.append((workno, missing))
        tasks.sort(key=lambda task: (len(task[0]), task[0]), reverse=True)
        return tasks

    def fetch_localized_titles(
        self,
        path: str,
        limit: int | None = None,
        langs: Sequence[str] = TRANSLATION_LANGS,
        workers: int = DEFAULT_WORKERS,
        rate: float | None = None,
    ) -> int:
        """
        Record the official titles in `langs` of works that offer those languages under one work ID.

        DLsite shows such a work with a different title per locale, while `works_table` holds the Japanese one.
        `title_table[workno]` maps each language to its title, or None if it equals the Japanese title.
        Newest works come first and recorded languages are skipped, so reruns resume. The table is saved to
        `path` periodically and on exit.

        Parameters
        ----------
        limit : int, optional
            The maximum number of works to look up in this run. The default is unlimited.
        workers : int
            The number of parallel requests.
        rate : float, optional
            The maximum number of requests per second in total. The default is DEFAULT_RATE.

        Returns
        -------
        int
            The number of works looked up.
        """
        limiter = RateLimiter(rate or DEFAULT_RATE)

        def lookup(task: tuple[str, list[str]]) -> tuple[str, dict[str, str | None]]:
            workno, missing = task
            japanese = self.works_table[workno].get("name")
            titles = {}
            for lang in missing:
                url = f"https://www.dlsite.com/maniax/api/=/product.json?workno={workno}&locale={EDITION_LOCALES[lang]}"
                data = _request_json(url, workno, limiter)
                title = data[0].get("work_name") if data else None
                titles[lang] = title if title and title != japanese else None
            return workno, titles

        def store(result: tuple[str, dict[str, str | None]]) -> None:
            workno, titles = result
            self.title_table.setdefault(workno, {}).update(titles)

        return run_parallel(
            self.title_tasks(langs), lookup, store, workers, "Titles", limit, lambda: self.save_translations(path)
        )

    @staticmethod
    def list_language_page(lang: str, page: int, limiter: RateLimiter | None = None) -> tuple[list[str], int]:
        """
        Get one page of the DLsite search results for works offered in `lang`, newest first.
        The results mix original works with their translated editions.

        Returns
        -------
        tuple[list[str], int]
            The work IDs on the page and the total number of results.
        """
        url = (
            "https://www.dlsite.com/maniax/fsr/ajax/=/language/jp/order/release_d"
            f"/options%5B0%5D/{lang}/options_and_or/and/per_page/{LISTING_PAGE_SIZE}/page/{page}/from/fs.header"
        )
        data = _request_json(url, f"{lang} listing page {page}", limiter)
        ids = re.findall(r'data-list_item_product_id="(RJ\d+)"', data["search_result"])
        return list(dict.fromkeys(ids)), int(data["page_info"]["count"])

    @staticmethod
    def get_translation_info(workno: str, lang: str = "ENG", limiter: RateLimiter | None = None) -> dict[str, Any]:
        """
        Look up `workno` on DLsite and describe it as a translated edition.

        Parameters
        ----------
        lang : str
            The edition language expected, which selects the locale of the returned title and circle.
            If the work turns out to be an edition in another language, it is looked up again for that one.

        Returns
        -------
        dict
            For an official ENG, CHI_HANT or CHI_HANS edition: its language, original work ID and language,
            and the edition's own title, circle, release date, options and site.
            Otherwise (original work, other language, unavailable): `{"lang": None}`.
        """
        url = f"https://www.dlsite.com/maniax/api/=/product.json?workno={workno}&locale={EDITION_LOCALES[lang]}"
        data = _request_json(url, workno, limiter)
        now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        if not data:
            return {"lang": None, "fetchedAt": now}

        product = data[0]
        info = product.get("translation_info") or {}
        actual, original = info.get("lang"), info.get("original_workno")
        if actual not in TRANSLATION_LANGS or not original or original == workno:
            return {"lang": None, "fetchedAt": now}
        if actual != lang:
            return DLsiteCatalog.get_translation_info(workno, actual, limiter)

        editions = {e["workno"]: e.get("lang") for e in product.get("language_editions") or []}
        return {
            "lang": lang,
            "originalWorkno": original,
            "originalLang": editions.get(original) or "JPN",
            "name": product["work_name"],
            "maker": product.get("maker_name"),
            "makerId": product.get("maker_id"),
            "registDate": product.get("regist_date"),
            "options": product.get("options"),
            "siteId": product.get("site_id"),
            "fetchedAt": now,
        }

    def fetch_translations(
        self,
        path: str,
        limit: int | None = None,
        langs: Sequence[str] = TRANSLATION_LANGS,
        workers: int = DEFAULT_WORKERS,
        rate: float | None = None,
    ) -> int:
        """
        Find the official editions in `langs` that have their own work ID and record them in `translation_table`.

        Every listing page is scanned, but only IDs that are in neither `works_table` nor `translation_table`
        are looked up, so reruns resume where an interrupted run stopped. The table is saved to `path`
        periodically and on exit.

        Parameters
        ----------
        path : str
            The directory to save `translation_table.json`.
        limit : int, optional
            The maximum number of works to look up in this run. The default is unlimited.
        workers : int
            The number of parallel requests.
        rate : float, optional
            The maximum number of requests per second in total. The default is DEFAULT_RATE.

        Returns
        -------
        int
            The number of works looked up.
        """
        limiter = RateLimiter(rate or DEFAULT_RATE)
        listing_limiter = RateLimiter(min(rate or DEFAULT_RATE, LISTING_RATE))

        # First collect the unknown IDs, newest first, so that a limit keeps the newest editions.
        unknown: dict[str, str] = {}
        for lang in langs:
            ids, total = self.list_language_page(lang, 1, listing_limiter)
            pages = {1: ids}
            run_parallel(
                range(2, -(-total // LISTING_PAGE_SIZE) + 1),
                lambda page: (page, self.list_language_page(lang, page, listing_limiter)[0]),
                lambda result: pages.__setitem__(*result),
                workers,
                f"Listing {lang}",
                unit="page",
            )
            for page in sorted(pages):
                for workno in pages[page]:
                    if workno not in self.works_table and workno not in self.translation_table:
                        unknown.setdefault(workno, lang)

        def store(result: tuple[str, dict[str, Any]]) -> None:
            self.translation_table[result[0]] = result[1]

        return run_parallel(
            unknown.items(),
            lambda task: (task[0], self.get_translation_info(task[0], task[1], limiter)),
            store,
            workers,
            "Editions",
            limit,
            lambda: self.save_translations(path),
        )

    def print_date(self) -> datetime:
        """
        Print the dates that the catalogue has been updated.

        Returns
        -------
        datetime.datetime
            The last date that the catalogue has been updated.
        """
        # Find all the dates and sort them
        dates = [datetime.strptime(i, "%Y-%m-%d") for i in self.dates_table.keys()]
        dates.sort()

        # If there is only one date, print it and return
        if len(dates) < 2:
            print(dates)
            return dates[0]

        # If there are more than one date, print the dates that are not consecutive
        previous_date = dates[0]
        i, j = dates[0], dates[1]  # set for avoiding error
        for i, j in zip(dates[:-1], dates[1:]):
            if (j - i).days > 1:
                if i == previous_date:
                    print(i.strftime("%Y-%m-%d"))
                else:
                    print(f"{previous_date.strftime('%Y-%m-%d')} = {i.strftime('%Y-%m-%d')}")
                previous_date = j

        if j == previous_date:
            print(j.strftime("%Y-%m-%d"))
        else:
            print(f"{previous_date.strftime('%Y-%m-%d')} = {j.strftime('%Y-%m-%d')}")
        return dates[-1]

    def _to_dataframe(self) -> pd.DataFrame:
        """
        Convert the catalogue to a pandas DataFrame.

        Returns
        -------
        pandas.DataFrame
            The catalogue.
        """
        return pd.DataFrame.from_dict(self.works_table).T

    @staticmethod
    def get_outline(date: str) -> list[dict[str, Any]]:
        """
        Get the work data of `date`.
        Usage example: DLsite_catalog.getOutline("2021-09-01")

        Parameters
        ----------
        date : str
            The date. Format: YYYY-MM-DD

        Returns
        -------
        list
            A list of dictionaries containing the work data of `date`.
        """
        response = requests.get(f"https://www.dlsite.com/maniax/new/work/api?date={date}", timeout=REQUEST_TIMEOUT)
        data = response.json()

        if data["meta"]["code"] != 200:
            raise ValueError(f"Error: {data['meta']}")
        else:
            return data["data"]["products"]


class GenreCatalog:
    """
    This class manipulates genres in DLsite. It contains 2 parts: `genre_catalogue` and `genre_embedding`.

    The `genre_catalogue` is a dictionary containing the localised genre names, category names and work counts of DLsite.
    A example structure of genre_catalogue is as follows:
    ```
    {
        "509": {
            "category": {
                "ja_JP": "こだわり/アピール",
                "en_US": "Focus/Appeals",
                "zh_CN": "偏好/需求",
                "zh_TW": "偏好/呈現手法",
                "ko_KR": "어필 포인트"
            },
            "name": {
                "ja_JP": "3D作品",
                "en_US": "3D Works",
                "zh_CN": "3D作品",
                "zh_TW": "3D作品",
                "ko_KR": "3D 작품"
            },
            "count": 12714
        }
    }
    ```
    Here "509" is the genre ID of "3D作品" in DLsite. The genre ID is a string of 3 digits.

    The `genre_embedding` is a dictionary containing the embeddings of genres, with keys being the genre IDs and values being the embeddings.
    The embeddings are generated by the sentence-transformers library.

    ### Usage example
    ```
    # Initialise a new GenreCatalog
    genre_catalogue = GenreCatalog("maniax")

    # Compute the embeddings of genres
    genre_catalogue.get_embedding(model, "path/to/save")

    # Save the catalogue
    genre_catalogue.save_data("path/to/save")

    # Load custom genre embeddings
    genre_catalogue.load_embedding("path/to/embedding")

    # Concatenate genre catalogues
    new_catalog = GenreCatalog.concat_genre([GenreCatalog("maniax"), GenreCatalog("pro"), GenreCatalog("books")])
    ```
    """

    def __init__(self, target: str, path: str = ""):
        """
        Initialise the GenreCatalog.
        If path is specified, load the catalogue from the path, otherwise create a new one.

        Parameters
        ----------
        target : str
            The work scope of DLsite. For example, "maniax".
        path : str, optional
            The path of the genre catalogue. If `path` is "", create a new catalogue. The default is "".
        """
        self.target = target
        self.locales = ["ja_JP", "en_US", "zh_CN", "zh_TW", "ko_KR"]

        if path == "":
            fetch_data = self.fetch_data()
            self.genre_catalogue = fetch_data[0]
            self.workformat = fetch_data[1]
            self.genre_embedding = {}
        else:
            with open(os.path.join(path, "genre_table.json"), "r", encoding="utf-8") as f:
                self.genre_catalogue = json.load(f)
            with open(os.path.join(path, "workformat.json"), "r", encoding="utf-8") as f:
                self.workformat = json.load(f)
            self.load_embedding(path)

    def fetch_data(self) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        """
        Crawl the genre catalogue and localisation information from DLsite.

        Returns
        -------
        genres_dict : dict
            The crawled genre catalogue, including the localised genre names, category names and work counts.
        workformat : dict
            The localisation information for the work format.
        """
        from bs4 import BeautifulSoup
        from urllib.request import urlopen, Request

        # Define the URLs
        locale_url = f"https://www.dlsite.com/{self.target}/fs/=/api_access/1"
        wokrcount_url = f"https://www.dlsite.com/{self.target}/genre/list"

        # Create empty dictionaries to store the genre information
        genres_dict = {}
        workformat = {}

        # First create the genre dictionary with the Japanese locale
        # Then update the genre dictionary with the other locales
        # At the same time, create the work format dictionary
        for locale in self.locales:
            cookies = {"locale": locale}
            response = requests.get(locale_url, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
            data = response.json()
            print(f"Now processing {locale}...")

            # If the locale is Japanese, set the genre dictionary
            if locale == "ja_JP":
                for category in data["genre_all"]:
                    for genre in category["values"]:
                        genres_dict[genre["value"]] = {
                            "category": {locale: category["category_name"]},
                            "name": {locale: genre["name"]},
                        }
                for key, format in data["worktype_all"].items():
                    if key != "work_type_category":
                        for worktype in format["values"]:
                            workformat[worktype["value"]] = {
                                "category": {locale: format["category_name"]},
                                "name": {locale: worktype["name"]},
                            }
            # If the locale is not Japanese, update the genre dictionary
            else:
                for category in data["genre_all"].values():
                    for genre in category["values"]:
                        try:
                            genres_dict[genre["value"]]["name"].update({locale: genre["name"]})
                            genres_dict[genre["value"]]["category"].update({locale: category["category_name"]})
                        except KeyError:
                            print(genre["value"], genre["name"])
                for key, format in data["worktype_all"].items():
                    if key != "work_type_category":
                        for worktype in format["values"]:
                            try:
                                workformat[worktype["value"]]["name"].update({locale: worktype["name"]})
                                workformat[worktype["value"]]["category"].update({locale: format["category_name"]})
                            except KeyError:
                                print(worktype["value"], worktype["name"])

        # Update the genre dictionary with the count information
        req = Request(url=wokrcount_url, headers=headers)
        soup = BeautifulSoup(urlopen(req, timeout=REQUEST_TIMEOUT), "html.parser")
        versatility_linklist_wrapper = soup.find_all("div", class_="versatility_linklist_wrapper")

        # Loop through each wrapper
        for wrapper in versatility_linklist_wrapper:
            # Find the title and genres list
            titles = wrapper.find_all("h2", class_="versatility_linklist_title")
            genres_list = wrapper.find_all("ul", class_="versatility_linklist")

            for title, genres in zip(titles, genres_list):
                genres = genres.find_all("a")
                # Loop through each genre
                for genre in genres:
                    # Get the genre ID and name
                    genre_id = genre.get("href").split("/")[-1]
                    name_raw = genre.text.replace(",", "")

                    # Update the genre dictionary with the genre count
                    count = re.search(r"\(\d+\)$", name_raw)
                    if count:
                        genres_dict[genre_id]["count"] = int(count.group(0).replace("(", "").replace(")", ""))
                    else:  # it seems we will never get here, as all genres in the count page have counts
                        print(f"Warning: {name_raw} has no count information.")
                        genres_dict[genre_id]["count"] = 0

        # set 0 count for genres that are not in the count page
        for genre_id in genres_dict.keys():
            if "count" not in genres_dict[genre_id].keys():
                genres_dict[genre_id]["count"] = 0

        return genres_dict, workformat

    def save_data(self, path: str):
        """
        Save the genre catalogue and the localisation information to the path.

        Parameters
        ----------
        path : str
            The path to save the genre catalogue
        """
        with open(os.path.join(path, "genre_table.json"), "w", encoding="utf-8") as f:
            json.dump(self.genre_catalogue, f)
        with open(os.path.join(path, "workformat.json"), "w", encoding="utf-8") as f:
            json.dump(self.workformat, f)

    def load_embedding(self, path: str):
        """
        Load the genre embeddings from 'genre_vec.npy' in the path.

        Parameters
        ----------
        path : str
            The path to load the genre embeddings.
        """
        with open(os.path.join(path, "genre_vec.pkl"), "rb") as f:
            self.genre_embedding = pickle.load(f)

    def get_embedding(self, model_name: str, path: str):
        """
        Compute and save the embeddings of the genre catalogue.

        Parameters
        ----------
        model_name : str
            The model name of sentence_transformers.SentenceTransformer for computing the embeddings.
        path : str
            The path to save the embeddings.
        """
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name)

        for genre_id, genre in self.genre_catalogue.items():
            name = genre["name"]["ja_JP"]
            if "/" in name:
                name = name.split("/")
                embed = sum(model.encode(name)) / len(name)
            else:
                embed = model.encode([name])[0]
            self.genre_embedding[genre_id] = embed

        with open(os.path.join(path, "genre_vec.pkl"), "wb") as f:
            pickle.dump(self.genre_embedding, f)

    def get_weighting(self, weight_func: str = "r_logistic") -> dict[str, np.ndarray]:
        """
        Compute the embedding weighting of each genre based on its count and a given weight function.

        Parameters
        ----------
        weight_func : str, optional
            The name of the weight function to use. Default is "r_logistic".
            Options are "r_logistic", "logistic", "gaussian", and "linear".
            See the documentation of the `weight` function for details.

        Returns
        -------
        embed_weightings : dict
            A dictionary of the genre ID and its corresponding embedding weighting.
        """
        embed_weightings = {}
        for genre_id, genre_embed in self.genre_embedding.items():
            count = self.genre_catalogue[genre_id]["count"]
            weight = self.weight(count, weight_func)
            embed_weightings[genre_id] = genre_embed * weight
        return embed_weightings

    @staticmethod
    def concat_genre(base: dict[str, Any], tables: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Concatenate multiple genre catalogues into one.
        Take the fisrt catalogue as the base and update the genre names and counts from the other catalogues.
        Useful when you want to combine the genre catalogues crawled from different targets.

        Parameters
        ----------
        base : dict
            The base genre catalogue.
        tables : list[dict]
            The list of genre catalogues to be concatenated.

        Returns
        -------
        genre : dict
            The concatenated genre catalogue.
        """
        for table in tables:
            for genre_id, genre in table.items():
                if genre_id in base:
                    try:
                        base[genre_id]["count"] += genre["count"]
                        # update the genre name if the new one is longer
                        if "ja_JP" in genre["name"] and len(genre["name"]) > len(base[genre_id]["name"]):
                            base[genre_id]["name"] = genre["name"]
                            base[genre_id]["category"] = genre["category"]
                    except KeyError:
                        print(f"Warning: {genre_id} has no count information.")
                else:
                    base[genre_id] = genre
        return base

    @staticmethod
    def weight(x: int, weight_func: str) -> float:
        """
        Compute the weight of a genre based on its count.

        Parameters
        ----------
        x : int
            The count of the genre.
        weight_func : str
            The weighting function to be used.
            1. r_logistic: Reverse logistic function.
            2. logistic: Logistic function.
            3. gaussian: Gaussian function.
            4. linear: Linear function.

        Returns
        -------
        weight : float
            The weight of the genre.
        """
        x = np.log10(int(x + 1))

        if weight_func == "r_logistic" or weight_func == 1:
            return -1 / (1 + np.exp((-x + 4.25) * 4)) + 1
        elif weight_func == "logistic" or weight_func == 2:
            return 1 / (1 + np.exp((-x + 2.75) * 4))
        elif weight_func == "gaussian" or weight_func == 3:
            return np.exp(-((x - 3.5) ** 2))
        elif weight_func == "linear" or weight_func == 4:
            return 1.0
        else:
            raise ValueError("Invalid weight function!")
