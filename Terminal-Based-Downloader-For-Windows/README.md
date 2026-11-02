# YouTube Downloader

A simple Windows-based YouTube Video and Playlist Downloader built using **yt-dlp, FFmpeg, and PowerShell**, with a convenient Batch (`.bat`) launcher.

Download individual YouTube videos or entire playlists in different video resolutions, including 8K, 4K, 2K, 1080p, 720p, and 480p.

## Features

- Download individual YouTube videos.
- Download complete YouTube playlists.
- Select video quality before downloading.
- Supports multiple resolutions:
  - 8K (4320p)
  - 4K (2160p)
  - 2K (1440p)
  - Full HD (1080p)
  - HD (720p)
  - SD (480p)
- Automatically merges video and audio using FFmpeg.
- Displays download progress.
- Shows playlist download statistics.
- Supports creating a separate folder for each playlist.
- Uses YouTube cookies for authenticated downloads.
- Prevents overwriting existing downloaded files.
- Simple menu-driven interface using a `.bat` file.

## Project Structure

Keep both files in the same directory:

```text
YouTube-Downloader/
│
├── youtube_downloader.bat
├── youtube_downloader.ps1
└── README.md
```

- **youtube_downloader.bat** – Launches the PowerShell downloader.
- **youtube_downloader.ps1** – Contains the download functionality, menus, quality selection, and progress tracking.
- **README.md** – Project documentation.

## Requirements

Before using the downloader, install the following:

| Software | Purpose |
|---|---|
| Windows 10 / 11 | Operating system |
| yt-dlp | Extracts and downloads YouTube videos |
| FFmpeg | Merges video and audio |
| Brave Browser | Used to sign in to YouTube and export cookies |
| Get cookies.txt LOCALLY | Exports YouTube cookies |

## Installation

### Step 1 – Install yt-dlp

yt-dlp is the command-line program responsible for downloading videos.

**Using Windows Package Manager (winget):**

Open PowerShell or Command Prompt and execute:

```powershell
winget install yt-dlp.yt-dlp
```

Verify the installation:

```powershell
yt-dlp --version
```

Official GitHub repository: https://github.com/yt-dlp/yt-dlp

### Step 2 – Install FFmpeg

FFmpeg is required to merge separately downloaded video and audio streams into a single MP4 file.

Download FFmpeg:

https://ffmpeg.org/download.html

After installation, make sure FFmpeg is added to your Windows PATH environment variable.

Verify the installation:

```powershell
ffmpeg -version
```

Also verify:

```powershell
ffprobe -version
```

### Step 3 – Configure YouTube Cookies

YouTube may require authentication to download certain videos or playlists. The downloader uses a cookies file to authenticate requests.

If you encounter errors such as:

```text
Sign in to confirm you're not a bot.
```

Follow these steps to export fresh YouTube cookies.

#### 3.1 – Install the Browser Extension

Install the following Chrome-compatible extension:

**Get cookies.txt LOCALLY**

Extension link:

https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

You can use this extension in Brave Browser.

#### 3.2 – Sign in to YouTube using Brave

1. Open Brave Browser.
2. Visit https://www.youtube.com/.
3. Sign in using your Google account.
4. Make sure YouTube is accessible and your account is signed in.
5. Keep YouTube open.

#### 3.3 – Export YouTube Cookies

1. Open the **Get cookies.txt LOCALLY** extension.
2. Make sure you are on the YouTube website.
3. Export the cookies for YouTube.
4. Save the exported cookies file.

#### 3.4 – Rename and Move the Cookies File

Rename the exported file to:

```text
youtube-cookies.txt
```

Move it into your Windows Downloads folder.

The final location must be:

```text
C:\Users\<YourUsername>\Downloads\youtube-cookies.txt
```

For example:

```text
C:\Users\ahert\Downloads\youtube-cookies.txt
```

**Important:** The filename and location must match the path configured in the PowerShell script.

The cookies file contains authentication information. Never share it publicly, upload it to GitHub, or commit it to your repository.

## Usage

### Step 1 – Open the Project

Navigate to the folder containing the downloader files.

### Step 2 – Launch the Downloader

Double-click:

```text
youtube_downloader.bat
```

The Batch file automatically launches the PowerShell script.

### Step 3 – Select Download Type

The main menu provides the following options:

```text
========================================
        YOUTUBE DOWNLOADER
========================================

1. Download Single Video
2. Download Entire Playlist
3. Exit

Enter your choice:
```

Choose the required option.

### Step 4 – Select Video Quality

Choose your preferred video resolution:

```text
========================================
          SELECT VIDEO QUALITY
========================================

1. 8K  (4320p)
2. 4K  (2160p)
3. 2K  (1440p)
4. 1080p
5. 720p
6. 480p
0. Back

Enter your choice:
```

The downloader selects the best available video and audio streams within your chosen maximum resolution.

**Note:** The actual resolution depends on the quality available on YouTube for that video.

