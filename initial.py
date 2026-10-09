import os
import argparse
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from module.dlsite import DLsiteCatalog, GenreCatalog

parser = argparse.ArgumentParser(description="Initial and update work databases.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    "-i",
    "--init",
    action="store_true",
    help="Initialize the database. Equivalent to --show if the database has existed.",
)
group.add_argument("-s", "--show", action="store_true", help="Print the existing dates in database.")
group.add_argument(
    "-u",
    "--update",
    action="store_true",
    help="Update the database to a day before current date.",
)
group.add_argument(
    "-d",
    "--date",
    nargs="+",
    help="Set the start date and end date for crawling the website into database. Only crawl one day if one argument is provided.",
)
parser.add_argument("--path", default="database", help="The path of database.")
parser.add_argument(
    "--model",
    default="sonoisa/sentence-luke-japanese-base-lite",
    help="The name of language model. Example: sonoisa/sentence-luke-japanese-base-lite (default), distiluse-base-multilingual-cased-v2.",
)
parser.add_argument(
    "--no_genre",
    action="store_true",
    help="[Debug] Avoid updating genre data. Only available for --date and --update.",
)
parser.add_argument(
    "--raw_only",
    action="store_true",
    help="[Debug] Avoid exporting SQLite database. Only available for --date and --update.",
)
args = parser.parse_args()


