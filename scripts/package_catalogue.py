"""Create a portable serving bundle from trusted local data, without crawling or publishing."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

FILES = ('works.sqlite', 'genre_table.json', 'workformat.json', 'genre_vectors.json', 'genre_vectors.f32')


def build(data, output, url):
    output.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if not (data / name).is_file():
            raise ValueError(f'Missing {name}; convert trusted legacy vectors first')
    with sqlite3.connect((data / 'works.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise ValueError('Invalid database')
        columns = {row[1] for row in db.execute('PRAGMA table_info(maniax)')}
        if not {'index', 'name', 'tags', 'siteId'} <= columns:
            raise ValueError('Missing work schema')
    manifest = json.loads((data / 'genre_vectors.json').read_text())
    raw = (data / 'genre_vectors.f32').read_bytes()
    if manifest['version'] != 1 or hashlib.sha256(raw).hexdigest() != manifest['sha256']:
        raise ValueError('Invalid portable vectors')
    temporary = output / 'works-serving.zip.tmp'
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in FILES:
                archive.write(data / name, name)
        final = output / 'works-serving.zip'
        temporary.replace(final)
        digest = hashlib.file_digest(final.open('rb'), 'sha256').hexdigest()
        metadata = dict(version=1, url=url, sha256=digest, size=final.stat().st_size)
        (output / 'serving-catalogue.json').write_text(json.dumps(metadata, indent=2) + '\n')
        (output / 'works-serving.zip.sha256').write_text(f'{digest}  works-serving.zip\n')
        return metadata
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, default=Path('database'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--url', default='https://github.com/charasleeping/DLfilter/releases/download/database/works-serving.zip')
    args = p.parse_args()
    print(json.dumps(build(args.data, args.output, args.url)))