### Step 5 – Enter YouTube URL

Copy the YouTube video or playlist URL and paste it into the downloader.

Example video URL:

```text
https://www.youtube.com/watch?v=VIDEO_ID
```

Example playlist URL:

```text
https://www.youtube.com/playlist?list=PLAYLIST_ID
```

### Step 6 – Choose Playlist Destination

When downloading a playlist, you can select where to save it:

```text
========================================
       SELECT DOWNLOAD LOCATION
========================================

1. Default Folder
2. Create New Folder

Enter your choice:
```

**Option 1 – Default Folder**

Downloads the playlist directly into:

```text
E:\Downloads
```

**Option 2 – Create New Folder**

Enter a folder name, for example:

```text
Jass
```

The downloader creates the folder automatically:

```text
E:\Downloads\Jass
```

All videos from that playlist will be saved inside the selected folder.

## Download Location

By default, downloaded videos are stored in:

```text
E:\Downloads
```

Example folder structure:

```text
E:\
└── Downloads\
    │
    ├── Video Title [720p] [VIDEO_ID].mp4
    │
    ├── Jass\
    │   ├── Video 01 [720p] [VIDEO_ID].mp4
    │   ├── Video 02 [720p] [VIDEO_ID].mp4
    │   └── Video 03 [720p] [VIDEO_ID].mp4
    │
    └── Music Playlist\
        ├── Video 01 [1080p] [VIDEO_ID].mp4
        └── Video 02 [1080p] [VIDEO_ID].mp4
```

## Troubleshooting

### 1. Sign in to confirm you're not a bot

**Error:**

```text
ERROR: [youtube] Sign in to confirm you're not a bot.
```

**Solution:**

This usually means YouTube is not accepting the current cookies or is requesting additional authentication.

1. Open Brave Browser.
2. Sign in to your YouTube account.
3. Install the **Get cookies.txt LOCALLY** extension if it is not already installed.
4. Visit YouTube while signed in.
5. Export fresh YouTube cookies using the extension.
6. Rename the exported file to `youtube-cookies.txt`.
7. Replace the existing file in your Downloads folder:

```text
C:\Users\<YourUsername>\Downloads\youtube-cookies.txt
```

8. Restart the downloader and try again.

Extension:

https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

**Tip:** If the problem continues, make sure your YouTube account is not displaying a verification or security challenge. Update yt-dlp and try again later if YouTube is temporarily restricting requests.

### 2. yt-dlp is not recognized

**Error:**

```text
'yt-dlp' is not recognized as an internal or external command.
```

**Solution:**

Install yt-dlp and ensure its installation directory is included in the Windows PATH environment variable.

Verify:

```powershell
yt-dlp --version
```

### 3. FFmpeg is not recognized

**Error:**

```text
ERROR: ffmpeg not found
```

**Solution:**

Install FFmpeg and add its `bin` directory to the Windows PATH environment variable.

Verify:

```powershell
ffmpeg -version
```

### 4. Cookies file not found

**Error:**

```text
Cookies file not found.
```

**Solution:**

Check whether the file exists in:

```text
C:\Users\<YourUsername>\Downloads\youtube-cookies.txt
```

Make sure the filename is exactly:

```text
youtube-cookies.txt
```

Also ensure Windows has not saved it as:

```text
youtube-cookies.txt.txt
```

### 5. Requested video quality is unavailable

If a video does not support the selected resolution, yt-dlp downloads the best available quality up to the selected maximum.

For example, if you select 4K but the video is available only in 1080p, the downloader can select 1080p instead.

### 6. Existing file is not downloaded again

The downloader uses an option to prevent overwriting existing files.

If a video has already been downloaded, the existing file is protected from being overwritten.

## Updating yt-dlp

It is recommended to keep yt-dlp updated because YouTube frequently changes its extraction behavior.

For standalone yt-dlp installations:

```powershell
yt-dlp -U
```

If installed through winget:

```powershell
winget upgrade yt-dlp.yt-dlp
```

Check the installed version:

```powershell
yt-dlp --version
```

## Important Notes

- An active internet connection is required.
- YouTube cookies must be valid and may need to be exported again.
- Some videos may be private, restricted, deleted, or unavailable.
- Download quality depends on the source video's available formats.
- FFmpeg must be installed and accessible through PATH.
- The default download destination is `E:\Downloads`.
- Do not share your `youtube-cookies.txt` file.
- Use this downloader responsibly and respect copyright laws and YouTube's terms of service.

## Technologies Used

- **Batch Script (.bat)** – Application launcher.
- **PowerShell** – Download automation and menu interface.
- **yt-dlp** – YouTube video and playlist extraction.
- **FFmpeg** – Video and audio merging.
- **Brave Browser** – YouTube authentication and cookie export.

## Author

**Tejas Aher**

GitHub: https://github.com/tejaskaher0

---

⭐ If you find this project useful, consider giving the repository a star on GitHub!


