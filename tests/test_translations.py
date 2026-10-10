"""Translation crawling: language parsing, throttling, the thread pool, resumable crawls and removal."""

import json
import time

import pytest

import initial
from module import dlsite
from module.dlsite import (
    DLsiteCatalog,
    RateLimiter,
    parse_languages,
    parse_remove_targets,
    remove_translation_data,
    run_parallel,
)


def test_parse_languages():
    assert parse_languages(["EN", "tc"]) == ["ENG", "CHI_HANT"]
    assert parse_languages(["sc,en"]) == ["ENG", "CHI_HANS"]
    assert parse_languages(["CHI_HANS", "ENG", "TC"]) == ["ENG", "CHI_HANT", "CHI_HANS"]
    assert parse_languages(["JA"]) == []
    assert parse_languages(["JA", "EN"]) == ["ENG"]
    assert parse_languages(["none"]) == []


@pytest.mark.parametrize("values", [["FR"], ["NONE", "EN"]])
def test_parse_languages_rejects(values):
    with pytest.raises(ValueError):
        parse_languages(values)


def test_parse_remove_targets():
    assert parse_remove_targets(["all"]) == "ALL"
    assert parse_remove_targets(["EN", "SC"]) == ["ENG", "CHI_HANS"]
    for values in (["JA"], ["ALL", "EN"]):
        with pytest.raises(ValueError):
            parse_remove_targets(values)


def test_rate_limiter_spaces_requests():
    limiter = RateLimiter(50)
    start = time.monotonic()
    for _ in range(6):
        limiter.wait()
    assert time.monotonic() - start >= 5 * 0.02 * 0.9


def test_rate_limiter_pause_blocks_waiters():
    limiter = RateLimiter(1000)
    limiter.pause(0.2)
    start = time.monotonic()
    limiter.wait()
    assert time.monotonic() - start >= 0.18


class FakeResponse:
    def __init__(self, status, payload=None, headers=None):
        self.status_code = status
        self._payload = payload
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_request_json_throttle_pauses_limiter(monkeypatch):
    responses = [FakeResponse(429, headers={"Retry-After": "3"}), FakeResponse(200, {"ok": True})]
    monkeypatch.setattr(dlsite, "_session", lambda: type("S", (), {"get": lambda self, url, timeout: responses.pop(0)})())
    slept, paused = [], []
    monkeypatch.setattr(dlsite.time, "sleep", slept.append)

    class Limiter:
        def wait(self):
            pass

        def pause(self, seconds):
            paused.append(seconds)

    assert dlsite._request_json("http://x", "x", Limiter()) == {"ok": True}
    assert paused == [3.0] and slept == [3.0]


def test_request_json_gives_up(monkeypatch):
    monkeypatch.setattr(dlsite, "_session", lambda: type("S", (), {"get": lambda self, url, timeout: FakeResponse(500)})())
    monkeypatch.setattr(dlsite.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="Failed to fetch x"):
        dlsite._request_json("http://x", "x")


def test_run_parallel_collects_every_result_and_checkpoints():
    results, saves = [], []
    done = run_parallel(range(25), lambda n: n * 2, results.append, 4, "test", checkpoint=lambda: saves.append(1))
    assert done == 25
    assert sorted(results) == [n * 2 for n in range(25)]
    assert saves  # at least the final checkpoint


def test_run_parallel_limit_and_empty():
    results, saves = [], []
    assert run_parallel(range(50), lambda n: n, results.append, 3, "test", limit=7, checkpoint=lambda: saves.append(1)) == 7
    assert len(results) == 7
    assert run_parallel([], lambda n: n, results.append, 3, "test", checkpoint=lambda: saves.append(1)) == 0
    assert len(saves) == 1  # nothing completed, so no needless save


def test_run_parallel_error_still_checkpoints():
    saves = []

    def work(n):
        if n == 3:
            raise ValueError("boom")
        return n

    with pytest.raises(ValueError):
        run_parallel(range(10), work, lambda r: None, 2, "test", checkpoint=lambda: saves.append(1))


