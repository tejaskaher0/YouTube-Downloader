#!/usr/bin/env python3
"""Remove YouTube Downloader shortcuts for the current user."""
from start import uninstall_shortcut

if __name__ == "__main__":
    raise SystemExit(0 if uninstall_shortcut() else 1)
