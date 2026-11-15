"""Compare the native HTTP implementation to the independent Python oracle."""
import json
import os
import socket
import subprocess
import time
from pathlib import Path

import numpy as np
import pytest
import requests
from conftest import DATA_DIR, build_data_dir

BINARY = Path(__file__).resolve().parent.parent / ('target/release/dlfilter.exe' if os.name == 'nt' else 'target/release/dlfilter')


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    if not BINARY.exists():
        pytest.fail('Build the native server with cargo build --release before running contracts')
    folder = tmp_path_factory.mktemp('native')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    env = dict(os.environ, DLFILTER_DATA_DIR=str(DATA_DIR), DLFILTER_CACHE_DIR=str(folder/'cache'),
               DLFILTER_PRESETS_DIR=str(folder/'presets'), DLFILTER_PORT=str(port), DLFILTER_HOST='127.0.0.1')
    log = (folder/'server.log').open('w+')
    server = subprocess.Popen([str(BINARY), 'serve'], env=env, cwd=folder, stdout=log, stderr=log)
    session = requests.Session(); session.trust_env = False
    base = f'http://127.0.0.1:{port}'
    try:
        for _ in range(200):
            if server.poll() is not None:
                log.seek(0); pytest.fail(log.read())
            try:
                if session.get(base+'/api/info', timeout=.2).status_code == 200: break
            except requests.RequestException: pass
            time.sleep(.05)
        else: pytest.fail('Native server did not become ready')
        yield lambda route, **kwargs: session.request(kwargs.pop('method','GET'),base+route,timeout=10,**kwargs)
    finally:
        server.terminate(); server.wait(timeout=10); session.close(); log.close()


@pytest.mark.parametrize('params', [
    {}, {'q':'少女'}, {'q':'magic','ages':'000'}, {'q':'ｍａｇｉｃ ｇｉｒｌ','ages':'111'},
    {'q':'RJ01000001'}, {'q':'ｒｊ０１０００００１'}, {'q':'RJ010000','field':'id','ages':'000'},
    {'q':'サークル','field':'artist','ages':'000'}, {'q':'%','ages':'000'}, {'q':'_','ages':'000'},
    {'q':'"; DROP TABLE maniax; --'}, {'q':'Filler','page':2}, {'q':'Filler','page':3},
    {'q':'magic','ages':'000','genres':'001+002'}, {'genres':'001','ages':'000','rj_id':'RJ01000005'},
    {'included_genres':'003','ages':'111'}, {'excluded_genres':'003','ages':'111'},
    {'categories':'SOU','excluded_low_rate':True}, {'since':'2024-01-01','ages':'000'},
    {'q':'magic','field':'title','ages':'000','genres':'001+002','weight_func':3,'dlcount':80},
])
def test_search_parity(native, client, params):
    expected = client.get('/api/search',params=params)
    actual = native('/api/search',params=params)
    assert actual.status_code == expected.status_code, actual.text
    a,b=actual.json(),expected.json()
    assert a['total']==b['total']
    assert [w['index'] for w in a['results']]==[w['index'] for w in b['results']]
    for x,y in zip(a['results'],b['results']):
        if 'score' in x:
            assert x.pop('score') == pytest.approx(y.pop('score'), abs=1e-5)
        assert x==y


@pytest.mark.parametrize('params', [{'q':'magic','ages':'11'},{'q':'x','field':'bad'}, {'page':0}, {'page_size':49}, {'count':0}, {'genres':'999'}, {'since':'2026-02-30'}, {'included_genres':'001','excluded_genres':'001'}])
def test_validation_parity(native,client,params):
    a=native('/api/search',params=params); b=client.get('/api/search',params=params)
    assert a.status_code==b.status_code
    assert a.json()['state']=='error'


def test_locale_works_and_html(native,client):
    for locale in ('en_US','ja_JP','zh_TW','zh_CN','unknown'):
        assert native('/api/locale/'+locale).json()==client.get('/api/locale/'+locale).json()
    params=[('rj_id','ｒｊ０１０００００１'),('rj_id','BJ123456'),('rj_id','VJ01234567')]
    assert native('/api/works',params=params).json()==client.get('/api/works',params=params).json()
    html=native('/').text
    assert '{{ asset_url' not in html and '/static/script.js?v=' in html
    assert native('/static/script.js').status_code==200
    assert native('/api/info').json()['length']==client.get('/api/info').json()['length']