def catalogue():
    DL = DLsiteCatalog()
    DL.works_table = {
        "RJ01000001": {"name": "日本語", "options": ["JPN", "ENG", "CHI_HANT"]},
        "RJ01000002": {"name": "日本語2", "options": ["JPN", "CHI_HANS"]},
        "RJ01000003": {"name": "only Japanese", "options": ["JPN"]},
        "RJ01000004": {"name": "english original", "options": ["ENG"]},
    }
    return DL


def test_title_tasks_select_newest_first_and_missing_languages():
    DL = catalogue()
    assert [t[0] for t in DL.title_tasks()] == ["RJ01000002", "RJ01000001"]
    assert dict(DL.title_tasks(["ENG"])) == {"RJ01000001": ["ENG"]}

    DL.title_table = {"RJ01000001": {"ENG": "One"}}
    assert dict(DL.title_tasks()) == {"RJ01000001": ["CHI_HANT"], "RJ01000002": ["CHI_HANS"]}


def test_fetch_localized_titles_resumes_per_language(monkeypatch, tmp_path):
    DL = catalogue()
    calls = []

    def fake_request(url, label, limiter=None):
        locale = url.rsplit("locale=", 1)[1]
        calls.append((label, locale))
        # RJ01000002 has no distinct Traditional/Simplified title
        return [{"work_name": "日本語2" if label == "RJ01000002" else f"{label} {locale}"}]

    monkeypatch.setattr(dlsite, "_request_json", fake_request)
    assert DL.fetch_localized_titles(str(tmp_path), langs=["ENG"], workers=2) == 1
    assert DL.title_table == {"RJ01000001": {"ENG": "RJ01000001 en_US"}}

    assert DL.fetch_localized_titles(str(tmp_path), workers=2) == 2
    assert DL.title_table["RJ01000001"] == {"ENG": "RJ01000001 en_US", "CHI_HANT": "RJ01000001 zh_TW"}
    assert DL.title_table["RJ01000002"] == {"CHI_HANS": None}
    assert len(calls) == 3

    assert DL.fetch_localized_titles(str(tmp_path), workers=2) == 0
    saved = json.loads((tmp_path / "title_table.json").read_text(encoding="utf-8"))
    assert saved == DL.title_table


def test_fetch_localized_titles_limit(monkeypatch, tmp_path):
    DL = catalogue()
    monkeypatch.setattr(dlsite, "_request_json", lambda url, label, limiter=None: [{"work_name": label + "!"}])
    assert DL.fetch_localized_titles(str(tmp_path), limit=1, workers=2) == 1
    assert list(DL.title_table) == ["RJ01000002"]


def test_fetch_translations_scans_listings_and_looks_up_unknown_ids(monkeypatch, tmp_path):
    DL = catalogue()
    DL.translation_table = {"RJ09000003": {"lang": None}}
    listings = {
        ("ENG", 1): ["RJ09000001", "RJ01000001"],
        ("ENG", 2): ["RJ09000002", "RJ09000003"],
    }

    def fake_listing(lang, page, limiter=None):
        return listings.get((lang, page), []), 150 if lang == "ENG" else 0

    def fake_info(workno, lang, limiter=None):
        return {"lang": lang, "originalWorkno": "RJ01000001", "name": f"{workno} edition"}

    monkeypatch.setattr(DLsiteCatalog, "list_language_page", staticmethod(fake_listing))
    monkeypatch.setattr(DLsiteCatalog, "get_translation_info", staticmethod(fake_info))

    assert DL.fetch_translations(str(tmp_path), langs=["ENG"], workers=2) == 2
    # known works and cached negatives are not looked up again
    assert set(DL.translation_table) == {"RJ09000001", "RJ09000002", "RJ09000003"}
    assert DL.translation_table["RJ09000001"]["name"] == "RJ09000001 edition"
    assert (tmp_path / "translation_table.json").exists()

    assert DL.fetch_translations(str(tmp_path), langs=["ENG"], workers=2) == 0


