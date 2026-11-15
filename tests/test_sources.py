import json
import sqlite3
from pathlib import Path
import pytest
import initial
from module import dlsite, catalogue_store
from module.dlsite import DLsiteCatalog, GenreCatalog
from module.database import connect_readonly


def test_legacy_dates_only_seed_maniax(tmp_path):
    (tmp_path / 'works_table.json').write_text('{}')
    (tmp_path / 'dates_table.json').write_text(json.dumps({'2024-01-01': '2024-01-02'}))
    c = DLsiteCatalog(str(tmp_path))
    assert c.source_dates == {'maniax': {'2024-01-01': '2024-01-02'}}
    assert 'books' not in c.source_dates


def test_checkpoint_replays_records_and_source_progress(tmp_path, monkeypatch):
    c = DLsiteCatalog(str(tmp_path))
    monkeypatch.setattr(c, 'get_outline', lambda date, source: [{'id': 'BJ123456', 'name': source}])
    c.get_data_one_day('2024-01-01', 'books')
    # No aggregate JSON save: a new process still sees this day's records and progress.
    restarted = DLsiteCatalog(str(tmp_path))
    assert restarted.works_table['BJ123456']['siteId'] == 'books'
    assert '2024-01-01' in restarted.source_dates['books']
    assert restarted.dates_table == {}
    restarted.get_outline = lambda date, source: [{'id': 'BJ123456', 'name': 'updated'}]
    restarted.get_data_one_day('2024-01-02', 'books')
    assert len(DLsiteCatalog(str(tmp_path)).works_table) == 1


def test_failed_checkpoint_does_not_advance_day(tmp_path, monkeypatch):
    c = DLsiteCatalog(str(tmp_path))
    monkeypatch.setattr(c, 'get_outline', lambda date, source: [{'id': 'VJ123456', 'bad': object()}])
    with pytest.raises(TypeError):
        c.get_data_one_day('2024-01-01', 'pro')
    assert not c.works_table and not c.source_dates.get('pro')
    assert not DLsiteCatalog(str(tmp_path)).source_dates.get('pro')


def test_update_does_not_backfill_uninitialized_sources(tmp_path, monkeypatch, capsys):
    c = DLsiteCatalog(str(tmp_path)); c.save_tables(str(tmp_path))
    monkeypatch.setattr(initial, 'needs_rebuild', lambda p: False)
    initial.main(['-u', 'NONE', '-s', '--path', str(tmp_path)])
    out = capsys.readouterr().out
    assert 'books: not collected' in out and '--sources books' in out
    assert not (tmp_path / catalogue_store.CHECKPOINT_FILE).exists()


def test_rebuild_normalizes_new_sources_and_keeps_tagless(tmp_path):
    (tmp_path / 'genre_table.json').write_text(json.dumps({'001': {'count': 1}}))
    (tmp_path / 'workformat.json').write_text('{}')
    import pickle
    (tmp_path / 'genre_vec.pkl').write_bytes(pickle.dumps({}))
    c = DLsiteCatalog()
    c.works_table = {'BJ123456': {'name': 'Book', 'type': {'id': 'WBT'}, 'siteId': 'books',
                                'tags': None, 'img': {'resizeUrl': '//img.dlsite.jp/book.jpg'}},
                     'VJ123456': {'name': 'Game', 'tags': [{'id': 1}], 'rate': {'averageStar': 45, 'count': 1}}}
    initial.rebuild_database(c, str(tmp_path))
    with connect_readonly(tmp_path / 'works.sqlite') as conn:
        assert conn.execute('SELECT COUNT(*) FROM maniax').fetchone()[0] == 2
        assert conn.execute('SELECT imageUrl, tags, type FROM maniax WHERE [index]="BJ123456"').fetchone() == ('https://img.dlsite.jp/book.jpg', '##', 'WBT')
        assert conn.execute('SELECT siteId FROM maniax WHERE [index]="VJ123456"').fetchone()[0] == 'pro'


def test_cli_sources_and_invalid_selection():
    assert initial.parse_args(['-u', 'NONE', '--sources', 'books', 'soft']).sources == ['books', 'soft']
    with pytest.raises(SystemExit): initial.parse_args(['-u', '--sources', 'comic'])