@pytest.mark.parametrize('mode', [1,2,3,4])
@pytest.mark.parametrize('downloads',[0,50,100])
def test_legacy_similarity(native,client,mode,downloads):
    query={'genres':'001+002','ages':'000','weight_func':mode,'dlcount':downloads}
    a=native('/api/similarity',method='POST',json=query).json();b=client.post('/api/similarity',json=query).json()
    assert a['info']['length']==b['info']['length']
    native_scores=dict(a['result']); reference_scores=dict(b['result'])
    assert native_scores.keys()==reference_scores.keys()
    # Float32 BLAS kernels may reorder near ties, especially the final matrix rows.
    # Compare scores by ID, and require every meaningful ordering to agree.
    for work_id,score in native_scores.items():
        assert score==pytest.approx(reference_scores[work_id],abs=1e-5)
    for i,(work_id,score) in enumerate(a['result']):
        for other_id,other_score in a['result'][i+1:]:
            assert reference_scores[work_id]>=reference_scores[other_id]-1e-5
            if score==other_score:
                assert work_id<other_id


def test_random_and_presets(native):
    data=native('/api/random',params={'q':'Filler','ages':'000','count':5}).json()
    ids=[w['index'] for w in data['results']]
    assert len(ids)==len(set(ids))==5
    assert all(w['name'].startswith('Filler') for w in data['results'])
    p={'q':'hello','genres':['001'],'rj_id':'ｂｊ１２３４５６'}
    assert native('/api/presets/Test',method='PUT',json=p).status_code==200
    saved=native('/api/presets/Test').json()['preset']
    assert saved['q']=='hello' and saved['rj_id']=='BJ123456'
    assert any(p['name']=='Test' for p in native('/api/presets').json()['presets'])
    for name in ('..','.hidden','a.b','x'*61):
        assert native('/api/presets/'+name,method='PUT',json=p).status_code in (400,404)
    assert native('/api/presets/Bad',method='PUT',json={'unknown':True}).status_code==422
    assert native('/api/presets/Missing').status_code==404


def test_vectors_and_preparation_recovery(tmp_path):
    build_data_dir(tmp_path)
    env=dict(os.environ,DLFILTER_DATA_DIR=str(tmp_path),DLFILTER_CACHE_DIR=str(tmp_path/'cache'))
    def prepare():return subprocess.run([str(BINARY),'prepare'],env=env,capture_output=True,text=True)
    assert prepare().returncode==0
    (tmp_path/'cache/search.bin').write_bytes(b'corrupt')
    assert prepare().returncode==0
    manifest=json.loads((tmp_path/'cache/cache.json').read_text())
    before=manifest['fingerprint']
    genre=json.loads((tmp_path/'genre_table.json').read_text());genre['001']['count']+=1
    (tmp_path/'genre_table.json').write_text(json.dumps(genre))
    assert prepare().returncode==0
    assert json.loads((tmp_path/'cache/cache.json').read_text())['fingerprint']!=before
    (tmp_path/'genre_vectors.f32').write_bytes(b'invalid')
    failed=prepare();assert failed.returncode!=0 and 'checksum or length' in failed.stderr


def test_concurrent_native_queries(native):
    from concurrent.futures import ThreadPoolExecutor
    params={'q':'Filler','genres':'001','ages':'000'}
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _: native('/api/search',params=params).json(),range(16)))
    assert all(data==results[0] for data in results)


def test_native_uses_read_only_data(tmp_path):
    data=tmp_path/'data';data.mkdir();build_data_dir(data)
    files=list(data.iterdir())
    for file in files: file.chmod(0o444)
    data.chmod(0o555)
    try:
        env=dict(os.environ,DLFILTER_DATA_DIR=str(data),DLFILTER_CACHE_DIR=str(tmp_path/'writable-cache'))
        result=subprocess.run([str(BINARY),'prepare'],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert sorted(p.name for p in data.iterdir())==sorted(p.name for p in files)
    finally:
        data.chmod(0o755)
        for file in files:file.chmod(0o644)