def test_remove_translation_data(tmp_path):
    (tmp_path / "translation_table.json").write_text(
        json.dumps({"RJ1": {"lang": "ENG"}, "RJ2": {"lang": "CHI_HANT"}, "RJ3": {"lang": None}}), encoding="utf-8"
    )
    (tmp_path / "title_table.json").write_text(
        json.dumps({"RJ4": {"ENG": "a", "CHI_HANT": "b"}, "RJ5": {"ENG": None}}), encoding="utf-8"
    )

    assert remove_translation_data(str(tmp_path), ["ENG"], dry_run=True) == (1, 2)
    assert json.loads((tmp_path / "translation_table.json").read_text()).keys() == {"RJ1", "RJ2", "RJ3"}

    assert remove_translation_data(str(tmp_path), ["ENG"]) == (1, 2)
    assert json.loads((tmp_path / "translation_table.json").read_text()).keys() == {"RJ2", "RJ3"}
    assert json.loads((tmp_path / "title_table.json").read_text()) == {"RJ4": {"CHI_HANT": "b"}}


def test_remove_translation_data_without_tables(tmp_path):
    assert remove_translation_data(str(tmp_path), ["ENG"]) == (0, 0)


def test_parse_args_modes_and_languages():
    args = initial.parse_args(["-u"])
    assert args.update and args.languages is None and args.kinds == ["titles", "editions"]
    assert args.workers == 6 and not args.skip

    args = initial.parse_args(["-u", "EN", "tc", "-k", "titles", "-s"])
    assert args.languages == ["ENG", "CHI_HANT"] and args.kinds == ["titles"] and args.skip
    assert initial.parse_args(["-u", "en,sc"]).languages == ["ENG", "CHI_HANS"]

    assert initial.parse_args(["-u", "NONE"]).languages == []
    assert initial.parse_args(["-u", "JA"]).languages == []
    args = initial.parse_args(["-d", "2022-01-01", "2022-01-02", "JA"])
    assert args.languages == [] and args.date == ["2022-01-01", "2022-01-02"]
    args = initial.parse_args(["-d", "2022-01-01", "EN", "TC"])
    assert args.languages == ["ENG", "CHI_HANT"] and args.date == ["2022-01-01"] and not args.update
    assert initial.parse_args(["-d", "2022-01-01"]).languages is None
    assert initial.parse_args(["-c"]).check


def test_parse_args_remove():
    assert initial.parse_args(["-r"]).remove == [] and initial.parse_args(["-r"]).remove_targets is None
    assert initial.parse_args(["-r", "ALL"]).remove_targets == "ALL"
    assert initial.parse_args(["-r", "EN", "SC", "-s"]).remove_targets == ["ENG", "CHI_HANS"]


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["-t"],
        ["-c", "-u"],
        ["-r", "JA"],
        ["-r", "ALL", "EN"],
        ["-u", "FR"],
        ["-u", "NONE", "EN"],
        ["-d", "EN"],
        ["-l", "EN"],
        ["-r", "EN", "-k", "titles"],
        ["-u", "--workers", "0"],
        ["-s"],
    ],
)
def test_parse_args_rejects(argv, capsys):
    with pytest.raises(SystemExit) as exc:
        initial.parse_args(argv)
    assert exc.value.code == 2


class FakeStdin:
    def __init__(self, tty):
        self.tty = tty

    def isatty(self):
        return self.tty


def test_confirm_skip_and_no_terminal(monkeypatch):
    skip = initial.parse_args(["-u", "-s"])
    assert initial.confirm(skip, "Continue?") is True
    assert initial.ask_languages(skip) == []

    ask = initial.parse_args(["-u"])
    monkeypatch.setattr(initial.sys, "stdin", FakeStdin(False))
    with pytest.raises(SystemExit):
        initial.confirm(ask, "Continue?")
    with pytest.raises(SystemExit):
        initial.ask_languages(ask)


