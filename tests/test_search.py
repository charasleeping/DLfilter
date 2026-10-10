import sqlite3

import pytest

from conftest import work as make_work, write_works_db
from module import search as search_module
from module.search import EDITION_COLUMNS, RESULT_COLUMNS


def search(client, **params):
    return client.get("/api/search", params=params)


def ids(data):
    return [work["index"] for work in data["results"]]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("RJ01000001", "RJ01000001"),
        ("RJ123456", "RJ123456"),
        ("rj01000001", "RJ01000001"),
        ("ｒｊ０１０００００１", "RJ01000001"),
        ("  RJ123456  ", "RJ123456"),
    ],
)
def test_rj_id_lookup(client, query, expected):
    data = search(client, q=query, ages="000").json()
    assert data["state"] == "success"
    assert ids(data)[0] == expected


def test_id_field_is_prefix_match(client):
    data = search(client, q="RJ010000", field="id", ages="000").json()
    assert data["total"] == 6
    assert search(client, q="magic", field="id", ages="000").json()["total"] == 0


def test_japanese_title_substring(client):
    assert ids(search(client, q="少女").json()) == ["RJ01000001"]


def test_artist_field(client):
    data = search(client, q="サークル", field="artist", ages="000").json()
    assert sorted(ids(data)) == ["RJ01000001", "RJ01000004"]


def test_title_field_ignores_circle(client):
    assert search(client, q="Bulk", field="title").json()["total"] == 0
    assert search(client, q="Bulk", field="artist").json()["total"] == 60
    assert search(client, q="Bulk", field="all").json()["total"] == 60


def test_width_and_case_are_ignored(client):
    assert ids(search(client, q="FULLWIDTH", ages="000").json()) == ["RJ01000004"]
    assert ids(search(client, q="ｍａｇｉｃ ｇｉｒｌ", ages="000").json()) == ["RJ01000002"]


@pytest.mark.parametrize("query", ["magic adventure", "magic　adventure", "adventure magic"])
def test_all_terms_must_match(client, query):
    assert ids(search(client, q=query, ages="000").json()) == ["RJ01000002"]


def test_ranking_exact_then_prefix_then_name(client):
    data = search(client, q="magic", ages="000").json()
    assert ids(data) == ["RJ01000005", "RJ01000002", "RJ01000004"]
    assert data["total"] == 3


@pytest.mark.parametrize(
    ("ages", "expected"),
    [
        ("100", ["RJ01000005"]),
        ("010", ["RJ01000004"]),
        ("001", ["RJ01000002"]),
        ("111", ["RJ01000005", "RJ01000002", "RJ01000004"]),
        ("000", ["RJ01000005", "RJ01000002", "RJ01000004"]),
    ],
)
def test_age_filter(client, ages, expected):
    assert ids(search(client, q="magic", ages=ages).json()) == expected


def test_age_defaults_to_all_ages_only(client):
    assert ids(search(client, q="magic").json()) == ["RJ01000005"]


def test_like_wildcards_are_literal(client):
    assert ids(search(client, q="%", ages="000").json()) == ["RJ01000003"]
    assert sorted(ids(search(client, q="_", ages="000").json())) == ["RJ01000003", "RJ01000006"]
    assert ids(search(client, q="100%", ages="000").json()) == ["RJ01000003"]
    assert search(client, q="\\", ages="000").json()["total"] == 0


@pytest.mark.parametrize("query", ["' OR 1=1 --", '"; DROP TABLE maniax; --', "') OR ('1'='1"])
def test_sql_injection_is_inert(client, query):
    data = search(client, q=query, ages="000").json()
    assert data["state"] == "success"
    assert data["total"] == 0
    assert search(client, q="magic", ages="000").json()["total"] == 3


def test_no_match(client):
    data = search(client, q="zzzz-nothing").json()
    assert data["total"] == 0
    assert data["results"] == []


def test_pagination_is_stable_and_complete(client):
    first = search(client, q="Filler").json()
    second = search(client, q="Filler", page=2).json()
    beyond = search(client, q="Filler", page=3).json()

    assert first["total"] == second["total"] == beyond["total"] == 60
    assert len(first["results"]) == 48
    assert len(second["results"]) == 12
    assert beyond["results"] == []

    names = [w["name"] for w in first["results"] + second["results"]]
    assert names == [f"Filler {i:02d}" for i in range(60)]
    assert search(client, q="Filler").json()["results"] == first["results"]


def test_custom_page_size(client):
    data = search(client, q="Filler", page=3, page_size=10).json()
    assert [w["name"] for w in data["results"]] == [f"Filler {i:02d}" for i in range(20, 30)]


