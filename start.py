#!/usr/bin/env python3
"""Smart cross-platform launcher for YouTube Downloader.

GUI desktop launches are windowed (no console). Running this script from a
terminal on a headless machine starts the terminal downloader in that terminal.
Use --terminal to explicitly request terminal mode.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import platform
import shutil
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GUI_APP = ROOT / "src" / "main.py"
TERMINAL_APP = ROOT / "src" / "terminal.py"
APP_TITLE = "YouTube Downloader"


def has_graphical_session() -> bool:
    system = platform.system()
    if system == "Windows":
        return True
    if system == "Darwin":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.environ.get("TERM_PROGRAM"))
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def show_error(title: str, message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message, parent=root)
        root.destroy()
    except Exception:
        print(f"{title}: {message}", file=sys.stderr)


def install_ytdlp_for_gui() -> bool:
    """Install yt-dlp quietly so a GUI launch never flashes a console window."""
    if importlib.util.find_spec("yt_dlp") is None:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=600,
            )
        except Exception as exc:
            show_error("Dependency installation failed",
                       f"Could not install yt-dlp automatically.\n\n{exc}\n\n"
                       "Install it with:\npython -m pip install --upgrade yt-dlp")
            return False
        if result.returncode != 0:
            details = (result.stdout or "")[-2500:]
            show_error("Dependency installation failed",
                       "yt-dlp could not be installed automatically.\n\n"
                       f"{details}\n\n"
                       "Install it with:\npython -m pip install --upgrade yt-dlp")
            return False
    importlib.invalidate_caches()
    try:
        import yt_dlp  # noqa: F401
        return True
    except Exception as exc:
        show_error("Dependency error", f"yt-dlp is still unavailable:\n\n{exc}")
        return False


def desktop_directory() -> Path:
    """Resolve the user's configured Desktop folder, including localized paths."""
    home = Path.home()
    if platform.system() == "Linux":
        xdg_user_dir = shutil.which("xdg-user-dir")
        if xdg_user_dir:
            try:
                result = subprocess.run(
                    [xdg_user_dir, "DESKTOP"],
                    capture_output=True, text=True, timeout=5, check=False
                )
                value = result.stdout.strip()
                if result.returncode == 0 and value:
                    candidate = Path(value).expanduser()
                    if candidate.is_absolute():
                        return candidate
            except Exception:
                pass
    return home / "Desktop"


