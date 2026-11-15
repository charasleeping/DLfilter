"""Portable genre vectors. Pickle conversion is explicit and only for trusted local files."""
import argparse
import hashlib
import json
import math
import os
import pickle
import struct
import tempfile
from pathlib import Path


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.vectors-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def export_vectors(vectors, directory):
    ids = sorted(vectors)
    if not ids:
        raise ValueError('No genre vectors')
    dimension = len(vectors[ids[0]])
    if not 1 <= dimension <= 65536 or len(ids) > 1000:
        raise ValueError('Invalid vector dimensions')
    payload = bytearray()
    for gid in ids:
        row = vectors[gid]
        if len(gid) != 3 or not gid.isascii() or not gid.isdigit() or len(row) != dimension:
            raise ValueError('Invalid genre vector')
        for value in row:
            value = float(value)
            if not math.isfinite(value):
                raise ValueError('Nonfinite genre vector')
            payload.extend(struct.pack('<f', value))
    manifest = dict(version=1, ids=ids, dimension=dimension, sha256=hashlib.sha256(payload).hexdigest())
    directory = Path(directory)
    atomic_write(directory / 'genre_vectors.f32', payload)
    atomic_write(directory / 'genre_vectors.json', json.dumps(manifest).encode())
    return manifest


def main():
    from module import config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trusted-pickle', type=Path, required=True, help='Only use a local pickle you trust; loading pickle executes code.')
    parser.add_argument('--output', type=Path, default=config.DATA_DIR)
    args = parser.parse_args()
    with args.trusted_pickle.open('rb') as f:
        vectors = pickle.load(f)
    result = export_vectors(vectors, args.output)
    print(f"Exported {len(result['ids'])} vectors, dimension {result['dimension']}, to {args.output}")


if __name__ == '__main__':
    main()
