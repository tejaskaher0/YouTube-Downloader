#!/usr/bin/env python3
"""Cross-platform YouTube Downloader GUI.

Tkinter desktop UI backed by yt-dlp. FFmpeg is used by yt-dlp to merge
separate audio/video streams when available.
"""

from __future__ import annotations

import queue
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


APP_TITLE = "YouTube Downloader"
QUALITIES = {
    "8K (4320p)": 4320,
    "4K (2160p)": 2160,
    "2K (1440p)": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
}


def default_download_dir() -> Path:
    """Use ~/Downloads where present; otherwise fall back to the home directory."""
    downloads = Path.home() / "Downloads"
    return downloads if downloads.is_dir() else Path.home()


class QueueLogger:
    """Forward yt-dlp log messages safely to the Tkinter main thread."""

    def __init__(self, event_queue: queue.Queue):
        self.events = event_queue

    def debug(self, message):
        # yt-dlp sends progress/debug chatter here; progress hooks handle the UI.
        if message and not str(message).startswith("[debug]"):
            return

    def warning(self, message):
        self.events.put(("log", f"WARNING: {message}"))

    def error(self, message):
        self.events.put(("log", f"ERROR: {message}"))


class YouTubeDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("850x720")
        self.root.minsize(720, 620)

        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.downloading = False
        self.completed_items = 0
        self.errors = 0

        downloads = default_download_dir()
        self.mode = tk.StringVar(value="single")
        self.quality = tk.StringVar(value="1080p")
        self.destination = tk.StringVar(value=str(downloads))
        self.playlist_location = tk.StringVar(value="default")
        self.playlist_folder = tk.StringVar()
        self.cookies_path = tk.StringVar(value=str(downloads / "youtube-cookies.txt"))
        self.status = tk.StringVar(value="Ready")
        self.progress_value = tk.DoubleVar(value=0)

        self._build_interface()
        self._check_dependencies()
        self.root.after(100, self._drain_events)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build_interface(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="YouTube Downloader", font=("TkDefaultFont", 20, "bold")).pack(anchor="w")
        ttk.Label(
            container,
            text="Cross-platform video and playlist downloader · Windows · Linux · macOS",
        ).pack(anchor="w", pady=(2, 12))

        mode_box = ttk.LabelFrame(container, text="Download type", padding=9)
        mode_box.pack(fill="x", pady=5)
        ttk.Radiobutton(
            mode_box, text="Single video", variable=self.mode, value="single",
            command=self._refresh_mode
        ).pack(side="left", padx=(0, 18))
        ttk.Radiobutton(
            mode_box, text="Entire playlist", variable=self.mode, value="playlist",
            command=self._refresh_mode
        ).pack(side="left")

        url_box = ttk.LabelFrame(container, text="YouTube URL", padding=9)
        url_box.pack(fill="x", pady=5)
        self.url_entry = ttk.Entry(url_box)
        self.url_entry.pack(fill="x")
        self.url_entry.focus_set()

        choices = ttk.Frame(container)
        choices.pack(fill="x", pady=5)

        quality_box = ttk.LabelFrame(choices, text="Maximum quality", padding=9)
        quality_box.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.quality_combo = ttk.Combobox(
            quality_box, textvariable=self.quality,
            values=list(QUALITIES), state="readonly"
        )
        self.quality_combo.pack(fill="x")

        destination_box = ttk.LabelFrame(choices, text="Download destination", padding=9)
        destination_box.pack(side="left", fill="both", expand=True, padx=(5, 0))
        destination_row = ttk.Frame(destination_box)
        destination_row.pack(fill="x")
        ttk.Entry(destination_row, textvariable=self.destination).pack(side="left", fill="x", expand=True)
        ttk.Button(destination_row, text="Browse…", command=self._browse_destination).pack(side="left", padx=(6, 0))

        self.playlist_box = ttk.LabelFrame(container, text="Playlist folder options", padding=9)
        self.playlist_box.pack(fill="x", pady=5)
        self.default_radio = ttk.Radiobutton(
            self.playlist_box, text="Save directly in the selected destination",
            variable=self.playlist_location, value="default",
            command=self._refresh_playlist_folder
        )
        self.default_radio.pack(anchor="w")
        self.subfolder_radio = ttk.Radiobutton(
            self.playlist_box, text="Create/use a new subfolder",
            variable=self.playlist_location, value="subfolder",
            command=self._refresh_playlist_folder
        )
        self.subfolder_radio.pack(anchor="w")
        self.folder_entry = ttk.Entry(self.playlist_box, textvariable=self.playlist_folder)
        self.folder_entry.pack(fill="x", pady=(5, 0))

        cookie_box = ttk.LabelFrame(container, text="YouTube cookies (optional)", padding=9)
        cookie_box.pack(fill="x", pady=5)
        cookie_row = ttk.Frame(cookie_box)
        cookie_row.pack(fill="x")
        ttk.Entry(cookie_row, textvariable=self.cookies_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cookie_row, text="Browse…", command=self._browse_cookies).pack(side="left", padx=(6, 0))
        ttk.Label(
            cookie_box,
            text="Select a Netscape-format cookies.txt file if YouTube requires sign-in. Keep it private.",
            wraplength=780,
        ).pack(anchor="w", pady=(5, 0))

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=(9, 5))
        self.start_button = ttk.Button(buttons, text="Start Download", command=self._start)
        self.start_button.pack(side="left")
        ttk.Button(buttons, text="Clear Log", command=self._clear_log).pack(side="left", padx=8)

        ttk.Progressbar(
            container, variable=self.progress_value, maximum=100, mode="determinate"
        ).pack(fill="x", pady=(6, 3))
        ttk.Label(container, textvariable=self.status).pack(anchor="w")

        log_box = ttk.LabelFrame(container, text="Activity log", padding=7)
        log_box.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(log_box, height=12, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self._refresh_mode()

    def _log(self, message: str):
        self.log.configure(state="normal")
        self.log.insert("end", str(message).rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _check_dependencies(self):
        if yt_dlp is None:
            self._log("ERROR: yt-dlp is not installed. Run: python -m pip install -r requirements.txt")
            self.status.set("Install Python dependencies, then restart.")
            return
        missing = [name for name in ("ffmpeg", "ffprobe") if not shutil.which(name)]
        if missing:
            self._log("WARNING: Not found on PATH: " + ", ".join(missing))
            self._log("Install FFmpeg to merge separate video and audio streams.")
        self._log(f"yt-dlp version: {yt_dlp.version.__version__}")
        self._log("Ready. Paste a video or playlist URL.")

    def _refresh_mode(self):
        playlist_enabled = self.mode.get() == "playlist"
        state = "normal" if playlist_enabled else "disabled"
        self.default_radio.configure(state=state)
        self.subfolder_radio.configure(state=state)
        self._refresh_playlist_folder()

    def _refresh_playlist_folder(self):
        enabled = self.mode.get() == "playlist" and self.playlist_location.get() == "subfolder"
        self.folder_entry.configure(state="normal" if enabled else "disabled")

    def _browse_destination(self):
        folder = filedialog.askdirectory(
            title="Choose download destination",
            initialdir=self.destination.get() or str(Path.home()),
        )
        if folder:
            self.destination.set(folder)

    def _browse_cookies(self):
        path = filedialog.askopenfilename(
            title="Select cookies file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=str(Path(self.cookies_path.get()).parent),
        )
        if path:
            self.cookies_path.set(path)

    @staticmethod
    def _valid_folder_name(name: str) -> bool:
        if not name or name in {".", ".."} or Path(name).name != name:
            return False
        forbidden = set('<>:"/\\\\|?*')
        return not any(char in forbidden or ord(char) < 32 for char in name)

    def _start(self):
        if self.downloading:
            return
        if yt_dlp is None:
            messagebox.showerror("Missing dependency", "Install yt-dlp using the README instructions.")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL required", "Paste a YouTube video or playlist URL.")
            return

        destination = Path(self.destination.get()).expanduser()
        if not destination.exists() or not destination.is_dir():
            messagebox.showerror("Invalid destination", "Choose an existing destination folder.")
            return

        is_playlist = self.mode.get() == "playlist"
        target = destination
        if is_playlist and self.playlist_location.get() == "subfolder":
            folder = self.playlist_folder.get().strip()
            if not self._valid_folder_name(folder):
                messagebox.showerror("Invalid folder name", "Enter a folder name without path separators or reserved characters.")
                return
            target = destination / folder

        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Cannot create folder", str(exc))
            return

        cookie_text = self.cookies_path.get().strip()
        cookie_file = Path(cookie_text).expanduser() if cookie_text else None
        if cookie_file and not cookie_file.is_file():
            if messagebox.askyesno("Cookies file not found", f"File not found:\n{cookie_file}\n\nContinue without cookies?"):
                cookie_file = None
            else:
                return

        self.downloading = True
        self.completed_items = 0
        self.errors = 0
        self.progress_value.set(0)
        self.status.set("Starting…")
        self.start_button.configure(state="disabled")
        self._log("-" * 64)
        self._log(f"Type: {'Playlist' if is_playlist else 'Single video'}")
        self._log(f"Destination: {target}")
        self._log(f"Maximum quality: {self.quality.get()}")
        self._log(f"Cookies: {cookie_file if cookie_file else 'Not selected'}")

        self.worker = threading.Thread(
            target=self._download_worker,
            args=(url, target, QUALITIES[self.quality.get()], is_playlist, cookie_file),
            daemon=True,
        )
        self.worker.start()

    def _download_worker(self, url: str, target: Path, max_height: int, is_playlist: bool, cookie_file: Path | None):
        try:
            def progress_hook(data):
                state = data.get("status")
                info = data.get("info_dict") or {}
                title = info.get("title") or "Downloading"
                if state == "downloading":
                    downloaded = data.get("downloaded_bytes") or 0
                    total = data.get("total_bytes") or data.get("total_bytes_estimate")
                    percent = (downloaded * 100 / total) if total else 0
                    self.events.put(("progress", percent, title))
                elif state == "finished":
                    self.events.put(("log", f"Downloaded stream: {title} (merging/post-processing may follow)"))

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
                "logger": QueueLogger(self.events),
                "windowsfilenames": True,
                "trim_file_name": 180,
            }
            if cookie_file:
                options["cookiefile"] = str(cookie_file)

            self.events.put(("log", "Starting yt-dlp. This can take a moment…"))
            with yt_dlp.YoutubeDL(options) as downloader:
                result_code = downloader.download([url])
            self.events.put(("finished", result_code))
        except Exception as exc:
            self.events.put(("fatal", str(exc)))

    def _drain_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    self._log(event[1])
                elif kind == "progress":
                    percent, title = event[1], event[2]
                    self.progress_value.set(max(0, min(100, percent)))
                    self.status.set(f"{percent:.1f}% — {title}")
                elif kind == "finished":
                    self._finish(event[1] == 0)
                elif kind == "fatal":
                    self._log("DOWNLOAD ERROR: " + event[1])
                    self._finish(False)
                    messagebox.showerror("Download failed", event[1])
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _finish(self, success: bool):
        if not self.downloading:
            return
        self.downloading = False
        self.start_button.configure(state="normal")
        if success:
            self.progress_value.set(100)
            self.status.set("Download finished.")
            self._log("Download process finished. Check the selected destination.")
        else:
            self.status.set("Download failed. Review the activity log.")
            self._log("Download did not finish successfully. Review the messages above.")

    def _close(self):
        if self.downloading and not messagebox.askyesno(
            "Download in progress",
            "A download is running. Closing now may interrupt it. Close anyway?"
        ):
            return
        self.root.destroy()


def main():
    root = tk.Tk()
    YouTubeDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
