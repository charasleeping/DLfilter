#!/usr/bin/env bash
# Starts DLfilter. Double-click on macOS, or run ./start.command on Linux.
cd "$(dirname "$0")" || exit 1

pause_on_error() {
    status=$?
    # 130 is Ctrl+C, the normal way to stop the server.
    if [ "$status" -ne 0 ] && [ "$status" -ne 130 ]; then
        echo
        read -r -p "Something went wrong. Press Enter to close."
    fi
}
trap pause_on_error EXIT
set -e

export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
    echo "DLfilter uses uv (https://docs.astral.sh/uv/) to set up Python and its libraries."
    read -r -p "Install uv now with https://astral.sh/uv/install.sh? [y/N] " answer
    case "$answer" in
        [yY]*) curl -LsSf https://astral.sh/uv/install.sh | sh ;;
        *) echo "Cancelled."; exit 1 ;;
    esac
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing libraries (the first run downloads about 1 GB)..."
uv sync --locked
uv run --no-sync python -m module.fetch_database

echo "Starting DLfilter. Press Ctrl+C to stop."
uv run --no-sync python app.py --open
