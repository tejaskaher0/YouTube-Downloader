#!/usr/bin/env python3
"""Terminal-only interface for the cross-platform YouTube downloader."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

QUALITIES = {
    "1": ("8K (4320p)", 4320),
    "2": ("4K (2160p)", 2160),
    "3": ("2K (1440p)", 1440),
    "4": ("1080p", 1080),
    "5": ("720p", 720),
    "6": ("480p", 480),
}


def say(message: str = "") -> None:
    print(message, flush=True)


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        say("\nCancelled.")
        raise SystemExit(1)
    return value or default


def default_download_dir() -> Path:
    downloads = Path.home() / "Downloads"
    return downloads if downloads.is_dir() else Path.home()


def valid_folder_name(name: str) -> bool:
    if not name or name in {".", ".."} or Path(name).name != name:
        return False
    forbidden = set('<>:"/\\|?*')
    return not any(char in forbidden or ord(char) < 32 for char in name)


class TerminalLogger:
    def debug(self, message):
        pass

    def warning(self, message):
        say(f"WARNING: {message}")

    def error(self, message):
        say(f"ERROR: {message}")


def main() -> int:
    print("=" * 64)
    print("             YOUTUBE DOWNLOADER - TERMINAL MODE")
    print("=" * 64)

    if yt_dlp is None:
        say("ERROR: yt-dlp is not installed. Run: python -m pip install --upgrade yt-dlp")
        return 1
    say(f"yt-dlp version: {yt_dlp.version.__version__}")
    missing = [name for name in ("ffmpeg", "ffprobe") if not shutil.which(name)]
    if missing:
        say("WARNING: Missing from PATH: " + ", ".join(missing))
        say("Separate video/audio streams may not merge without FFmpeg.")

    say("\nDownload type:")
    say("  1. Single video")
    say("  2. Entire playlist")
    mode = ask("Choose", "1")
    if mode not in {"1", "2"}:
        say("Invalid selection.")
        return 1
    is_playlist = mode == "2"

    url = ask("Paste YouTube video/playlist URL")
    if not url:
        say("URL is required.")
        return 1

    say("\nMaximum quality:")
    for key, (label, _) in QUALITIES.items():
        say(f"  {key}. {label}")
    quality_choice = ask("Choose quality", "4")
    if quality_choice not in QUALITIES:
        say("Invalid quality selection.")
        return 1
    quality_label, max_height = QUALITIES[quality_choice]

    default_dir = default_download_dir()
    destination_text = ask("Download destination", str(default_dir))
    destination = Path(destination_text).expanduser()
    if not destination.exists() or not destination.is_dir():
        say(f"ERROR: Destination folder does not exist or is not a directory: {destination}")
        return 1

    target = destination
    if is_playlist:
        say("\nPlaylist destination:")
        say("  1. Save directly in selected destination")
        say("  2. Create/use a subfolder")
        folder_choice = ask("Choose", "1")
        if folder_choice == "2":
            folder_name = ask("Subfolder name")
            if not valid_folder_name(folder_name):
                say("ERROR: Invalid folder name. Do not use path separators or reserved characters.")
                return 1
            target = destination / folder_name
        elif folder_choice != "1":
            say("Invalid selection.")
            return 1

    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        say(f"ERROR: Cannot create destination: {exc}")
        return 1

    suggested_cookie = default_dir / "youtube-cookies.txt"
    cookie_default = str(suggested_cookie) if suggested_cookie.is_file() else ""
    cookie_text = ask("Cookies file path (optional; press Enter to skip)", cookie_default)
    cookie_file = Path(cookie_text).expanduser() if cookie_text else None
    if cookie_file and not cookie_file.is_file():
        say(f"WARNING: Cookies file not found: {cookie_file}")
        if ask("Continue without cookies? (Y/n)", "Y").lower() not in {"y", "yes"}:
            return 1
        cookie_file = None

    say("\n" + "-" * 64)
    say(f"Type: {'Playlist' if is_playlist else 'Single video'}")
    say(f"Destination: {target}")
    say(f"Maximum quality: {quality_label}")
    say(f"Cookies: {cookie_file if cookie_file else 'Not selected'}")
    say("Starting download...\n")

    last_percent = {"value": -1}

    def progress_hook(data):
        status = data.get("status")
        info = data.get("info_dict") or {}
        title = info.get("title") or "Downloading"
        if status == "downloading":
            downloaded = data.get("downloaded_bytes") or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            if total:
                percent = downloaded * 100 / total
                if int(percent) != last_percent["value"]:
                    last_percent["value"] = int(percent)
                    line = f"\rDownloading: {percent:5.1f}% | {title[:65]}"
                    print(line, end="", flush=True)
        elif status == "finished":
            print(f"\nDownloaded stream: {title} (post-processing may follow)", flush=True)

    options = {
        "format": f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]",
        "merge_output_format": "mp4",
        "outtmpl": str(target / "%(title)s [%(height)sp] [%(id)s].%(ext)s"),
        "noplaylist": not is_playlist,
        "overwrites": False,
        "continuedl": True,
        "ignoreerrors": False,
        "quiet": True,
        "no_warnings": False,
        "progress_hooks": [progress_hook],
        "logger": TerminalLogger(),
        "windowsfilenames": True,
        "trim_file_name": 180,
    }
    if cookie_file:
        options["cookiefile"] = str(cookie_file)

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            result = downloader.download([url])
        say("\nDownload process finished. Check the selected destination.")
        return 0 if result == 0 else 1
    except KeyboardInterrupt:
        say("\nDownload cancelled by user.")
        return 130
    except Exception as exc:
        say(f"\nDOWNLOAD ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
