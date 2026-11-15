"""Browser setup API uses disposable data, no releases or live catalogue changes."""
import hashlib
import http.server
import functools
import threading
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import zipfile

import pytest
import requests
from conftest import DATA_DIR

BINARY = Path(__file__).resolve().parents[1] / ('target/release/dlfilter.exe' if os.name == 'nt' else 'target/release/dlfilter')
FILES = ('works.sqlite','genre_table.json','workformat.json','genre_vectors.json','genre_vectors.f32')


def wait_for(read, predicate=lambda value: value, timeout=20):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        value=read()
        if predicate(value): return value
        time.sleep(.05)
    pytest.fail(f'Timed out: {value}')


@pytest.fixture
def setup_server(tmp_path):
    root=tmp_path/'app';root.mkdir();(root/'scripts').mkdir()
    # A bounded offline helper exercises exactly the packaged JSON-lines protocol.
    (root/'scripts/title_helper.py').write_text('import sys,json,time\nfor line in sys.stdin:\n t=json.loads(line); time.sleep(.1); print(json.dumps({"title":"Supplemental sunshine title"}),flush=True)\n')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/slow.zip':
                self.send_response(200);self.send_header('Content-Length',str(10*1024*1024));self.end_headers()
                try:
                    for _ in range(1280): self.wfile.write(b'x'*8192);self.wfile.flush();time.sleep(.02)
                except (BrokenPipeError,ConnectionResetError): pass
            else: super().do_GET()
    handler=functools.partial(Handler,directory=str(tmp_path))
    web=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=web.serve_forever,daemon=True).start()
    (root/'manifest-base.txt').write_text(f'http://127.0.0.1:{web.server_port}')
    env=dict(os.environ,DLFILTER_DB_MANIFEST_URL=f'http://127.0.0.1:{web.server_port}/manifest.json',DLFILTER_ROOT=str(root),DLFILTER_DATA_DIR=str(root/'data'),DLFILTER_CACHE_DIR=str(root/'cache'),DLFILTER_PRESETS_DIR=str(root/'presets'),DLFILTER_PORT=str(port),DLFILTER_HOST='127.0.0.1',DLFILTER_TITLE_PYTHON=sys.executable)
    log=(tmp_path/'server.log').open('w+')
    server=subprocess.Popen([str(BINARY),'serve'],env=env,stdout=log,stderr=log)
    session=requests.Session();session.trust_env=False
    base=f'http://127.0.0.1:{port}'
    def request(path,**kwargs): return session.request(kwargs.pop('method','GET'),base+path,timeout=30,**kwargs)
    try:
        for _ in range(200):
            if server.poll() is not None:
                log.seek(0);pytest.fail(log.read())
            try:
                if request('/api/setup/status').ok: break
            except requests.RequestException: pass
            time.sleep(.05)
        else: pytest.fail('Setup server failed to start')
        token=request('/api/setup/status').json()['token']
        def restart():
            nonlocal server
            server.terminate();server.wait(timeout=10)
            server=subprocess.Popen([str(BINARY),'serve'],env=env,stdout=log,stderr=log)
            for _ in range(200):
                try:
                    if request('/api/setup/status').json()['ready']: return
                except requests.RequestException: pass
                time.sleep(.05)
            pytest.fail('Restart failed')
        request.restart=restart
        yield request, {'x-dlfilter-token':token}, root
    finally:
        server.terminate();server.wait(timeout=10);log.close();session.close();web.shutdown();web.server_close()


def archive(tmp_path,modify=None):
    data=tmp_path/'bundle';data.mkdir(exist_ok=True)
    for name in FILES: shutil.copyfile(DATA_DIR/name,data/name)
    if modify: modify(data)
    path=tmp_path/'catalogue.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name in FILES:z.write(data/name,name)
    return path


def install(request,headers,path):
    with path.open('rb') as f:
        response=request('/api/setup/import',method='POST',headers=headers,files={'catalogue':('catalogue.zip',f,'application/zip')})
    assert response.status_code==202,response.text
    return wait_for(lambda:request('/api/setup/status').json(),lambda s:s['ready'] or s['installation']['state']=='error')