def test_response_shape_and_formatting(client):
    data = search(client, q="  RJ01000006 ").json()
    assert {k: data[k] for k in ("state", "source", "query", "field", "page", "page_size", "total")} == {
        "state": "success",
        "source": "local",
        "query": "RJ01000006",
        "field": "all",
        "page": 1,
        "page_size": 48,
        "total": 1,
    }
    work = data["results"][0]
    assert set(work) == set(RESULT_COLUMNS) | set(EDITION_COLUMNS) | {"titleToggle"}
    assert work["titleToggle"] is False and work["lang"] is None
    assert work["name"] == "Under_score Story"
    assert work["tags"] == ["002"]
    assert work["options"] == ["JPN", "DLP"]
    assert work["registDate"] == "2023-05-05"


@pytest.mark.parametrize(
    ("params", "code"),
    [
        ({"q": ""}, "empty_query"),
        ({"q": "   "}, "empty_query"),
        ({"q": "　"}, "empty_query"),
        ({"q": "a" * 101}, "query_too_long"),
        ({"q": "magic", "field": "description"}, "invalid_field"),
        ({"q": "magic", "ages": "11"}, "invalid_ages"),
        ({"q": "magic", "ages": "12a"}, "invalid_ages"),
        ({"q": "magic", "page": 0}, "invalid_page"),
        ({"q": "magic", "page": 10_001}, "invalid_page"),
        ({"q": "magic", "page_size": 0}, "invalid_page_size"),
        ({"q": "magic", "page_size": 49}, "invalid_page_size"),
    ],
)
def test_validation(client, params, code):
    response = client.get("/api/search", params=params)
    assert response.status_code == 400
    assert response.json() == {"state": "error", "code": code, "message": response.json()["message"]}


def test_query_at_length_limit_is_accepted(client):
    assert search(client, q="a" * 100).status_code == 200


def test_database_error_is_generic(client, monkeypatch, tmp_path):
    import app

    monkeypatch.setattr(app, "database_path", tmp_path / "missing.sqlite")
    response = search(client, q="magic")
    assert response.status_code == 500
    assert response.json()["code"] == "database_error"
    assert "missing.sqlite" not in response.text


@pytest.fixture()
def translated_conn(tmp_path):
    works = [
        make_work("RJ01000010", "ふれあいミイちゃん", "ペンギン発電所", name_ENG="Interactive Mii", name_CHI_HANT="互動小咪"),
        make_work("RJ01000011", "[ENG Ver.] Genesis Mizuki", "Translators Unite", lang="ENG",
                  originalWorkno="RJ01000012", originalLang="JPN", originalName="創世記ミズキ"),
        make_work("RJ01000012", "創世記ミズキ", "サークルX"),
    ]
    write_works_db(tmp_path / "works.sqlite", works)
    conn = sqlite3.connect(tmp_path / "works.sqlite")
    yield conn
    conn.close()


def find(conn, query, field="all"):
    return search_module.search(conn, query, field, "000", 1, 10)[1]


def test_translated_title_matches_and_toggles(translated_conn):
    (work,) = find(translated_conn, "interactive mii")
    assert work["index"] == "RJ01000010"
    assert (work["name"], work["lang"]) == ("Interactive Mii", "ENG")
    assert (work["originalName"], work["originalLang"]) == ("ふれあいミイちゃん", "JPN")
    assert work["titleToggle"] is True
    assert not any(key.startswith("name_") for key in work)

    (work,) = find(translated_conn, "互動")
    assert (work["name"], work["lang"], work["titleToggle"]) == ("互動小咪", "CHI_HANT", True)


def test_original_language_match_has_no_toggle(translated_conn):
    for query, field in [("ふれあい", "all"), ("ペンギン", "all"), ("RJ01000010", "id"), ("ペンギン", "artist")]:
        (work,) = find(translated_conn, query, field)
        assert work["name"] == "ふれあいミイちゃん" and work["lang"] is None and work["titleToggle"] is False


def test_translated_title_ranks_and_respects_field(translated_conn):
    assert [w["index"] for w in find(translated_conn, "Interactive Mii", "title")] == ["RJ01000010"]
    assert find(translated_conn, "Interactive Mii", "artist") == []


def test_separate_edition_toggles_only_for_translated_query(translated_conn):
    (work,) = find(translated_conn, "genesis")
    assert (work["index"], work["lang"], work["titleToggle"]) == ("RJ01000011", "ENG", True)
    assert work["originalName"] == "創世記ミズキ"

    assert [w["index"] for w in find(translated_conn, "創世記")] == ["RJ01000012"]
