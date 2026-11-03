#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
    python3 start.py --uninstall-shortcut
else
    echo "Python 3 is required to remove the shortcut."
    exit 1
fi