def _desktop_entry_quote(value: str) -> str:
    """Quote a value for the Exec key in a freedesktop .desktop file."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return f'"{escaped}"'


def _mark_linux_shortcut_trusted(shortcut: Path) -> None:
    """Best-effort trust marking for desktop environments such as GNOME."""
    gio = shutil.which("gio")
    if gio:
        try:
            subprocess.run(
                [gio, "set", str(shortcut), "metadata::trusted", "true"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=5, check=False
            )
        except Exception:
            pass


def create_shortcut() -> bool:
    """Create or refresh a desktop/application launcher after the first GUI startup."""
    system = platform.system()
    script = ROOT / "start.py"
    desktop = desktop_directory()

    if system == "Windows":
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if not pythonw.exists():
            pythonw = Path(sys.executable)
        try:
            desktop.mkdir(parents=True, exist_ok=True)
            shortcut = desktop / f"{APP_TITLE}.lnk"
            ps = shutil.which("powershell") or shutil.which("pwsh")
            if not ps:
                return False

            def ps_quote(value: str) -> str:
                return value.replace("'", "''")

            command = (
                "$w=New-Object -ComObject WScript.Shell;"
                f"$s=$w.CreateShortcut('{ps_quote(str(shortcut))}');"
                f"$s.TargetPath='{ps_quote(str(pythonw))}';"
                f"$s.Arguments='\"{ps_quote(str(script))}\"';"
                f"$s.WorkingDirectory='{ps_quote(str(ROOT))}';"
                "$s.Description='YouTube video and playlist downloader';"
                "$s.Save()"
            )
            result = subprocess.run(
                [ps, "-NoProfile", "-NonInteractive", "-Command", command],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=15, check=False
            )
            return result.returncode == 0 and shortcut.exists()
        except Exception:
            return False

    if system == "Linux":
        try:
            # Application-menu entry: this is available even if the Desktop folder
            # is hidden, absent, or not used by the desktop environment.
            data_home = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))).expanduser()
            applications = data_home / "applications"
            applications.mkdir(parents=True, exist_ok=True)

            executable = str(Path(sys.executable).resolve())
            script_path = str(script.resolve())
            working_dir = str(ROOT.resolve())
            desktop_entry = (
                "[Desktop Entry]\n"
                "Version=1.0\n"
                "Type=Application\n"
                f"Name={APP_TITLE}\n"
                "Comment=Download YouTube videos and playlists\n"
                f"Exec={_desktop_entry_quote(executable)} {_desktop_entry_quote(script_path)}\n"
                f"Path={_desktop_entry_quote(working_dir)}\n"
                "Terminal=false\n"
                "Categories=AudioVideo;Network;\n"
                "StartupNotify=true\n"
            )

            app_launcher = applications / "youtube-downloader.desktop"
            app_launcher.write_text(desktop_entry, encoding="utf-8")
            app_launcher.chmod(0o755)

            # Also put a launcher directly on the user's configured Desktop.
            desktop.mkdir(parents=True, exist_ok=True)
            desktop_shortcut = desktop / f"{APP_TITLE}.desktop"
            desktop_shortcut.write_text(desktop_entry, encoding="utf-8")
            desktop_shortcut.chmod(0o755)
            _mark_linux_shortcut_trusted(desktop_shortcut)

            # Refresh the application menu database when the utility is present.
            update_db = shutil.which("update-desktop-database")
            if update_db:
                try:
                    subprocess.run(
                        [update_db, str(applications)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        timeout=10, check=False
                    )
                except Exception:
                    pass
            return app_launcher.exists() and desktop_shortcut.exists()
        except Exception:
            return False

    if system == "Darwin":
        try:
            # A native .app bundle appears on the macOS Desktop and can be opened
            # from Finder. Prefer pythonw to avoid attaching a Terminal window.
            desktop.mkdir(parents=True, exist_ok=True)
            app = desktop / f"{APP_TITLE}.app"
            contents = app / "Contents"
            macos = contents / "MacOS"
            macos.mkdir(parents=True, exist_ok=True)

            pythonw = Path(sys.executable).with_name("pythonw")
            interpreter = pythonw if pythonw.is_file() else Path(sys.executable)
            launcher = macos / "YouTubeDownloader"
            launcher.write_text(
                "#!/bin/sh\n"
                f"cd {shlex.quote(str(ROOT.resolve()))}\n"
                f"exec {shlex.quote(str(interpreter.resolve()))} "
                f"{shlex.quote(str(script.resolve()))}\n",
                encoding="utf-8",
            )
            launcher.chmod(0o755)

            info_plist = contents / "Info.plist"
            info_plist.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                '<plist version="1.0"><dict>\n'
                '<key>CFBundleName</key><string>YouTube Downloader</string>\n'
                '<key>CFBundleDisplayName</key><string>YouTube Downloader</string>\n'
                '<key>CFBundleIdentifier</key><string>com.tejas.youtube-downloader</string>\n'
                '<key>CFBundleExecutable</key><string>YouTubeDownloader</string>\n'
                '<key>CFBundlePackageType</key><string>APPL</string>\n'
                '<key>CFBundleVersion</key><string>1.0</string>\n'
                '<key>NSHighResolutionCapable</key><true/>\n'
                '</dict></plist>\n',
                encoding="utf-8",
            )
            return launcher.exists() and info_plist.exists()
        except Exception:
            return False

    return False



def uninstall_shortcut() -> bool:
    """Remove only the shortcuts created by this application for the current user."""
    system = platform.system()
    desktop = desktop_directory()
    removed = []
    errors = []

    def remove_path(path: Path) -> None:
        try:
            if path.is_symlink() or path.is_file():
                path.unlink(missing_ok=True)
                removed.append(str(path))
            elif path.is_dir():
                shutil.rmtree(path)
                removed.append(str(path))
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    if system == "Windows":
        remove_path(desktop / f"{APP_TITLE}.lnk")
    elif system == "Linux":
        data_home = Path(os.environ.get(
            "XDG_DATA_HOME", str(Path.home() / ".local" / "share")
        )).expanduser()
        remove_path(data_home / "applications" / "youtube-downloader.desktop")
        remove_path(desktop / f"{APP_TITLE}.desktop")
        update_db = shutil.which("update-desktop-database")
        applications = data_home / "applications"
        if update_db and applications.exists():
            try:
                subprocess.run(
                    [update_db, str(applications)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10, check=False
                )
            except Exception:
                pass
    elif system == "Darwin":
        remove_path(desktop / f"{APP_TITLE}.app")
    else:
        print(f"Shortcut removal is not supported on {system}.")
        return False

    if removed:
        print("Removed shortcut(s):")
        for item in removed:
            print(f"  - {item}")
    else:
        print("No YouTube Downloader shortcuts were found for this user.")

    if errors:
        print("\\nSome shortcuts could not be removed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("\\nShortcut removal completed. The application files and downloaded videos were not deleted.")
    return True

def run_gui(gui_child: bool = False) -> int:
    if not GUI_APP.is_file():
        show_error("Application files missing", "src/main.py is missing from the application folder.")
        return 1
    try:
        import tkinter as tk
        # Verify an actual display can be opened before choosing GUI mode.
        probe = tk.Tk()
        probe.withdraw()
        probe.destroy()
    except Exception as exc:
        # A console-launched run falls back to terminal mode. A windowed
        # shortcut cannot expose a terminal, so explain the issue visibly.
        if sys.stdin and sys.stdin.isatty():
            return run_terminal()
        show_error("GUI unavailable",
                   "A graphical desktop or Tkinter is unavailable.\n\n"
                   f"{exc}\n\nRun start.py from a terminal to use terminal mode.")
        return 1

    if not install_ytdlp_for_gui():
        return 1

    # FFmpeg is optional for launching. The GUI already explains how to install it.
    create_shortcut()

    # On Windows, hand off the GUI to pythonw.exe after first-run checks.
    # This lets the starter process exit so its temporary console window closes.
    # The GUI child is marked with --gui-child to prevent another handoff.
    if platform.system() == "Windows" and not gui_child:
        current_exe = Path(sys.executable)
        pythonw = current_exe.with_name("pythonw.exe")
        if pythonw.is_file() and current_exe.name.lower() != "pythonw.exe":
            try:
                subprocess.Popen(
                    [str(pythonw), str(ROOT / "start.py"), "--gui-child"],
                    cwd=str(ROOT),
                    close_fds=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return 0
            except Exception as exc:
                show_error(
                    "GUI launch warning",
                    "Could not hand off to pythonw.exe. The GUI will continue "
                    f"in the current process.\\n\\n{exc}"
                )

    # Run the GUI in this process. On Windows, the pythonw child has no console.
    sys.path.insert(0, str(ROOT))
    try:
        from src.main import main as gui_main
        gui_main()
        return 0
    except Exception as exc:
        show_error("YouTube Downloader could not start", str(exc))
        return 1


def run_terminal() -> int:
    if not TERMINAL_APP.is_file():
        print("Terminal application file src/terminal.py is missing.", file=sys.stderr)
        return 1
    return subprocess.call([sys.executable, str(TERMINAL_APP)], cwd=str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--terminal", action="store_true",
                        help="start the terminal interface even if a GUI is available")
    parser.add_argument("--gui-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--uninstall-shortcut", action="store_true",
        help="remove this application's desktop and application-menu shortcuts"
    )
    args = parser.parse_args()

    if args.uninstall_shortcut:
        return 0 if uninstall_shortcut() else 1

    if not (ROOT / "src" / "main.py").is_file() or not TERMINAL_APP.is_file():
        show_error("Application files missing",
                   "Keep start.py and the complete src folder together.")
        return 1

    if args.terminal or not has_graphical_session():
        return run_terminal()
    return run_gui(gui_child=args.gui_child)


if __name__ == "__main__":
    raise SystemExit(main())
