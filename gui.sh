#!/usr/bin/env bash
# Launch osu! Beatmap Downloader GUI on macOS / Linux / Git Bash

if command -v python3 >/dev/null 2>&1; then
    python3 gui.py "$@"
elif command -v python >/dev/null 2>&1; then
    python gui.py "$@"
else
    echo "Error: Python is required to run the GUI on Linux/macOS." >&2
    echo "Please install python3 (e.g. brew install python-tk or sudo apt install python3-tk)" >&2
    exit 1
fi