def test_installer_accepts_progress_and_translation_files(tmp_path):
    from module.fetch_database import REQUIRED_FILES, OPTIONAL_FILES, install_archive
    import zipfile
    archive = tmp_path / 'data.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name in REQUIRED_FILES + OPTIONAL_FILES: z.writestr(name, b'data')
    names = install_archive(archive, tmp_path / 'data')
    assert set(names) == set(REQUIRED_FILES + OPTIONAL_FILES)


def test_new_source_translation_routes(monkeypatch, tmp_path):
    c = DLsiteCatalog(); c.sources = ('soft',)
    c.works_table = {'VJ123456': {'name': 'Original', 'options': ['JPN', 'ENG'], 'siteId': 'soft'}}
    calls = []
    monkeypatch.setattr(dlsite, '_request_json', lambda url, *args: calls.append(url) or [{'work_name': 'Title'}])
    assert c.fetch_localized_titles(str(tmp_path), langs=['ENG']) == 1
    assert '/soft/api/' in calls[0]
    monkeypatch.setattr(DLsiteCatalog, 'list_language_page', staticmethod(lambda lang, page, limiter, source: (['VJ123457'], 1)))
    monkeypatch.setattr(DLsiteCatalog, 'get_translation_info', staticmethod(lambda workno, lang, limiter, source: {'lang': lang, 'siteId': source}))
    assert c.fetch_translations(str(tmp_path), langs=['ENG']) == 1
    assert c.translation_table['VJ123457']['siteId'] == 'soft'


def test_genre_and_format_catalogues_merge(monkeypatch, tmp_path):
    class FakeGenre:
        def __init__(self, target):
            self.genre_catalogue = {'001': {'count': 1, 'name': {'ja_JP': 'Tag'}, 'category': {'ja_JP': 'Tags'}}}
            self.workformat = {('WBT' if target == 'books' else 'ADV'): {'name': {'ja_JP': target}, 'category': {'en_US': 'Game'}}}
        concat_genre = staticmethod(GenreCatalog.concat_genre)
        def get_embedding(self, **kwargs): pass
        def save_data(self, path):
            assert set(self.workformat) == {'WBT', 'ADV'}
            assert self.genre_catalogue['001']['count'] == 6  # base, home, girls-pro, books, pro, soft
    monkeypatch.setattr(initial, 'GenreCatalog', FakeGenre)
    args = initial.parse_args(['-u', 'NONE', '--path', str(tmp_path)])
    initial.update_genres(args)


def test_edition_export_does_not_reuse_original_thumbnail():
    import pandas as pd
    from module.database import add_localized_titles, add_translation_editions
    df = pd.DataFrame([{'index': 'BJ123456', 'name': 'Original', 'maker': 'Publisher', 'makerId': 'BG1',
                        'siteId': 'books', 'options': '#JPN#', 'registDate': pd.Timestamp('2024-01-01'),
                        'imageUrl': 'https://img.dlsite.jp/original.jpg'}]).set_index('index')
    df = add_localized_titles(df, {'BJ123456': {'ENG': 'Title'}})
    df = add_translation_editions(df, {'BJ123457': {'lang': 'ENG', 'originalWorkno': 'BJ123456', 'originalLang': 'JPN', 'name': 'Edition'}})
    assert df.loc['BJ123457', 'imageUrl'] is None
    assert df.loc['BJ123457', 'name_ENG'] is None
    assert df.loc['BJ123457', 'originalName'] == 'Original'


def test_locale_keeps_genres_with_missing_translations(client, monkeypatch):
    from reference import python_app as app
    monkeypatch.setitem(app.GG.genre_catalogue, '998', {'name': {'ja_JP': '日本語'}, 'category': {'ja_JP': '分類'}, 'count': 1})
    data = client.get('/api/locale/zh_TW').json()['locale']
    assert data['genres']['998']['name'] == '日本語'


def test_rj_title_lookup_uses_actual_home_site(monkeypatch, tmp_path):
    c = DLsiteCatalog()
    c.works_table = {'RJ123456': {'name': 'Title', 'siteId': 'home', 'options': ['JPN', 'ENG']}}
    urls = []
    monkeypatch.setattr(dlsite, '_request_json', lambda url, *args: urls.append(url) or [{'work_name': 'Localized'}])
    assert c.fetch_localized_titles(str(tmp_path), langs=['ENG']) == 1
    assert '/home/api/' in urls[0]
