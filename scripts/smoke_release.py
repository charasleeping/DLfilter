"""Smoke-test an extracted native release with no interpreters available on its PATH."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import struct
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile


def smoke(archive):
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder)
        with zipfile.ZipFile(archive) as z:
            z.extractall(folder)
            for item in z.infolist():
                if not item.is_dir(): (folder/item.filename).chmod(item.external_attr>>16 or 0o644)
        root=next(p for p in folder.iterdir() if p.is_dir())
        suffix='.exe' if os.name=='nt' else ''
        helper=root/'bin'/('dlfilter-titles'+suffix)
        empty_path=folder/'no-tools';empty_path.mkdir()
        env=dict(os.environ,PATH=str(empty_path),DLFILTER_DATA_DIR=str(folder/'data'),DLFILTER_CACHE_DIR=str(folder/'cache'),DLFILTER_PRESETS_DIR=str(folder/'presets'))
        env.pop('DLFILTER_TITLE_PYTHON',None);env.pop('DLFILTER_ROOT',None)
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env['DLFILTER_PORT']=str(port);env['DLFILTER_HOST']='127.0.0.1'
        result=subprocess.run([str(helper)],input='{"id":"invalid"}\n',text=True,capture_output=True,env=env,timeout=30,check=True)
        assert 'error' in json.loads(result.stdout)
        server=subprocess.Popen([str(root/'bin'/('dlfilter'+suffix)),'serve'],env=env,cwd=folder,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));base=f'http://127.0.0.1:{port}'
        def request(route,data=None,headers=None):
            req=urllib.request.Request(base+route,data=data,headers=headers or {})
            with opener.open(req,timeout=10) as response:return json.load(response)
        try:
            for _ in range(200):
                try:status=request('/api/setup/status');break
                except OSError:time.sleep(.05)
            else:raise RuntimeError('Packaged server did not start')
            assert not status['ready']
            payload=folder/'fixture';payload.mkdir()
            db=sqlite3.connect(payload/'works.sqlite')
            db.execute('CREATE TABLE maniax ([index] TEXT PRIMARY KEY,name TEXT,description TEXT,maker TEXT,siteId TEXT,type TEXT,ageCategory INTEGER,tags TEXT,options TEXT,registDate TEXT,dlCount INTEGER,rate INTEGER,rateCount INTEGER,reviewCount INTEGER)')
            db.execute("INSERT INTO maniax VALUES ('BJ123456','Smoke book','','Publisher','books','MNG',1,'#001#','#JPN#','2026-01-01',10,45,10,0)");db.commit();db.close()
            names={l:'Fixture' for l in ('en_US','ja_JP','zh_TW','zh_CN')}
            (payload/'genre_table.json').write_text(json.dumps({'001':dict(name=names,category=names,count=1)}))
            (payload/'workformat.json').write_text(json.dumps({'MNG':dict(name=names,category=names)}))
            raw=struct.pack('<ff',1,0);(payload/'genre_vectors.f32').write_bytes(raw)
            (payload/'genre_vectors.json').write_text(json.dumps(dict(version=1,ids=['001'],dimension=2,sha256=hashlib.sha256(raw).hexdigest())))
            zip_path=folder/'fixture.zip'
            with zipfile.ZipFile(zip_path,'w') as z:
                for file in payload.iterdir():z.write(file,file.name)
            boundary='release-smoke-boundary'
            body=f'--{boundary}\r\nContent-Disposition: form-data; name="catalogue"; filename="fixture.zip"\r\nContent-Type: application/zip\r\n\r\n'.encode()+zip_path.read_bytes()+f'\r\n--{boundary}--\r\n'.encode()
            request('/api/setup/import',body,{'Content-Type':f'multipart/form-data; boundary={boundary}','X-DLFilter-Token':status['token']})
            for _ in range(200):
                status=request('/api/setup/status')
                if status['ready']:break
                if status['installation']['state']=='error':raise RuntimeError(status)
                time.sleep(.05)
            assert status['ready']
            assert request('/api/search?q=Smoke')['results'][0]['index']=='BJ123456'
            with opener.open(base+'/',timeout=10) as response:assert b'catalog-card-container' in response.read()
            print('Packaged setup, import, search, frontend and private helper passed:',archive)
        finally:server.terminate();server.wait(timeout=10)


if __name__=='__main__':
    import sys
    for file in sys.argv[1:] or sorted(Path('dist').glob('*.zip')):smoke(Path(file))
