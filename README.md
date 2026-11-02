# YouTube Downloader

A cross-platform Python application for downloading individual YouTube videos and playlists. It has a **single smart launcher (`start.py`)** that detects the operating system and whether a graphical display is available.

- **Windows:** uses the graphical interface when Tkinter is available; falls back to terminal mode if the GUI cannot start.
- **Linux:** uses the GUI when a display session is available and Tkinter can open a window; otherwise uses terminal mode.
- **macOS:** attempts the GUI in a graphical session; otherwise uses terminal mode.

The graphical interface is built with Tkinter. Both interfaces use **yt-dlp** for downloads and **FFmpeg/ffprobe** for merging separate video and audio streams.

> **Responsible use:** Download only content you own, have permission to download, or are otherwise legally permitted to download. Respect copyright law, YouTube's terms, and the rights of content creators. This application does not bypass DRM, private-video permissions, or other access controls.

---

## Table of contents

1. [Features](#features)
2. [How automatic mode detection works](#how-automatic-mode-detection-works)
3. [Project structure](#project-structure)
4. [System requirements](#system-requirements)
5. [Installation](#installation)
   - [Windows 10/11](#windows-1011)
   - [Rocky Linux / RHEL / Fedora](#rocky-linux--rhel--fedora)
   - [Ubuntu / Debian](#ubuntu--debian)
   - [Arch Linux](#arch-linux)
   - [macOS](#macos)
6. [Run the application](#run-the-application)
7. [Graphical interface guide](#graphical-interface-guide)
8. [Terminal interface guide](#terminal-interface-guide)
9. [YouTube cookies (optional)](#youtube-cookies-optional)
10. [Download quality and output files](#download-quality-and-output-files)
11. [Updating the application](#updating-the-application)
12. [Troubleshooting](#troubleshooting)
13. [Security and GitHub guidance](#security-and-github-guidance)
14. [Technologies](#technologies)

---

## Features

- Download one video or an entire playlist.
- Quality choices: **8K (4320p), 4K (2160p), 2K (1440p), 1080p, 720p, and 480p**.
- Automatically select the best available video/audio streams up to the selected resolution.
- Merge separate video and audio streams into MP4 when FFmpeg is available.
- Choose a download destination.
- Save a playlist directly in the selected destination or in a new/existing subfolder.
- Optionally use a Netscape-format `cookies.txt` file when YouTube requires an authenticated session.
- Show progress and download messages.
- Avoid overwriting existing files and continue supported interrupted downloads.
- Detect the operating system and graphical display availability.
- Use one `start.py` entry point for GUI and terminal environments.
- Check for `yt-dlp` and offer to install it automatically.
- Check for FFmpeg/ffprobe and offer package-manager installation where supported.
- Create a desktop launcher in supported graphical environments.

**Important:** The chosen resolution is a *maximum*, not a guarantee. If the source does not offer the selected resolution, yt-dlp may choose a lower available format.

## How automatic mode detection works

Run `start.py`; you do not need to choose the interface manually.

| Environment | Selected interface |
|---|---|
| Windows desktop | Tkinter GUI, if it can start |
| Windows without working Tkinter | Terminal fallback |
| Linux with `DISPLAY` or `WAYLAND_DISPLAY` and working Tkinter | Tkinter GUI |
| Linux SSH/headless/terminal-only session | Terminal interface |
| macOS graphical session with working Tkinter | Tkinter GUI |
| macOS terminal-only session | Terminal interface |

The starter tests whether Tkinter can actually create a window. Merely having the Tkinter Python module installed is not enough if the current process has no usable display.

**Terminal mode does not require Tkinter or a desktop environment.** This is useful on Rocky Linux servers, SSH sessions, and other headless Linux machines.

---

## Project structure

```text
YouTube-Downloader-GUI/
├── src/
│   ├── main.py          # Tkinter graphical interface
│   └── terminal.py      # Interactive terminal interface
├── start.py             # OS/display detection, dependency checks and launcher
├── run_windows.bat      # Windows convenience launcher
├── run_unix.sh          # Linux/macOS convenience launcher
├── requirements.txt     # Python package requirements
├── README.md            # Project documentation
└── .gitignore           # Excludes cookies, virtual environments and temp files
```

Keep `start.py`, `src/main.py`, and `src/terminal.py` in this structure. Do not move the Python files independently.

## System requirements

- Windows 10/11, a supported Linux distribution, or macOS.
- Python **3.10 or newer recommended**.
- Internet connection.
- `pip` (normally included with Python).
- `yt-dlp` Python package.
- FFmpeg and ffprobe on `PATH` (strongly recommended; required for reliable merging of separate video/audio streams).
- Tkinter and a graphical display **only for GUI mode**.
- A terminal capable of interactive keyboard input for terminal mode.

The starter can install `yt-dlp` with pip and can offer to install FFmpeg through a detected package manager. Python itself must already be installed. Tkinter is an operating-system/Python distribution component and may need to be installed separately for GUI use.

---

## Installation

### Windows 10/11

#### 1. Install Python

1. Download Python from <https://www.python.org/downloads/windows/>.
2. Run the installer.
3. Select **Add Python to PATH**.
4. Ensure the Tcl/Tk support option is selected (usually included in the standard python.org installer).
5. Open a new Command Prompt and verify:

```cmd
python --version
python -m pip --version
```

If `python` is not recognized, reopen Command Prompt after installation or repair the Python PATH configuration. The `python3` command is not required if `python` works.

#### 2. Install FFmpeg

Recommended with Windows Package Manager (`winget`):

```powershell
winget install --id Gyan.FFmpeg -e
```

Alternatively, install a Windows FFmpeg build from <https://ffmpeg.org/download.html> and add the directory containing `ffmpeg.exe` and `ffprobe.exe` to the system/user `PATH`.

Close and reopen Command Prompt after changing PATH. Verify:

```cmd
ffmpeg -version
ffprobe -version
```

#### 3. Download and extract the project

Download the project ZIP from the repository or release page, then extract it. Open Command Prompt in the extracted project directory.

Example:

```cmd
cd %USERPROFILE%\Downloads\YouTube-Downloader-GUI
```

If Windows adds a suffix such as `(1)` to the extracted folder name, use the actual folder path.

#### 4. Install Python dependencies

```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The smart starter can also offer to install `yt-dlp` if it is missing.

### Rocky Linux / RHEL / Fedora

#### 1. Install Python, pip and (optional) Tkinter

For Rocky Linux 10 / RHEL 10 / Fedora-family systems:

```bash
sudo dnf install -y python3 python3-pip
```

For a graphical desktop, install Tkinter:

```bash
sudo dnf install -y python3-tkinter
```

On Rocky Linux/RHEL, the package name is generally `python3-tkinter`. Terminal mode does not need this package.

Verify:

```bash
python3 --version
python3 -m pip --version
```

#### 2. Install FFmpeg

FFmpeg may not be available in the default Rocky Linux/RHEL repositories. On Rocky Linux, one common route is to enable EPEL and RPM Fusion Free, then install FFmpeg. Check the current repository instructions for your exact Rocky/RHEL release before enabling third-party repositories.

Typical Rocky Linux commands:

```bash
sudo dnf install -y epel-release
sudo dnf install -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-10.noarch.rpm
sudo dnf install -y ffmpeg ffmpeg-free
```

The RPM Fusion release package shown above is for EL 10. Use the matching RPM Fusion package for a different major release.

On Fedora, try:

```bash
sudo dnf install -y ffmpeg
```

Verify:

```bash
ffmpeg -version
ffprobe -version
```

If DNF reports `No match for argument: ffmpeg`, the required repository is not enabled or the package name/source differs for that release. Do not repeatedly rerun the same install command; configure the appropriate repository first.

#### 3. Download and extract the project

Extract the ZIP and enter the project directory. For example:

```bash
cd ~/Downloads/YouTube-Downloader-GUI
```

Use the actual extraction path if it differs.

#### 4. Install Python dependencies

Recommended: create a virtual environment so pip packages are isolated from system Python.

```bash
sudo dnf install -y python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `venv` support is missing, install the matching Python venv package provided by your distribution, or follow its Python packaging guidance.

### Ubuntu / Debian

#### 1. Install Python, pip, venv and (optional) Tkinter

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

For GUI mode:

```bash
sudo apt install -y python3-tk
```

Terminal mode does not require Tkinter.

#### 2. Install FFmpeg

```bash
sudo apt install -y ffmpeg
```

Verify:

```bash
ffmpeg -version
ffprobe -version
```

#### 3. Install the project

Extract the ZIP, enter the project directory, and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Arch Linux

Install the system packages:

```bash
sudo pacman -Syu
sudo pacman -S --needed python python-pip tk ffmpeg
```

Then extract the project, enter its directory, and install the Python requirement:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS

#### 1. Install Python

Install Python from <https://www.python.org/downloads/macos/> or use your preferred package manager. The Python build must include Tcl/Tk support for GUI mode.

Verify:

```bash
python3 --version
python3 -m pip --version
```

#### 2. Install FFmpeg

With Homebrew:

```bash
brew install ffmpeg
```

Verify:

```bash
ffmpeg -version
ffprobe -version
```

#### 3. Install the project dependencies

Extract the ZIP, enter the project directory, and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Run the application

Run the starter from the **project root directory**.

### Windows

```cmd
python start.py
```

Or double-click:

```text
run_windows.bat
```

Windows normally opens the GUI. If Tkinter cannot create a window, the starter switches to terminal mode.

### Linux

```bash
python3 start.py
```

Or make the helper executable and run it:

```bash
chmod +x run_unix.sh
./run_unix.sh
```

- From a Linux desktop terminal with a working display, the GUI should open.
- From an SSH session or terminal-only server with no display, terminal mode starts automatically.

### macOS

```bash
python3 start.py
```

Or:

```bash
chmod +x run_unix.sh
./run_unix.sh
```

### Direct launch (advanced)

You can start an interface directly, bypassing automatic detection:

```bash
python src/main.py       # GUI only; requires Tkinter and a working display
python src/terminal.py   # Terminal interface
```

On Windows, use `python` rather than `python3` if that is the command configured by your Python installation.

---

## Graphical interface guide

When the starter detects a working graphical environment, the Tkinter window opens.

1. **Download type:** choose `Single video` or `Entire playlist`.
2. **YouTube URL:** paste the video or playlist URL.
3. **Maximum quality:** choose 8K, 4K, 2K, 1080p, 720p, or 480p.
4. **Download destination:** select an existing folder or use **Browse**.
5. **Playlist folder options:** for playlists, save directly in the destination or create/use a subfolder.
6. **YouTube cookies (optional):** enter or browse to a Netscape-format cookies file if needed.
7. Select **Start Download**.
8. Watch the progress bar, status text and activity log.
9. Use **Clear Log** to clear the visible activity messages.

The destination folder must already exist. If you select the playlist subfolder option, the application creates that subfolder under the destination.

The default destination is `~/Downloads` if it exists; otherwise it uses the user's home directory.

## Terminal interface guide

When no usable graphical display is detected, `start.py` launches an interactive text menu.

The terminal flow asks for:

1. Download type:
   - `1` — Single video
   - `2` — Entire playlist
2. YouTube video or playlist URL.
3. Maximum quality:
   - `1` — 8K (4320p)
   - `2` — 4K (2160p)
   - `3` — 2K (1440p)
   - `4` — 1080p
   - `5` — 720p
   - `6` — 480p
4. Download destination (defaults to `~/Downloads` if it exists, otherwise the home directory).
5. For a playlist, save directly in the destination or create/use a subfolder.
6. Optional cookies file path. Press Enter to skip.
7. The download begins and progress is printed in the terminal.

The selected destination must already exist. The playlist subfolder, if selected, is created automatically.

To cancel a running terminal download, press `Ctrl+C`.

---

## YouTube cookies (optional)

YouTube may sometimes request sign-in or show a bot-verification challenge. If you need to use your own authenticated session, export your own cookies in Netscape `cookies.txt` format and provide the file path in the application.

One possible browser workflow:

1. Sign in to YouTube in your browser.
2. Use a trusted cookies-export extension that explicitly exports Netscape `cookies.txt` format, such as **Get cookies.txt LOCALLY**:
   <https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc>
3. Visit <https://www.youtube.com/> while signed in.
4. Export the cookies for YouTube in Netscape format.
5. Save the file as `youtube-cookies.txt`.
6. In the GUI, browse to the file. In terminal mode, enter its full path when prompted.

Suggested location:

- Windows: `%USERPROFILE%\Downloads\youtube-cookies.txt`
- Linux/macOS: `~/Downloads/youtube-cookies.txt`

If the file is stored elsewhere, enter or select its actual path.

**Cookies are sensitive authentication credentials.**
- Never share the file or paste its contents into a chat.
- Never commit it to Git or upload it to GitHub.
- Do not include it in screenshots or public issue reports.
- Keep it on a trusted device and delete it when no longer needed.
- If exposed, revoke/sign out the affected browser session and create a new export only if needed.

Cookies do not guarantee that a download will succeed. The account must have legitimate access to the content, and YouTube may still reject requests.

---

## Download quality and output files

The application asks yt-dlp for the best video stream at or below the selected height and the best available audio stream. If separate streams are downloaded, FFmpeg merges them.

Quality options:

| Option | Maximum height |
|---|---:|
| 8K | 4320p |
| 4K | 2160p |
| 2K | 1440p |
| Full HD | 1080p |
| HD | 720p |
| SD | 480p |

Typical output filename:

```text
Video Title [1080p] [VIDEO_ID].mp4
```

The actual output extension/container can depend on the source formats and post-processing. FFmpeg/ffprobe should be installed and available on `PATH` for reliable merging.

The application avoids overwriting existing files and enables yt-dlp's continued-download behavior. A partial download may remain if a download is interrupted.

---

## Updating the application

### Update yt-dlp

Activate the project's virtual environment if you created one, then run:

```bash
python -m pip install --upgrade yt-dlp
```

On Linux/macOS, if your Python command is `python3` and no virtual environment is active:

```bash
python3 -m pip install --user --upgrade yt-dlp
```

If using a virtual environment, `python -m pip` is preferred after activation.

### Update the project

Download/extract the latest project version, keeping any personal cookies file outside the project folder. Do not overwrite your cookie export with a public project file.

---

## Troubleshooting

### `python` is not recognized (Windows)

- Reinstall Python from <https://www.python.org/downloads/windows/>.
- Select **Add Python to PATH** during installation.
- Open a new Command Prompt.
- Verify with `python --version`.
- `python3` may not be configured on Windows; use `python`.

### `No module named yt_dlp`

Activate the virtual environment and install the requirements:

```bash
python -m pip install -r requirements.txt
```

Or install/update yt-dlp directly:

```bash
python -m pip install --upgrade yt-dlp
```

### `No module named tkinter`

Tkinter is needed only for GUI mode.

- Rocky Linux / Fedora:

```bash
sudo dnf install -y python3-tkinter
```

- Ubuntu / Debian:

```bash
sudo apt install -y python3-tk
```

- Windows: use a Python installation that includes Tcl/Tk support.
- macOS: use a Python distribution that includes Tcl/Tk support.

If you are on a headless Linux server, you do not need Tkinter. Run the smart starter:

```bash
python3 start.py
```

It should select terminal mode when no display is available.

### `TclError: no display name and no $DISPLAY environment variable`

This means the GUI was launched without access to a graphical display.

Use the smart starter rather than launching `src/main.py` directly:

```bash
python3 start.py
```

If you intend to use the GUI over SSH, configure a working X11/Wayland forwarding setup and a display server on the client. Otherwise, use terminal mode.

### GUI does not open on Windows

- Confirm you installed Python with Tcl/Tk support.
- Test Tkinter:

```cmd
python -m tkinter
```

- If no test window opens, repair/reinstall Python with Tcl/Tk support.
- Run `python start.py` again; the starter should use terminal mode if GUI initialization fails.

### `ffmpeg` or `ffprobe` not found

Verify:

```bash
ffmpeg -version
ffprobe -version
```

If either command is missing, install FFmpeg using the instructions for your operating system and ensure its executable directory is on `PATH`. Close and reopen the terminal after changing PATH.

On Rocky Linux/RHEL, `dnf install ffmpeg` may return `No match for argument`. Enable a suitable repository such as RPM Fusion for the matching EL major version, then retry the package installation.

If the starter's automatic FFmpeg installation fails, install FFmpeg manually and run `start.py` again.

### `Sign in to confirm you're not a bot`

- Check that you can open YouTube normally in your browser.
- If authentication is legitimately required, export a fresh Netscape-format cookies file from your own signed-in browser session and select/provide its path.
- Update yt-dlp:

```bash
python -m pip install --upgrade yt-dlp
```

- Wait and retry later if YouTube is temporarily rate-limiting requests.
- Do not share cookies or attempt to bypass access restrictions.

### `ERROR: Destination folder does not exist`

Create the destination directory first or select an existing directory. In GUI mode, use **Browse**. In terminal mode, enter a valid existing directory path.

### Playlist subfolder name is invalid

Use a simple folder name. Do not include path separators, reserved characters, or control characters. The application creates the folder under the selected destination.

### Requested resolution is not available

The quality setting is a maximum. The source may not have that resolution, so yt-dlp can select a lower available format.

### Video is unavailable

The video may be private, deleted, region-restricted, age-restricted, removed, or unavailable to the signed-in account. The downloader cannot grant access to content the account is not authorized to view.

### Download was interrupted

Run the download again using the same destination. The application enables yt-dlp's continued-download behavior, but resuming depends on the source and the partial files yt-dlp retained.

---

## Security and GitHub guidance

The included `.gitignore` excludes common cookie files, Python bytecode, virtual environments and temporary download fragments.

Before committing changes, check staged and untracked files:

```bash
git status
```

Never commit:

- `youtube-cookies.txt`
- `cookies.txt`
- Browser profile data
- Passwords, tokens, API keys, or other authentication material
- Personal downloads

If an authentication cookie is accidentally pushed to a public repository, deleting it in a later commit is not sufficient. Revoke the exposed session and remove the secret from repository history as appropriate.

## Technologies

- **Python 3** — application and launcher
- **Tkinter / ttk** — graphical interface
- **yt-dlp** — video and playlist download engine
- **FFmpeg / ffprobe** — stream merging and media processing
- **threading / queue** — keep the GUI responsive while downloading
- **platform / os / subprocess** — operating-system, display and dependency checks

## Author

**Tejas Aher**  
GitHub: <https://github.com/tejaskaher0>

---

*If you find this project useful, consider starring the repository.*
