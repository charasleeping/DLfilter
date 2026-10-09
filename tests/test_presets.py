import json

from conftest import PRESETS_DIR, WORKS

PRESET = {
    "rj_id": "RJ01000001",
    "genres": ["001", "002"],
    "included_genres": ["003"],
    "excluded_genres": [],
    "categories": ["MNG", "ICG"],
    "popularity_weight": {"enabled": True, "value": 2},
    "release_date": {"enabled": False, "value": 40},
    "download_count": {"enabled": True, "value": 80},
    "ages": [True, False, True],
    "excluded_contents": [True, False, True, False, True],
    "advanced_options_open": True,
}


def test_random_works(client):
    data = client.get("/api/random", params={"ages": "111", "count": 5}).json()
    assert data["state"] == "success"
    ids = [work["index"] for work in data["results"]]
    assert len(ids) == len(set(ids)) == 5
    assert set(ids) <= {work["index"] for work in WORKS}
    assert isinstance(data["results"][0]["tags"], list)


def test_random_works_respects_ages(client):
    data = client.get("/api/random", params={"ages": "001", "count": 48}).json()
    assert [work["index"] for work in data["results"]] == ["RJ01000002"]


def random_ids(client, **params):
    data = client.get("/api/random", params={"ages": "111", "count": 48, **params}).json()
    assert data["state"] == "success"
    return {work["index"] for work in data["results"]}


def test_random_works_filters(client):
    assert random_ids(client, categories="SOU") == {"RJ01000003"}
    assert random_ids(client, categories="ICG+SOU") == {"RJ01000002", "RJ01000003"}
    assert random_ids(client, included_genres="003") == {"RJ01000002", "RJ01000003"}
    assert random_ids(client, included_genres="002+003") == {"RJ01000002"}
    assert "RJ01000002" not in random_ids(client, excluded_genres="003")
    assert random_ids(client, since="2024-01-01", categories="SOU") == {"RJ01000003"}
    assert "RJ123456" not in random_ids(client, since="2020-01-01")
    assert "RJ123456" in random_ids(client, included_genres="004", excluded_genres="003")
    assert random_ids(client, excluded_low_rate="true", excluded_options="AIG+GRO")  # no test work is excluded


def test_random_works_filter_validation(client):
    for params in [{"categories": "mng"}, {"included_genres": "1"}, {"since": "2024"}, {"excluded_options": "XXX"}]:
        assert client.get("/api/random", params=params).status_code == 422, params


def test_random_works_validation(client):
    assert client.get("/api/random", params={"ages": "12"}).status_code == 400
    assert client.get("/api/random", params={"count": 49}).status_code == 400


def test_preset_round_trip(client):
    assert client.put("/api/presets/My preset_1", json=PRESET).json() == {"state": "success", "name": "My preset_1"}
    assert json.loads((PRESETS_DIR / "My preset_1.json").read_text(encoding="utf-8")) == PRESET

    listing = client.get("/api/presets").json()
    assert listing["folder"] == "presets"
    assert "My preset_1" in [preset["name"] for preset in listing["presets"]]

    data = client.get("/api/presets/My preset_1").json()
    assert data["preset"] == PRESET


def test_preset_overwrite_and_unicode_name(client):
    client.put("/api/presets/お気に入り", json=PRESET)
    client.put("/api/presets/お気に入り", json={**PRESET, "genres": ["004"]})
    assert client.get("/api/presets/お気に入り").json()["preset"]["genres"] == ["004"]


def test_preset_defaults_fill_missing_fields(client):
    client.put("/api/presets/minimal", json={"genres": ["001"]})
    preset = client.get("/api/presets/minimal").json()["preset"]
    assert preset["release_date"] == {"enabled": False, "value": 5}
    assert preset["ages"] == [False, False, True]


def test_preset_rejects_bad_names(client):
    for name in ["..", ".hidden", "a.b", " padded", "x" * 61]:
        assert client.put(f"/api/presets/{name}", json=PRESET).status_code in (400, 404), name
        assert client.get(f"/api/presets/{name}").status_code in (400, 404), name
    assert not any(PRESETS_DIR.parent.glob("*.json"))


def test_preset_rejects_bad_content(client):
    assert client.put("/api/presets/bad", json={**PRESET, "genres": ["1; DROP"]}).status_code == 422
    assert client.put("/api/presets/bad", json={**PRESET, "extra": 1}).status_code == 422
    assert client.put("/api/presets/bad", json={**PRESET, "ages": [True]}).status_code == 422
    assert not (PRESETS_DIR / "bad.json").exists()


def test_preset_missing_and_corrupt(client):
    assert client.get("/api/presets/nothing-here").status_code == 404
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    (PRESETS_DIR / "corrupt.json").write_text("{not json", encoding="utf-8")
    assert client.get("/api/presets/corrupt").status_code == 422
