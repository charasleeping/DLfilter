"""Transactional daily checkpoints, replayed over the legacy raw JSON catalogue.

Records and their completed source/day are committed together. This avoids rewriting
multi-gigabyte JSON files after every day and makes first-time backfills resumable.
"""
import json
import sqlite3
from pathlib import Path

CHECKPOINT_FILE = 'catalogue_updates.sqlite'


def checkpoint(path, source, day, fetched_at, records):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path / CHECKPOINT_FILE) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS days (source TEXT, day TEXT, fetched_at TEXT, PRIMARY KEY(source, day))')
        conn.executemany('INSERT OR REPLACE INTO records VALUES (?, ?)',
                         [(w['id'], json.dumps(w, ensure_ascii=False)) for w in records])
        conn.execute('INSERT OR REPLACE INTO days VALUES (?, ?, ?)', (source, day, fetched_at))


def replay(path, works, dates):
    file = Path(path) / CHECKPOINT_FILE
    if not file.is_file():
        return
    with sqlite3.connect(file.resolve().as_uri() + '?mode=ro', uri=True) as conn:
        for workno, payload in conn.execute('SELECT id, payload FROM records'):
            works[workno] = json.loads(payload)
        for source, day, fetched_at in conn.execute('SELECT source, day, fetched_at FROM days'):
            dates.setdefault(source, {})[day] = fetched_at
