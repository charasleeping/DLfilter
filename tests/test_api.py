from conftest import DATA_DIR, WORKS


def test_root_and_static(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/script.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_works_from_another_directory(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert client.get("/").status_code == 200
    assert client.get("/static/template.js").status_code == 200
    assert client.get("/api/info").json()["length"] == len(WORKS)


def test_app_uses_fixture_data():
    from module import config

    assert config.DATA_DIR == DATA_DIR.resolve()


def test_info(client):
    data = client.get("/api/info").json()
    assert data["state"] == "success"
    assert data["length"] == len(WORKS)
    assert len(data["time"]) == 19


def test_locale(client):
    data = client.get("/api/locale/ja_JP").json()
    assert data["state"] == "success"
    assert data["locale"]["genres"]["001"]["name"] == "Genre 001 ja_JP"
    assert data["locale"]["work_formats"]["MNG"]["name"] == "Manga"


def test_locale_falls_back_to_english(client):
    data = client.get("/api/locale/xx_XX").json()
    assert data["locale"]["genres"]["001"]["name"] == "Genre 001 en_US"


def test_works_known_id(client):
    data = client.get("/api/works", params={"rj_id": "RJ01000001"}).json()
    assert data["state"] == "success"
    work = data["works"]["RJ01000001"]
    assert work["name"] == "魔法少女の冒険"
    assert work["tags"] == ["001", "002"]
    assert work["options"] == ["JPN", "DLP"]
    assert work["registDate"] == "2024-01-01"


def test_works_missing_id_keeps_empty_mapping(client):
    data = client.get("/api/works", params={"rj_id": ["RJ123456", "RJ99999999"]}).json()
    assert data["state"] == "success"
    assert data["works"]["RJ99999999"] == {}
    assert data["works"]["RJ123456"]["name"] == "Old Classic"
    assert data["missing"] == ["RJ99999999"]


def test_works_missing_is_empty_when_all_found(client):
    data = client.get("/api/works", params={"rj_id": ["RJ01000001", "RJ123456"]}).json()
    assert data["missing"] == []


def test_works_rejects_bad_format(client):
    assert client.get("/api/works", params={"rj_id": "RJ12"}).status_code == 422


def test_works_limit(client):
    ids = [f"RJ{i:08d}" for i in range(51)]
    assert client.get("/api/works", params={"rj_id": ids}).json()["state"] == "error"


def test_similarity_shape(client):
    data = client.post("/api/similarity", json={"genres": "001+002", "ages": "111"}).json()
    assert data["state"] == "success"
    assert set(data) == {"state", "result", "info"}
    assert set(data["info"]) == {"length", "time"}
    ids = [item[0] for item in data["result"]]
    scores = [item[1] for item in data["result"]]
    assert scores == sorted(scores, reverse=True)
    assert "RJ01000001" in ids


def test_similarity_filters(client):
    data = client.post(
        "/api/similarity",
        json={"genres": "001", "ages": "100", "rj_id": "RJ01000005", "dlcount": 80, "categories": "MNG"},
    ).json()
    ids = [item[0] for item in data["result"]]
    assert "RJ01000005" not in ids
    assert "RJ01000002" not in ids  # R18
    assert "RJ01000003" not in ids  # SOU


def test_similarity_invalid_genre(client):
    assert client.post("/api/similarity", json={"genres": "999"}).json()["state"] == "error"
    assert client.post("/api/similarity", json={"genres": "1"}).status_code == 422


def test_index_versions_static_assets(client):
    html = client.get("/").text
    for name in ["localisation.js", "template.js", "script.js", "style.css"]:
        assert f"/static/{name}?v=" in html
