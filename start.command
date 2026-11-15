#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
set -e
trap 'status=$?; if [ "$status" -ne 0 ]; then read -r -p "DLFilter stopped. Press Enter to close."; fi' EXIT
if [ -x ./bin/dlfilter ]; then
    ./bin/dlfilter serve --open
elif [ -x ./target/release/dlfilter ]; then
    ./target/release/dlfilter serve --open
else
    echo "Native server not found. Install a native release or run: cargo build --release --locked"
    exit 1
fi
