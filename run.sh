#!/usr/bin/env bash
# Starts the CrimsonCart Receipts IDOR lab (macOS/Linux).
# No dependencies required - Python 3 standard library only.
set -e
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    exec python3 server.py
elif command -v python >/dev/null 2>&1; then
    exec python server.py
else
    echo "Python 3 was not found on this system. Install it from https://python.org and try again."
    exit 1
fi
