"""Combined filtering, scored pagination and all supported product identifiers."""
import numpy as np
import pytest
from conftest import work, write_works_db
from module.dlsite import GenreCatalog
from reference import search
from module.database import connect_readonly


def test_empty_search_browses_newest(client):
    for q in ('', '  ', '　'):
        d = client.get('/api/search', params={'q': q, 'ages': '000'}).json()
        assert d['state'] == 'success' and d['total'] > 0
        rows = d['results']
        assert rows == sorted(rows, key=lambda w: (-(int(w['registDate'].replace('-', ''))), w['index']))


def test_combined_filters_and_random_keywords(client):
    params = {'q': 'magic', 'ages': '111', 'categories': 'ICG', 'included_genres': '003', 'excluded_low_rate': True}
    d = client.get('/api/search', params=params).json()
    assert [w['index'] for w in d['results']] == ['RJ01000002']
    r = client.get('/api/random', params=params).json()
    assert [w['index'] for w in r['results']] == ['RJ01000002']
    assert not client.get('/api/search', params={**params, 'excluded_genres': '002'}).json()['results']


def test_scoring_filters_keywords_and_reference(client):
    d = client.get('/api/search', params={'q': 'magic', 'ages': '000', 'genres': '001+002', 'rj_id': 'rj01000005'}).json()
    assert d['total'] == 2
    assert {w['index'] for w in d['results']} == {'RJ01000002', 'RJ01000004'}
    assert [w['score'] for w in d['results']] == sorted([w['score'] for w in d['results']], reverse=True)


def test_all_genres_and_unlimited_scored_pagination(tmp_path):
    catalogue = GenreCatalog.__new__(GenreCatalog)
    catalogue.genre_catalogue = {f'{i:03}': {'count': 1} for i in range(1, 13)}
    catalogue.genre_embedding = {g: np.array([1., 0.]) for g in catalogue.genre_catalogue}
    catalogue.genre_embedding['012'] = np.array([0., 1.])
    rows = [work(f'BJ{i:08}', 'Example', 'Publisher', tags='#012#') for i in range(1, 251)]
    rows += [work('VJ000001', 'Tagless', 'Brand', tags=''), work('VJ000002', 'Unknown', 'Brand', tags='#999#')]
    path = tmp_path / 'works.sqlite'; write_works_db(path, rows)
    with connect_readonly(path) as conn:
        total, result = search.search(conn, '', 'all', '000', 6, 48, genres=list(catalogue.genre_catalogue), catalogue=catalogue)
        assert total == 250 and len(result) == 10
        assert result[0]['index'] == 'BJ00000241'
        assert result[0]['score'] > 0  # the twelfth selected genre contributes
        total, browse = search.search(conn, '', 'all', '000', 1, 48)
        assert total == 252
        total, tagless = search.search(conn, 'Tagless', 'all', '000', 1, 48)
        assert total == 1 and tagless[0]['tags'] == []


@pytest.mark.parametrize('product', ['BJ123456', 'VJ01234567', 'ｂｊ１２３４５６'])
def test_lookup_accepts_product_prefixes(client, product):
    r = client.get('/api/works', params={'rj_id': product})
    assert r.status_code == 200
    assert list(r.json()['works'])[0] in ('BJ123456', 'VJ01234567')


def test_presets_accept_all_genres_and_normalize_product(client):
    p = {'q': 'book', 'field': 'title', 'rj_id': 'ｖｊ０１２３４５６７', 'genres': [f'{i:03}' for i in range(403)]}
    assert client.put('/api/presets/Unified', json=p).status_code == 200
    d = client.get('/api/presets/Unified').json()['preset']
    assert d['rj_id'] == 'VJ01234567' and len(d['genres']) == 403
    assert d['q'] == 'book' and d['field'] == 'title'


def test_rejects_bad_ids_filters_and_dates(client):
    assert client.get('/api/works', params={'rj_id': 'XX123456'}).status_code == 422
    for params in ({'genres': '999'}, {'since': '2026-02-30'}, {'included_genres': '001', 'excluded_genres': '001'}):
        assert client.get('/api/search', params=params).status_code in (400, 422)


def test_bj_vj_search_ranking_and_lookup(client, tmp_path, monkeypatch):
    from reference import python_app as app
    path = tmp_path / 'prefixes.sqlite'
    write_works_db(path, [work('BJ123456', 'Book', 'Publisher', siteId='books'),
                          work('BJ123457', 'BJ123456 is mentioned', 'Publisher', siteId='books'),
                          work('VJ01234567', 'Game', 'Brand', siteId='soft')])
    monkeypatch.setattr(app, 'database_path', path)
    for query, expected in [('ｂｊ１２３４５６', 'BJ123456'), ('vj01234567', 'VJ01234567')]:
        data = client.get('/api/search', params={'q': query}).json()
        assert data['results'][0]['index'] == expected
        assert client.get('/api/works', params={'rj_id': query}).json()['works'][expected]['name']
    assert client.get('/api/search', params={'q': 'BJ12345', 'field': 'id'}).json()['total'] == 2