def test_confirm_answers(monkeypatch):
    args = initial.parse_args(["-u"])
    monkeypatch.setattr(initial.sys, "stdin", FakeStdin(True))
    for answer, default, expected in [("", True, True), ("", False, False), ("y", False, True), ("n", True, False)]:
        monkeypatch.setattr("builtins.input", lambda prompt, answer=answer: answer)
        assert initial.confirm(args, "Q?", default) is expected


def test_ask_languages_menu(monkeypatch):
    args = initial.parse_args(["-u"])
    monkeypatch.setattr(initial.sys, "stdin", FakeStdin(True))
    answers = iter(["9", "2 3", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert initial.ask_languages(args) == ["ENG", "CHI_HANT"]
    assert initial.ask_languages(args) == []  # empty answer is Japanese only


def test_throttle_backoff_doubles_without_retry_after():
    assert [dlsite._retry_after(FakeResponse(403), attempt) for attempt in (1, 2, 3)] == [30, 60, 120]
    assert dlsite._retry_after(FakeResponse(429, headers={"Retry-After": "7"}), 3) == 7


def test_rate_limiter_slows_down_once_per_refusal():
    limiter = RateLimiter(4)
    limiter.pause(0.01)
    limiter.pause(0.01)  # a second refusal during the same pause does not slow it down again
    assert limiter.interval == 0.5
    time.sleep(0.02)
    limiter.pause(0.01)
    assert limiter.interval == 1.0


from datetime import datetime  # noqa: E402


@pytest.mark.parametrize(
    ("last", "expected"),
    [
        ("2026-10-08", ("2026-10-08", "2026-10-10")),
        ("2026-10-10", ("2026-10-10", None)),  # updating again on the same day re-crawls yesterday
        ("2026-10-11", None),
    ],
)
def test_update_span(last, expected):
    today = datetime(2026, 10, 11, 15, 30)
    assert initial.update_span(datetime.strptime(last, "%Y-%m-%d"), today) == expected


def test_get_data_duration_allows_the_same_day(monkeypatch, capsys):
    DL = DLsiteCatalog()
    days = []
    monkeypatch.setattr(DLsiteCatalog, "get_data_one_day", lambda self, date: days.append(date))
    DL.get_data_duration("2026-10-10", "2026-10-10")
    DL.get_data_duration("2026-10-10", "2026-10-12")
    DL.get_data_duration("2026-10-11", "2026-10-10")
    assert days == ["2026-10-10", "2026-10-10", "2026-10-11", "2026-10-12"]
    assert "must not be earlier" in capsys.readouterr().out


@pytest.fixture()
def stopped(monkeypatch):
    rebuilt = []
    monkeypatch.setattr(initial, "needs_rebuild", lambda path: True)
    monkeypatch.setattr(initial, "rebuild_database", lambda DL, path: rebuilt.append(path))
    return rebuilt


def run_stop(argv):
    with pytest.raises(SystemExit) as exc:
        initial.stop_after_partial_run(None, initial.parse_args(argv), "stopped", 130)
    return exc.value.code


def test_stop_after_partial_run_offers_a_rebuild(monkeypatch, stopped):
    monkeypatch.setattr(initial.sys, "stdin", FakeStdin(True))
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    assert run_stop(["-u"]) == 130
    assert len(stopped) == 1


def test_stop_after_partial_run_declined_or_unattended(monkeypatch, stopped):
    monkeypatch.setattr(initial.sys, "stdin", FakeStdin(True))
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    run_stop(["-u"])
    monkeypatch.setattr(initial.sys, "stdin", FakeStdin(False))
    run_stop(["-u"])  # no terminal and no --skip: nobody to ask, so no rebuild
    run_stop(["-u", "--raw_only", "-s"])
    assert stopped == []


def test_stop_after_partial_run_skip_rebuilds_without_asking(monkeypatch, stopped):
    monkeypatch.setattr(initial.sys, "stdin", FakeStdin(False))
    assert run_stop(["-u", "-s"]) == 130
    assert len(stopped) == 1
