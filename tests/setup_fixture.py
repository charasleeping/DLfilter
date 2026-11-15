"""Write a tiny serving ZIP for the isolated setup-browser tests."""
from pathlib import Path
import sys
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conftest import DATA_DIR

with zipfile.ZipFile(Path(sys.argv[1]), 'w', zipfile.ZIP_DEFLATED) as z:
    for name in ('works.sqlite','genre_table.json','workformat.json','genre_vectors.json','genre_vectors.f32'):
        z.write(DATA_DIR/name,name)
