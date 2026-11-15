"""Compatibility launcher. Normal serving runs entirely in the Rust executable."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    filename = 'dlfilter.exe' if os.name == 'nt' else 'dlfilter'
    binary = next((p for p in (root/'bin'/filename, root/'target/release'/filename) if p.is_file()), None)
    if binary is None:
        sys.exit('Native server not found. Install a native release or run: cargo build --release --locked')
    args = [str(binary), 'serve']
    if '--open' in sys.argv[1:]: args.append('--open')
    return subprocess.call(args)


if __name__ == '__main__':
    sys.exit(main())