def check_date(date_str: str) -> bool:
    """
    Check if the date format and range are correct.

    Parameters
    ----------
    date_str : str
        The date string to be checked.

    Returns
    -------
    bool
        True if the date format and range are correct, False otherwise.
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Error: Date format incorrect. Should be YYYY-MM-DD.")
        return False

    if date > datetime.today() or date < datetime(2000, 1, 1):
        print("Error: Date out of available range. Should be between 2000-01-01 and today.")
        return False

    return True


# Check the date format and range are correct
if args.date:
    if check_date(args.date[0]) is False:
        exit()
    if len(args.date) == 2:
        if check_date(args.date[1]) is False:
            exit()
    elif len(args.date) > 2:
        print("Error: Invalid date input.")
        exit()

# Find for the catalogue
if os.path.isfile(os.path.join(args.path, "works_table.json")):
    DL = DLsiteCatalog(path=args.path)
    print(f"Loaded catalogue in {args.path}.")
    print("Dates recorded in the catalogue: ")
    DL.print_date()
    print(f"{len(DL.works_table)} works over {len(DL.dates_table)} days.")
    # If no update is required, exit
    if args.show or args.init:
        exit()
else:
    print(f"No catalogue found in {args.path}.")
    # If no update is required, exit
    if args.show or args.update:
        exit()

    flag = input(f"Create a new one at {args.path}? (Y/n) ")
    if flag == "Y":
        DL = DLsiteCatalog()
    else:
        exit()

if args.init:
    print("[Mode] INIT")
    while True:
        d1 = input("Please input the start date you want: YYYY-MM-DD:\n")
        if check_date(d1) is False:
            continue
        d2 = input("Please input the end date you want (optional): YYYY-MM-DD:\n")
        if d2 != "":
            if check_date(d2) is True:
                break
        else:
            break

    if d2 == "":
        DL.get_data_one_day(d1)
    else:
        DL.get_data_duration(d1, d2)
    DL.save_tables(args.path)
    print(f"Save work catalogue in {args.path}.")

elif args.update:
    print("[Mode] UPDATE")
    d1 = DL.print_date()
    d2 = datetime.today() - timedelta(1)
    if d1 >= d2:
        print("Error: The database is up to date.")
        exit()
    d1 = d1.strftime("%Y-%m-%d")
    d2 = d2.strftime("%Y-%m-%d")
    print(f"Update data from {d1} to {d2}")

    flag = input("Are you sure to update? (Y/n) ")
    if flag == "Y":
        DL.get_data_duration(d1, d2)
        DL.save_tables(args.path)
        print(f"Save work catalogue in {args.path}.")
    else:
        print("Abort. Continue to update the genre catalogue.")

elif args.date:
    print("[Mode] DATE")
    if len(args.date) == 1:
        DL.get_data_one_day(args.date[0])
    elif len(args.date) == 2:
        DL.get_data_duration(args.date[0], args.date[1])

    DL.save_tables(args.path)
    print(f"Save work catalogue in {args.path}.")

if args.init or not args.no_genre:
    # will override the genre catalogue if not init
    print("Downloading genre catalogues...")
    GG = GenreCatalog(target="maniax")
    GH = GenreCatalog(target="home")
    GL = GenreCatalog(target="girls-pro")

    # concat and save
    GG.genre_catalogue = GenreCatalog.concat_genre(GG.genre_catalogue, [GH.genre_catalogue, GL.genre_catalogue])

    print("Loading language model... it may take time to download if this is the first time you run.")
    GG.get_embedding(model_name=args.model, path=args.path)
    GG.save_data(path=args.path)
    print(f"Save genre catalogue in {args.path}.")

if args.init or not args.raw_only:
    print("Processing dataframes...")
    GG = GenreCatalog(target="", path=args.path)
    genre_set = set(GG.genre_catalogue.keys())
    df = DL._to_dataframe()

    # remove useless columns
    keys_to_del = [
        "rank",
        "id",
        "url",
        "category",
        "dlFormat",
        "img",
        "officialPrice",
        "localePrice",
        "localeOfficialPrice",
        "discountPercentage",
        "point",
        "pointEndDate",
        "reductionRate",
        "isFree",
        "freeEndDate",
        "freeOnly",
        "campaignEndDate",
        "isLimitWork",
        "isLimitSales",
        "isLimitInStock",
        "isTimesale",
        "limitEndDate",
        "salesPercentage",
        "onSale",
        "coupling",
        "gift",
        "showDownload",
        "isShowRate",
        "review",
        "isAna",
        "favUrl",
        "cartUrl",
        "authors",
        "icons",
        "isSmartphoneOnlyIcon",
        "salesDate",
        "touchStyle1",
        "pcGameImgUrls",
        "voiceBys",
        "announceComment",
        "isReserveWork",
    ]
    df = df.drop(keys_to_del, axis=1)
    df = df.dropna(subset=["tags"])

    df["tags"] = [[str(j["id"]).zfill(3) for j in i if str(j["id"]).zfill(3) in genre_set] for i in df["tags"]]
    df = df[df["tags"].map(len) > 0]

    df["tags"] = "#" + df["tags"].str.join("#") + "#"
    df["options"] = "#" + df["options"].str.join("#") + "#"
    df["makerId"] = df["maker"].apply(lambda x: x["id"])
    df["maker"] = df["maker"].apply(lambda x: x["name"])
    df["rateCount"] = df["rate"].apply(lambda x: x["count"])
    df["rate"] = df["rate"].apply(lambda x: x["averageStar"])
    df["type"] = df["type"].apply(lambda x: x["id"])

    df["dlCount"] = df["dlCount"].astype(int)
    df["registDate"] = pd.to_datetime(df["registDate"], unit="s")
    df["ageCategory"] = df["ageCategory"].astype(int)
    df["sexCategory"] = df["sexCategory"].astype(int)
    df["inservice"] = df["inservice"].astype(int)
    df["price"] = df["price"].astype(int)
    df["rate"] = df["rate"].astype(int)
    df["rateCount"] = df["rateCount"].astype(int)
    df["reviewCount"] = df["reviewCount"].astype(int)

    # Convert nested DLsite API values into SQLite-compatible JSON strings.
    for column in df.columns:
        if df[column].dtype == "object":
            structured = df[column].map(
                lambda value: isinstance(value, (dict, list, tuple))
            )

            if structured.any():
                sample = df.loc[structured, column].iloc[0]
                print(
                    f"Serializing nested values in column {column!r} "
                    f"(example type: {type(sample).__name__})"
                )

                df[column] = df[column].map(
                    lambda value: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list, tuple))
                    else value
                )

    print("Exporting SQLite database...")
    db = sqlite3.connect(os.path.join(args.path, "works.sqlite"))
    df.to_sql("maniax", db, if_exists="replace")
    db.close()
    print("Done.")

    print("Exporting SQLite database...")
    db = sqlite3.connect(os.path.join(args.path, "works.sqlite"))
    df.to_sql("maniax", db, if_exists="replace")
    db.close()
    print("Done.")