def test_clean_setup_security_import_and_repeat(setup_server,tmp_path):
    request,headers,root=setup_server
    assert request('/').url.endswith('/setup')
    assert not request('/api/setup/status').json()['ready']
    assert request('/api/setup/download',method='POST').status_code==403
    assert request('/api/setup/download',method='POST',headers={**headers,'Origin':'https://attacker.invalid'}).status_code==403
    assert request('/api/setup/status',headers={'Host':'attacker.invalid'}).status_code==403
    bundle=archive(tmp_path)
    assert install(request,headers,bundle)['ready']
    assert request('/api/search',params={'q':'magic','ages':'000'}).json()['total']>0
    assert request('/api/setup/download',method='POST',headers=headers).status_code==409
    assert sorted(p.name for p in (root/'data').iterdir())==sorted(FILES)


@pytest.mark.parametrize('bad',['legacy','traversal','corrupt','duplicate','symlink'])
def test_bad_import_preserves_data(setup_server,tmp_path,bad):
    request,headers,root=setup_server
    (root/'data').mkdir();(root/'data/keep.txt').write_text('preserve')
    path=tmp_path/'bad.zip'
    with zipfile.ZipFile(path,'w') as z:
        if bad=='traversal':z.writestr('../works.sqlite',b'not sqlite')
        elif bad=='duplicate':z.writestr('works.sqlite',b'a');z.writestr('nested/works.sqlite',b'b')
        elif bad=='symlink':
            entry=zipfile.ZipInfo('works.sqlite');entry.create_system=3;entry.external_attr=0o120777<<16;z.writestr(entry,'/tmp/elsewhere')
        elif bad=='corrupt':
            for name in FILES:z.writestr(name,b'not valid')
        else:z.writestr('genre_vec.pkl',b'never unpickle')
    result=install(request,headers,path)
    assert result['installation']['state']=='error'
    assert (root/'data/keep.txt').read_text()=='preserve'
    assert not (root/'works.sqlite').exists()


def test_background_titles_searchable_without_restart(setup_server,tmp_path):
    request,headers,root=setup_server
    def multilingual(data):
        with sqlite3.connect(data/'works.sqlite') as db:
            db.execute("UPDATE maniax SET options='#JPN#ENG#' WHERE [index]='RJ01000001'")
    assert install(request,headers,archive(tmp_path,multilingual))['ready']
    assert request('/api/search',params={'q':'Supplemental sunshine','ages':'000'}).json()['total']==0
    r=request('/api/setup/titles',method='POST',headers=headers,json={'languages':['ENG'],'enabled':True})
    assert r.ok,r.text
    final=wait_for(lambda:request('/api/setup/status').json(),lambda s:s['titles']['state'] in ('complete','error'))
    assert final['titles']['state']=='complete',final
    assert final['titles']['added']==1
    result=request('/api/search',params={'q':'Supplemental sunshine','ages':'000'}).json()
    assert result['results'][0]['index']=='RJ01000001'
    assert result['results'][0]['titleToggle'] is True
    assert result['results'][0]['name']=='Supplemental sunshine title'
    assert request('/api/search',params={'q':'Supplemental','genres':'001','ages':'000'}).json()['total']==1
    assert request('/api/random',params={'q':'Supplemental','ages':'000'}).json()['results'][0]['index']=='RJ01000001'
    assert request('/api/setup/titles/pause',method='POST',headers=headers).ok
    assert not request('/api/setup/status').json()['preferences']['enabled']
    request.restart()
    assert request('/api/search',params={'q':'Supplemental sunshine','ages':'000'}).json()['total']==1
    headers={'x-dlfilter-token':request('/api/setup/status').json()['token']}
    assert request('/api/setup/titles',method='POST',headers=headers,json={'languages':['bad'],'enabled':True}).status_code==422


def test_helper_protocol_and_shared_lookup():
    from module.title_lookup import extract_title,title_url
    assert 'books/api/' in title_url('BJ123456','books','ENG')
    assert extract_title([], '原題') is None
    assert extract_title([{'work_name':'原題'}], '原題') is None
    assert extract_title([{'work_name':'English'}], '原題')=='English'
    result=subprocess.run([sys.executable,'scripts/title_helper.py'],input='{"id":"invalid"}\n',text=True,capture_output=True,check=True)
    assert 'error' in json.loads(result.stdout)


