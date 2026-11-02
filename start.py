#!/usr/bin/env python3
"""Cross-platform setup and smart launcher for YouTube Downloader.

Windows prefers the Tkinter GUI. Linux/macOS use the GUI when a graphical
session is available and otherwise start the terminal interface. The
terminal interface does not require Tkinter or a desktop environment.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GUI_APP = ROOT / "src" / "main.py"
TERMINAL_APP = ROOT / "src" / "terminal.py"


def say(message: str) -> None:
    print(f"[YouTube Downloader] {message}", flush=True)


def ask(message: str) -> bool:
    try:
        return input(f"{message} [Y/n]: ").strip().lower() in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def wait_exit() -> None:
    try:
        input("Press Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        pass


def has_graphical_session() -> bool:
    """Detect whether the current process can open a native desktop window."""
    system = platform.system()
    if system == "Windows":
        # Windows desktop sessions do not use DISPLAY/WAYLAND_DISPLAY.
        return True
    if system == "Darwin":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.environ.get("TERM_PROGRAM"))
    if system == "Linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def tkinter_works() -> tuple[bool, str]:
    """Test Tkinter and an actual display, not just whether the module imports."""
    try:
        import tkinter as tk
        test_root = tk.Tk()
        test_root.withdraw()
        test_root.destroy()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def check_ytdlp() -> bool:
    if importlib.util.find_spec("yt_dlp") is None:
        say("yt-dlp is missing. Installing it with pip...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        if result.returncode != 0:
            say("Automatic installation failed. Run: python -m pip install --upgrade yt-dlp")
            return False
    importlib.invalidate_caches()
    try:
        import yt_dlp
        say(f"yt-dlp ready: {yt_dlp.version.__version__}")
        return True
    except Exception as exc:
        say(f"Could not import yt-dlp: {exc}")
        return False


def ffmpeg_install_commands() -> list[tuple[str, list[str]]]:
    system = platform.system()
    if system == "Windows":
        commands = []
        if shutil.which("winget"):
            commands.append(("winget", ["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-package-agreements", "--accept-source-agreements"]))
        if shutil.which("choco"):
            commands.append(("Chocolatey", ["choco", "install", "ffmpeg", "-y"]))
        if shutil.which("scoop"):
            commands.append(("Scoop", ["scoop", "install", "ffmpeg"]))
        return commands
    if system == "Darwin":
        return [("Homebrew", ["brew", "install", "ffmpeg"])] if shutil.which("brew") else []

    privilege = [] if hasattr(os, "geteuid") and os.geteuid() == 0 else ["sudo"]
    if shutil.which("apt-get"):
        return [("APT update", privilege + ["apt-get", "update"]), ("APT install", privilege + ["apt-get", "install", "-y", "ffmpeg"])]
    if shutil.which("dnf"):
        return [("DNF", privilege + ["dnf", "install", "-y", "ffmpeg"])]
    if shutil.which("yum"):
        return [("YUM", privilege + ["yum", "install", "-y", "ffmpeg"])]
    if shutil.which("pacman"):
        return [("Pacman", privilege + ["pacman", "-Sy", "--noconfirm", "ffmpeg"])]
    if shutil.which("zypper"):
        return [("Zypper", privilege + ["zypper", "--non-interactive", "install", "ffmpeg"])]
    return []


def ensure_ffmpeg() -> bool:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        say("FFmpeg and ffprobe found.")
        return True
    say("FFmpeg/ffprobe are missing. They are needed to merge separate video and audio streams.")
    commands = ffmpeg_install_commands()
    if not commands:
        say("No supported package manager found. Install FFmpeg manually: https://ffmpeg.org/download.html")
        return False
    if not ask("Try installing FFmpeg using the detected package manager?"):
        say("Skipped FFmpeg installation. Downloads may not merge correctly until FFmpeg is installed.")
        return False
    for label, command in commands:
        say("Running " + " ".join(command))
        try:
            result = subprocess.run(command)
        except OSError as exc:
            say(f"Could not start {label}: {exc}")
            return False
        if result.returncode != 0:
            say(f"{label} failed with exit code {result.returncode}.")
            if platform.system() == "Linux" and platform.freedesktop_os_release().get("ID", "") in {"rocky", "rhel", "almalinux", "ol"}:
                say("On Rocky/RHEL, FFmpeg may require RPM Fusion repositories before installing: ffmpeg.org/download.html")
            return False
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        say("FFmpeg installation verified.")
        return True
    say("FFmpeg may be installed, but this process cannot see it on PATH yet. Reopen the terminal and rerun.")
    return False


def create_shortcut() -> None:
    """Create a desktop launcher only for graphical sessions."""
    desktop = Path.home() / "Desktop"
    system = platform.system()
    if system == "Windows":
        if not desktop.is_dir():
            return
        ps = shutil.which("powershell") or shutil.which("pwsh")
        if not ps:
            return
        shortcut = desktop / "YouTube Downloader.lnk"
        if shortcut.exists():
            return
        def q(value: str) -> str:
            return value.replace("'", "''")
        command = (
            "$w=New-Object -ComObject WScript.Shell;"
            f"$s=$w.CreateShortcut('{q(str(shortcut))}');"
            f"$s.TargetPath='{q(sys.executable)}';"
            f"$s.Arguments='\"{q(str(Path(__file__).resolve()))}\"';"
            f"$s.WorkingDirectory='{q(str(ROOT))}';$s.Save()"
        )
        subprocess.run([ps, "-NoProfile", "-Command", command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif system == "Linux":
        apps = Path.home() / ".local" / "share" / "applications"
        try:
            apps.mkdir(parents=True, exist_ok=True)
            launcher = apps / "youtube-downloader.desktop"
            launcher.write_text(
                "[Desktop Entry]\nType=Application\nName=YouTube Downloader\n"
                f"Exec={sys.executable} {Path(__file__).resolve()}\nPath={ROOT}\n"
                "Terminal=false\nCategories=AudioVideo;Network;\n", encoding="utf-8")
            launcher.chmod(0o755)
            if desktop.is_dir():
                copy = desktop / "YouTube Downloader.desktop"
                shutil.copy2(launcher, copy)
                copy.chmod(0o755)
        except OSError as exc:
            say(f"Could not create Linux desktop shortcut: {exc}")
    elif system == "Darwin" and desktop.is_dir():
        launcher = desktop / "YouTube Downloader.command"
        if not launcher.exists():
            launcher.write_text(
                "#!/bin/bash\n"
                f'cd "{ROOT}"\n'
                f'exec "{sys.executable}" "{Path(__file__).resolve()}"\n', encoding="utf-8")
            launcher.chmod(0o755)


def main() -> int:
    print("=" * 62)
    print("             YOUTUBE DOWNLOADER - SMART STARTER")
    print("=" * 62)
    if sys.version_info < (3, 10):
        say("Python 3.10 or newer is recommended. Current: " + sys.version.split()[0])
        if not ask("Continue anyway?"):
            return 1

    if not TERMINAL_APP.is_file() or not GUI_APP.is_file():
        say("Application files are missing. Keep start.py, src/main.py and src/terminal.py together.")
        wait_exit()
        return 1

    system = platform.system()
    graphical = has_graphical_session()
    say(f"Detected operating system: {platform.system()} ({platform.release()})")
    say(f"Display session: {'GUI/display detected' if graphical else 'terminal-only / no display detected'}")

    use_gui = graphical
    if graphical:
        works, error = tkinter_works()
        if works:
            say("Tkinter GUI is available.")
        else:
            say(f"GUI cannot start ({error}). Switching to terminal mode.")
            if system == "Windows":
                say("Install/reinstall Python with Tcl/Tk support to use the Windows GUI.")
            use_gui = False
    else:
        say("Starting terminal-only mode. Tkinter and a desktop environment are not required.")

    if not check_ytdlp():
        wait_exit()
        return 1
    ensure_ffmpeg()

    if use_gui:
        create_shortcut()
        say("Launching the graphical downloader...")
        # Do not hide/detach the launcher until the GUI survives startup.
        popen_kwargs = {
            "cwd": str(ROOT),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if system == "Windows":
            popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            popen_kwargs["startupinfo"] = startupinfo
        else:
            # Keep the GUI alive independently when the launcher exits.
            popen_kwargs["start_new_session"] = True

        try:
            gui_process = subprocess.Popen([sys.executable, str(GUI_APP)], **popen_kwargs)
        except OSError as exc:
            say(f"Could not launch the GUI: {exc}")
            wait_exit()
            return 1

        time.sleep(1.0)
        exit_code = gui_process.poll()
        if exit_code is not None:
            say(f"The GUI exited during startup (exit code {exit_code}).")
            say("The launcher terminal will remain available for troubleshooting.")
            wait_exit()
            return exit_code or 1

        if system == "Windows":
            try:
                import ctypes
                ctypes.windll.kernel32.FreeConsole()
            except Exception as exc:
                say(f"Could not detach the launcher console: {exc}")
                wait_exit()
                return 1

        # Linux/macOS terminal windows belong to their terminal emulator and
        # cannot be portably minimized by a child process. The GUI is detached;
        # the launcher exits and returns control to the shell.
        return 0

    say("Launching the terminal downloader (terminal will remain visible)...")
    return subprocess.call([sys.executable, str(TERMINAL_APP)], cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
