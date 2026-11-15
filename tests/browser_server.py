"""Serve disposable catalogue fixtures for Playwright; never opens the user's data."""
import json
import pickle
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from conftest import DATA_DIR, WORKS, work, write_works_db
import numpy as np
import uvicorn

genres = json.loads((DATA_DIR / 'genre_table.json').read_text())
with (DATA_DIR / 'genre_vec.pkl').open('rb') as f:
    vectors = pickle.load(f)
for i in range(5, 15):
    gid = f'{i:03}'
    genres[gid] = dict(genres['001'], name={loc: f'Genre {gid}' for loc in genres['001']['name']})
    vectors[gid] = np.ones(8, dtype=np.float32)
(DATA_DIR / 'genre_table.json').write_text(json.dumps(genres))
with (DATA_DIR / 'genre_vec.pkl').open('wb') as f:
    pickle.dump(vectors, f)
write_works_db(DATA_DIR / 'works.sqlite', WORKS + [
    work('BJ123456', 'Test Book', 'Publisher', tags='#002#003#005#006#007#008#009#010#011#012#013#014#', siteId='books'),
    work('VJ01234567', 'Test Game', 'Brand', tags='#001#004#', siteId='soft'),
    work('BJ654321', 'Tagless Book', 'Publisher', tags='', siteId='books'),
])
if __name__ == '__main__':
    import os
    from module.export_vectors import export_vectors
    export_vectors(vectors, DATA_DIR)
    os.environ['DLFILTER_CACHE_DIR'] = str(DATA_DIR / 'cache')
    os.environ['DLFILTER_PORT'] = '8765'
    if os.environ.get('DLFILTER_TEST_BACKEND') == 'python':
        uvicorn.run('reference.python_app:app', host='127.0.0.1', port=8765)
    else:
        os.execv(str(Path(__file__).resolve().parent.parent / ('target/release/dlfilter.exe' if os.name == 'nt' else 'target/release/dlfilter')), ['dlfilter', 'serve'])