def test_manifest_download_and_checksum_failure(setup_server,tmp_path):
    request,headers,root=setup_server
    bundle=archive(tmp_path)
    base=(root/'manifest-base.txt').read_text()
    manifest=dict(version=1,url=base+'/catalogue.zip',sha256='0'*64,size=bundle.stat().st_size)
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    assert request('/api/setup/download',method='POST',headers=headers).status_code==202
    bad=wait_for(lambda:request('/api/setup/status').json(),lambda s:s['installation']['state']=='error')
    assert 'checksum' in bad['installation']['message']
    assert not (root/'data').exists()
    manifest['sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest()
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    assert request('/api/setup/download',method='POST',headers=headers).status_code==202
    assert wait_for(lambda:request('/api/setup/status').json(),lambda s:s['ready'])['ready']


def test_failed_titles_are_retryable_and_negative_is_cached(setup_server,tmp_path):
    request,headers,root=setup_server
    def multilingual(data):
        with sqlite3.connect(data/'works.sqlite') as db:
            db.execute("UPDATE maniax SET options='#JPN#ENG#' WHERE [index]='RJ01000001'")
    assert install(request,headers,archive(tmp_path,multilingual))['ready']
    script=root/'scripts/title_helper.py'
    script.write_text('import sys,json\nfor line in sys.stdin: print(json.dumps({"error":"offline fixture failure"}),flush=True)\n')
    payload={'languages':['ENG'],'enabled':True}
    request('/api/setup/titles',method='POST',headers=headers,json=payload)
    failed=wait_for(lambda:request('/api/setup/status').json(),lambda s:s['titles']['state']=='error')
    assert failed['titles']['done']==0
    script.write_text('import sys,json\nfor line in sys.stdin: print(json.dumps({"title":None}),flush=True)\n')
    request('/api/setup/titles',method='POST',headers=headers,json=payload)
    complete=wait_for(lambda:request('/api/setup/status').json(),lambda s:s['titles']['state']=='complete')
    assert complete['titles']['done']==1 and complete['titles']['added']==0
    request('/api/setup/titles',method='POST',headers=headers,json=payload)
    repeat=wait_for(lambda:request('/api/setup/status').json(),lambda s:s['titles']['state']=='complete')
    assert repeat['titles']['total']==0


def test_catalogue_packager(tmp_path):
    from scripts.package_catalogue import build
    result=build(DATA_DIR,tmp_path/'out','https://example.invalid/works-serving.zip')
    path=tmp_path/'out/works-serving.zip'
    assert result['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z: assert sorted(z.namelist())==sorted(FILES)


def test_pause_resume_preserves_completed_lookups(setup_server,tmp_path):
    request,headers,root=setup_server
    def multilingual(data):
        with sqlite3.connect(data/'works.sqlite') as db:
            db.execute("UPDATE maniax SET options='#JPN#ENG#' WHERE [index] IN ('RJ01000001','RJ01000002','RJ01000003','RJ01000004')")
    assert install(request,headers,archive(tmp_path,multilingual))['ready']
    payload={'languages':['ENG'],'enabled':True}
    request('/api/setup/titles',method='POST',headers=headers,json=payload)
    wait_for(lambda:request('/api/setup/status').json(),lambda s:s['titles']['done']>=1)
    assert request('/api/setup/titles/pause',method='POST',headers=headers).ok
    paused=wait_for(lambda:request('/api/setup/status').json(),lambda s:s['titles']['state']=='paused')
    assert 1<=paused['titles']['done']<4
    assert paused['titles']['message']==''
    request('/api/setup/titles',method='POST',headers=headers,json=payload)
    complete=wait_for(lambda:request('/api/setup/status').json(),lambda s:s['titles']['state']=='complete')
    assert complete['titles']['done']==4-paused['titles']['done']
    assert request('/api/search',params={'q':'Supplemental sunshine','ages':'000'}).json()['total']==4


def test_cancel_download_and_duplicate_submission(setup_server,tmp_path):
    request,headers,root=setup_server
    base=(root/'manifest-base.txt').read_text()
    (tmp_path/'manifest.json').write_text(json.dumps(dict(version=1,url=base+'/slow.zip',size=10*1024*1024,sha256='0'*64)))
    assert request('/api/setup/download',method='POST',headers=headers).status_code==202
    wait_for(lambda:request('/api/setup/status').json(),lambda s:s['installation']['done']>0)
    assert request('/api/setup/download',method='POST',headers=headers).status_code==409
    assert request('/api/setup/cancel',method='POST',headers=headers).ok
    wait_for(lambda:request('/api/setup/status').json(),lambda s:s['installation']['state']=='cancelled',timeout=5)
    assert not (root/'data').exists()
