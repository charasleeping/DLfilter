import os
import re
import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
from module import config
from module.database import add_localized_titles, add_translation_editions, export_works
from module.dlsite import (
    DEFAULT_RATE,
    DEFAULT_WORKERS,
    DLsiteCatalog,
    GenreCatalog,
    parse_languages,
    parse_remove_targets,
    remove_translation_data,
)

LARGE_CRAWL_DAYS = 31
KINDS = ("titles", "editions")
LANGUAGE_LABELS = {"ENG": "English", "CHI_HANT": "Traditional Chinese", "CHI_HANS": "Simplified Chinese"}
LANGUAGE_MENU = (
    ("JA", "Japanese only (no translations)"),
    ("EN", "English"),
    ("TC", "Traditional Chinese"),
    ("SC", "Simplified Chinese"),
)
REMOVE_MENU = (
    ("EN", "English translations"),
    ("TC", "Traditional Chinese translations"),
    ("SC", "Simplified Chinese translations"),
    ("ALL", "Every work (deletes works.sqlite)"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create, update, check and trim the work database.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-i",
        "--init",
        action="store_true",
        help="Initialize the database. Equivalent to --check if the database has existed.",
    )
    group.add_argument("-c", "--check", action="store_true", help="Print the existing dates in database.")
    group.add_argument(
        "-u",
        "--update",
        nargs="*",
        metavar="LANG",
        help="Update the original works to a day before current date, then fetch translations in the given languages: JA (originals only), EN, TC, SC or NONE. Asks which if none are given.",
    )
    group.add_argument(
        "-d",
        "--date",
        nargs="+",
        metavar="DATE|LANG",
        help="Crawl one day, or the days from the first date to the second (YYYY-MM-DD), then fetch translations in the languages listed after the dates, as with --update.",
    )
    group.add_argument(
        "-r",
        "--remove",
        nargs="*",
        metavar="TARGET",
        help="Remove the translations of EN, TC and/or SC, or every work with ALL, after a confirmation. Asks if no target is given.",
    )
    parser.add_argument(
        "-k",
        "--kinds",
        nargs="+",
        choices=KINDS,
        help="What to fetch: titles (works that offer several languages under one ID, fast) and/or editions (translations with their own ID, slow). Default: both.",
    )
    parser.add_argument("-s", "--skip", action="store_true", help="Skip every confirmation and question, using the defaults.")
    parser.add_argument("--path", default=str(config.DATA_DIR), help="The path of database.")
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS, help="Number of parallel requests when fetching translations."
    )
    parser.add_argument(
        "--rate",
        type=float,
        help=f"Maximum requests per second in total when fetching translations. Default: {DEFAULT_RATE:g}. DLsite blocks clients that go too fast.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of works to look up when fetching translations in this run. Rerun to continue.",
    )
    parser.add_argument(
        "--model",
        default=config.DEFAULT_MODEL,
        help="The name of language model or a local model directory. Example: sonoisa/sentence-luke-japanese-base-lite (default), distiluse-base-multilingual-cased-v2.",
    )
    parser.add_argument(
        "--no_genre",
        action="store_true",
        help="[Debug] Avoid updating genre data. Only available for --date and --update.",
    )
    parser.add_argument(
        "--raw_only",
        action="store_true",
        help="[Debug] Avoid exporting SQLite database. Only available for --date, --update and --remove.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse and validate the command line.
    Turns `update` into a bool, keeps only the dates in `date`, and adds `languages` (None if none were given,
    so the user is asked), `remove_targets` and `kinds`.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # --update takes languages, --date takes dates and languages; only languages contain no digits.
    raw_languages = None
    if args.update is not None:
        raw_languages = args.update
        args.update = True
    else:
        args.update = False
    if args.date is not None:
        dates = [value for value in args.date if any(char.isdigit() for char in value)]
        raw_languages = [value for value in args.date if value not in dates]
        if not dates:
            parser.error("--date needs at least one date, e.g. -d 2022-01-01 EN.")
        args.date = dates

    if args.kinds is not None and not (args.update or args.date is not None):
        parser.error("--kinds only applies to --update and --date.")
    if args.workers < 1:
        parser.error("--workers must be at least 1.")
    if args.rate is not None and args.rate <= 0:
        parser.error("--rate must be positive.")
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must not be negative.")

    args.languages = None
    args.remove_targets = None
    try:
        if raw_languages:
            args.languages = parse_languages(raw_languages)
        if args.remove:
            args.remove_targets = parse_remove_targets(args.remove)
    except ValueError as e:
        parser.error(str(e))
    args.kinds = [kind for kind in KINDS if kind in (args.kinds or KINDS)]
    return args


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


def require_terminal() -> None:
    if not sys.stdin.isatty():
        sys.exit("This needs an answer but there is no terminal. Run it in a terminal or pass -s/--skip.")


def confirm(args: argparse.Namespace, question: str, default: bool = True) -> bool:
    """Ask a yes/no question; --skip answers yes without asking."""
    if args.skip:
        return True
    require_terminal()
    answer = input(f"{question} ({'Y/n' if default else 'y/N'}) ").strip().lower()
    return default if not answer else answer in ("y", "yes")


def choose(title: str, menu: tuple[tuple[str, str], ...], default: str | None) -> list[str]:
    """Show a numbered menu and return the chosen codes; an empty answer gives `default` (or nothing)."""
    codes = [code for code, _ in menu]
    print(title)
    for number, (_, label) in enumerate(menu, 1):
        print(f"  {number}. {label}")
    while True:
        answer = input(f"Enter one or more numbers or codes{f' [{default}]' if default else ''}: ").strip()
        if not answer:
            return [default] if default else []
        tokens = [t for t in re.split(r"[,\s]+", answer.upper()) if t]
        chosen = [codes[int(t) - 1] if t.isdigit() and 1 <= int(t) <= len(codes) else t for t in tokens]
        if all(c in codes for c in chosen):
            return chosen
        print(f"Please use numbers 1-{len(codes)} or the codes {', '.join(codes)}.")


def ask_languages(args: argparse.Namespace) -> list[str]:
    """The translation languages to fetch, from a menu; --skip means none."""
    if args.skip:
        return []
    require_terminal()
    while True:
        try:
            return parse_languages(choose("Fetch translations too? Languages:", LANGUAGE_MENU, "JA"))
        except ValueError as e:
            print(e)


def ask_remove_targets() -> str | list[str]:
    require_terminal()
    while True:
        try:
            return parse_remove_targets(choose("Remove what?", REMOVE_MENU, None))
        except ValueError as e:
            print(e)


def check_dates(args: argparse.Namespace) -> bool:
    """Check the --date values, asking before a long crawl."""
    if len(args.date) > 2:
        print("Error: Invalid date input.")
        return False
    if not all(check_date(date) for date in args.date):
        return False
    if len(args.date) == 2:
        days = (datetime.strptime(args.date[1], "%Y-%m-%d") - datetime.strptime(args.date[0], "%Y-%m-%d")).days + 1
        if days > LARGE_CRAWL_DAYS and not confirm(
            args, f"This will crawl {days} days ({args.date[0]} to {args.date[1]}). Continue?"
        ):
            return False
    return True


def needs_rebuild(path: str) -> bool:
    """True if works.sqlite is missing or older than the tables it is built from."""
    database = os.path.join(path, "works.sqlite")
    if not os.path.exists(database):
        return True
    built = os.path.getmtime(database)
    sources = ("works_table.json", "translation_table.json", "title_table.json")
    return any(os.path.getmtime(os.path.join(path, s)) > built for s in sources if os.path.exists(os.path.join(path, s)))


def describe_translations(DL: DLsiteCatalog, args: argparse.Namespace, languages: list[str]) -> list[str]:
    names = ", ".join(LANGUAGE_LABELS[lang] for lang in languages)
    lines = [f"Translations: {names}, {args.workers} parallel requests, at most {args.rate or DEFAULT_RATE:g} per second."]
    if "titles" in args.kinds:
        tasks = DL.title_tasks(languages)
        requests_needed = sum(len(missing) for _, missing in tasks)
        minutes = round(requests_needed / (args.rate or DEFAULT_RATE) / 60)
        lines.append(f"  Titles: {len(tasks)} works, {requests_needed} requests, about {minutes} minutes.")
    if "editions" in args.kinds:
        lines.append("  Editions: counted after the listing pages are scanned; tens of thousands of requests at first.")
    return lines


def fetch_translations(DL: DLsiteCatalog, args: argparse.Namespace, languages: list[str]) -> int:
    made = 0
    if "titles" in args.kinds:
        made += DL.fetch_localized_titles(args.path, args.limit, languages, args.workers, args.rate)
    if "editions" in args.kinds and (args.limit is None or made < args.limit):
        left = None if args.limit is None else args.limit - made
        made += DL.fetch_translations(args.path, left, languages, args.workers, args.rate)
    return made


def stop_after_partial_run(DL: DLsiteCatalog, args: argparse.Namespace, message: str, code: int) -> None:
    """Report a stopped translation crawl, offer to rebuild works.sqlite from what was saved, and exit."""
    print(message)
    # Without a terminal and without --skip there is nobody to ask, so leave the database alone.
    if not args.raw_only and needs_rebuild(args.path) and (args.skip or sys.stdin.isatty()):
        if confirm(args, "Rebuild works.sqlite from what is saved so far?"):
            rebuild_database(DL, args.path)
    print("Rerun the same command to continue.")
    sys.exit(code)


def update_span(last: datetime, today: datetime) -> tuple[str, str | None] | None:
    """
    The dates `--update` should crawl: from the last recorded day to yesterday, or just yesterday again if it
    is the last recorded day (an update may be repeated within a day). None if the catalogue is ahead of that.
    """
    yesterday = (today - timedelta(1)).date()
    if last.date() > yesterday:
        return None
    if last.date() == yesterday:
        return yesterday.isoformat(), None
    return last.strftime("%Y-%m-%d"), yesterday.isoformat()


def update_genres(args: argparse.Namespace) -> None:
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


def init_crawl(DL: DLsiteCatalog, path: str) -> None:
    print("[Mode] INIT")
    require_terminal()
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
    DL.save_tables(path)
    print(f"Save work catalogue in {path}.")


def remove(args: argparse.Namespace) -> None:
    print("[Mode] REMOVE")
    targets = args.remove_targets
    if not args.remove:
        if args.skip:
            sys.exit("Say what to remove with --skip, e.g. -r EN TC or -r ALL.")
        targets = ask_remove_targets()
    if not targets:
        print("Nothing selected.")
        return

    database = os.path.join(args.path, "works.sqlite")
    if targets == "ALL":
        if not os.path.isfile(database):
            print(f"There is no database at {database}.")
            return
        print(f"This deletes {database} ({os.path.getsize(database) / 1e6:.0f} MB) with every work in it.")
        print("Its .bak copy, the raw catalogue, the genre files and the translation tables are kept.")
        if not confirm(args, "Delete it?", default=False):
            print("Abort.")
            return
        os.remove(database)
        print("Removed. Rebuild it with --update or --init.")
        return

    names = ", ".join(LANGUAGE_LABELS[lang] for lang in targets)
    editions, titles = remove_translation_data(args.path, targets, dry_run=True)
    if not editions and not titles:
        print(f"No {names} translations are recorded.")
        return
    print(f"This removes {editions} editions and {titles} localised titles ({names}) from the translation tables.")
    if not args.raw_only:
        print("The database is rebuilt afterwards, which needs the raw catalogue.")
    if not confirm(args, "Remove them?", default=False):
        print("Abort.")
        return
    remove_translation_data(args.path, targets)
    print("Removed from the translation tables.")
    if args.raw_only:
        return
    if not os.path.isfile(os.path.join(args.path, "works_table.json")):
        print("No raw catalogue to rebuild the database from; it is unchanged.")
        return
    rebuild_database(DLsiteCatalog(path=args.path), args.path)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.remove is not None:
        remove(args)
        return
    if args.date is not None and not check_dates(args):
        return

    # Find for the catalogue
    if os.path.isfile(os.path.join(args.path, "works_table.json")):
        DL = DLsiteCatalog(path=args.path)
        print(f"Loaded catalogue in {args.path}.")
        print("Dates recorded in the catalogue: ")
        DL.print_date()
        print(f"{len(DL.works_table)} works over {len(DL.dates_table)} days.")
        # If no update is required, exit
        if args.check or args.init:
            return
    else:
        print(f"No catalogue found in {args.path}.")
        # If no update is required, exit
        if args.check or args.update:
            return
        if not confirm(args, f"Create a new one at {args.path}?"):
            return
        DL = DLsiteCatalog()

    crawled = False
    if args.init:
        init_crawl(DL, args.path)
        crawled = True
    else:
        if args.update:
            print("[Mode] UPDATE")
            last = DL.print_date()
            span = update_span(last, datetime.today())
        else:
            print("[Mode] DATE")
            span = (args.date[0], args.date[1] if len(args.date) == 2 else None)

        languages = args.languages if args.languages is not None else ask_languages(args)
        if not span and not languages:
            print("The originals are up to date.")
            if not args.raw_only and needs_rebuild(args.path):
                print("works.sqlite is older than the saved tables.")
                rebuild_database(DL, args.path)
            return

        if args.update or languages:
            if span:
                print(f"Originals: {span[0]}" + (f" to {span[1]}" if span[1] else "") + ".")
            if languages:
                print("\n".join(describe_translations(DL, args, languages)))
            if not confirm(args, "Continue?"):
                print("Abort.")
                return

        if span:
            if span[1] is None:
                DL.get_data_one_day(span[0])
            else:
                DL.get_data_duration(span[0], span[1])
            DL.save_tables(args.path)
            print(f"Save work catalogue in {args.path}.")
            crawled = True

        if languages:
            print("[Mode] TRANSLATIONS")
            try:
                made = fetch_translations(DL, args, languages)
            except KeyboardInterrupt:
                stop_after_partial_run(DL, args, "Interrupted. Progress is saved.", 130)
            except RuntimeError as e:
                stop_after_partial_run(
                    DL, args, f"{e}\nProgress is saved. If DLsite answered 403 or 429, wait a while and lower --rate.", 1
                )
            editions = sum(1 for i in DL.translation_table.values() if i.get("lang"))
            print(f"Looked up {made} works; {len(DL.title_table)} works with titles and {editions} editions recorded.")

    if crawled and (args.init or not args.no_genre):
        update_genres(args)
    if args.init or (not args.raw_only and (crawled or needs_rebuild(args.path))):
        rebuild_database(DL, args.path)


def rebuild_database(DL: DLsiteCatalog, path: str) -> None:
    """Rebuild works.sqlite from the catalogue and the translation tables."""
    print("Processing dataframes...")
    GG = GenreCatalog(target="", path=path)
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

    df = add_localized_titles(df, DL.title_table)
    df = add_translation_editions(df, DL.translation_table)

    print("Exporting SQLite database...")
    backup = export_works(df, os.path.join(path, "works.sqlite"))
    if backup:
        print(f"Previous database kept at {backup}.")
    print("Done.")


if __name__ == "__main__":
    main()
