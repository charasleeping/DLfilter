"""Offline packaged-helper smoke test, requiring no Python packages or catalogue."""
import json
import os
from pathlib import Path
import subprocess

binary = Path('dist') / ('dlfilter-titles.exe' if os.name == 'nt' else 'dlfilter-titles')
result = subprocess.run([str(binary.resolve())], input='{"id":"invalid"}\n', text=True, capture_output=True, timeout=30, check=True)
assert 'error' in json.loads(result.stdout)
print('Packaged title helper works offline')
