import time
import os
import re
import json
import requests
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import Any


headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/22.0"}


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
        if path == "":
            self.works_table = {}
            self.dates_table = {}
        else:
            with open(os.path.join(path, "works_table.json"), "r") as f:
                self.works_table = json.load(f)
            with open(os.path.join(path, "dates_table.json"), "r") as f:
                self.dates_table = json.load(f)

    def get_data_duration(self, date1: str, date2: str):
        """
        Get the work data from `date1` to `date2`. Will call get_data_one_day() for updating `self.works_table`.
        Raise error if `date2` is same as or earlier than `date1`.

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
        if duration <= 0:
            print("Error: date2 must be later than date1.")
        else:
            for i in range(duration + 1):
                date = (d1 + timedelta(i)).strftime("%Y-%m-%d")
                self.get_data_one_day(date)

    def get_data_one_day(self, date: str):
        """
        Get the work data of `date`. Will call get_outline() for updating `self.works_table`.

        Parameters
        ----------
        date : str
            The date. Format: YYYY-MM-DD
        """
        while True:
            try:
                print(f"Fetching data for {date}...", end="")
                table = self.get_outline(date)
                break
            except Exception as e:
                print(f"Error: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)

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
        with open(os.path.join(path, "works_table.json"), "w") as f:
            json.dump(self.works_table, f)
        with open(os.path.join(path, "dates_table.json"), "w") as f:
            json.dump(self.dates_table, f)

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
        response = requests.get(f"https://www.dlsite.com/maniax/new/work/api?date={date}")
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
            with open(os.path.join(path, "genre_table.json"), "r") as f:
                self.genre_catalogue = json.load(f)
            with open(os.path.join(path, "workformat.json"), "r") as f:
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
            response = requests.get(locale_url, headers=headers, cookies=cookies)
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
        soup = BeautifulSoup(urlopen(req), "html.parser")
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
        with open(os.path.join(path, "genre_table.json"), "w") as f:
            json.dump(self.genre_catalogue, f)
        with open(os.path.join(path, "workformat.json"), "w") as f:
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
