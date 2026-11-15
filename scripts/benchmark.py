"""Read-only catalogue benchmarks. All derived assets and presets use a temporary directory."""
import argparse
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def percentile(values, percentile):
    values = sorted(values)
    return values[min(len(values)-1, int(len(values)*percentile))]


def run(data, output, samples):
    from module.export_vectors import export_vectors
    import pickle
    with tempfile.TemporaryDirectory(prefix='dlfilter-benchmark-') as tmp:
        tmp = Path(tmp); prepared = tmp/'data'; prepared.mkdir()
        for name in ('works.sqlite','genre_table.json','workformat.json'):
            (prepared/name).symlink_to((data/name).resolve())
        if (data/'genre_vectors.json').exists():
            for name in ('genre_vectors.json','genre_vectors.f32'):
                (prepared/name).symlink_to((data/name).resolve())
        else:
            with (data/'genre_vec.pkl').open('rb') as f: export_vectors(pickle.load(f),prepared)
        (prepared/'genre_vec.pkl').symlink_to((data/'genre_vec.pkl').resolve())
        with sqlite3.connect((data/'works.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as c:
            size=c.execute('SELECT COUNT(*) FROM maniax').fetchone()[0]
            known=c.execute('SELECT [index] FROM maniax ORDER BY [index] LIMIT 1').fetchone()[0]
        env=dict(os.environ,DLFILTER_DATA_DIR=str(prepared),DLFILTER_CACHE_DIR=str(tmp/'cache'),DLFILTER_PRESETS_DIR=str(tmp/'presets'),PYTHONPATH=str(ROOT))
        binary=ROOT/'target/release/dlfilter'
        t=time.perf_counter(); subprocess.run([str(binary),'prepare'],env=env,check=True); prepare_seconds=time.perf_counter()-t
        workloads=[('browse',{'ages':'100'}),('short_keyword',{'q':'少女','ages':'100'}),('long_keyword',{'q':'魔法少女','ages':'100'}),('id',{'q':known,'ages':'000','field':'id'}),('recent_similarity',{'genres':'001+002','ages':'000','since':'2026-10-01'}),('broad_similarity',{'genres':'001+002','ages':'100'}),('deep_similarity_page',{'genres':'001+002','ages':'100','page':5}),('random',{'ages':'100','count':48})]
        report={'platform':platform.platform(),'machine':platform.machine(),'catalogue_rows':size,'samples':samples,'prepare_seconds':prepare_seconds,'backends':{}}
        for backend in ('python','rust'):
            with socket.socket() as sock: sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
            env['DLFILTER_PORT']=str(port)
            command=[str(binary),'serve'] if backend=='rust' else [sys.executable,'-m','uvicorn','reference.python_app:app','--app-dir','tests','--host','127.0.0.1','--port',str(port)]
            rss=tmp/f'{backend}-rss.json'; log=(tmp/f'{backend}.log').open('w+')
            process=subprocess.Popen([sys.executable,str(ROOT/'scripts/measure_server.py'),'--output',str(rss),'--',*command],env=env,cwd=ROOT,stdout=log,stderr=log)
            session=requests.Session();session.trust_env=False; base=f'http://127.0.0.1:{port}'
            started=time.perf_counter()
            try:
                for _ in range(1000):
                    if process.poll() is not None: log.seek(0); raise RuntimeError(log.read())
                    try:
                        if session.get(base+'/api/info',timeout=.3).status_code==200: break
                    except requests.RequestException: pass
                    time.sleep(.02)
                else: raise RuntimeError('Startup timeout')
                result={'startup_seconds':time.perf_counter()-started,'queries':{}}
                for label,params in workloads:
                    route='/api/random' if label=='random' else '/api/search'
                    t=time.perf_counter(); response=session.get(base+route,params=params,timeout=90);response.raise_for_status(); first=time.perf_counter()-t; body=response.json()
                    times=[]
                    for _ in range(samples):
                        t=time.perf_counter();r=session.get(base+route,params=params,timeout=90);r.raise_for_status();times.append((time.perf_counter()-t)*1000)
                    stats={'first_ms':first*1000,'median_ms':percentile(times,.5),'p95_ms':percentile(times,.95),'total':body.get('total',len(body.get('results',[])))}
                    result['queries'][label]=stats
                    print(backend,label,json.dumps(stats),flush=True)
                if backend=='rust':
                    t=time.perf_counter(); r=session.get(base+'/api/search',params={'genres':'001+002','ages':'000'},timeout=90);r.raise_for_status();result['all_catalogue_similarity_first_ms']=(time.perf_counter()-t)*1000
                report['backends'][backend]=result
            finally:
                process.terminate();process.wait(timeout=20);session.close();log.close()
            result.update(json.loads(rss.read_text()))
        p=report['backends']['python']; r=report['backends']['rust']
        report['acceptance']={'warm_p95_under_150ms':all(v['p95_ms']<150 for v in r['queries'].values()),'rss_under_512mib':r['peak_rss_mib']<512,'slow_case_speedups':{k:p['queries'][k]['p95_ms']/r['queries'][k]['p95_ms'] for k in ('short_keyword','browse','broad_similarity')}}
        output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report['acceptance']),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,default=ROOT/'database');p.add_argument('--output',type=Path,default=ROOT/'benchmarks/local.json');p.add_argument('--samples',type=int,default=20);a=p.parse_args();run(a.data,a.output,a.samples)
