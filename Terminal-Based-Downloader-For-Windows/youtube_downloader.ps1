
# ============================================================
#                  YOUTUBE DOWNLOADER
# ============================================================

$ErrorActionPreference = "Continue"

# ============================================================
# CONFIGURATION
# ============================================================

$YtDlp = "yt-dlp"
$Cookie = "C:\Users\ahert\Downloads\youtube-cookies.txt"
$Destination = "E:\Downloads"

$Host.UI.RawUI.WindowTitle = "YouTube Downloader"

# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

function Show-Header {
    Clear-Host

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "              YOUTUBE DOWNLOADER" -ForegroundColor Yellow
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Message {
    param(
        [string]$Message,
        [string]$Color = "White"
    )

    Write-Host $Message -ForegroundColor $Color
}

function Show-ProgressStatus {
    param(
        [double]$Percent,
        [int]$Total,
        [int]$Downloaded,
        [int]$Skipped,
        [string]$CurrentVideo
    )

    $Remaining = [math]::Max(0, $Total - $Downloaded - $Skipped)

    $VideoNumber = $Downloaded + $Skipped + 1

    if ($CurrentVideo -match '^\d+$') {
        $VideoNumber = [int]$CurrentVideo
    }

    $Status = "Video $VideoNumber of $Total | Downloaded: $Downloaded | Skipped: $Skipped | Remaining: $Remaining | $([math]::Round($Percent))%"

    Write-Progress `
        -Activity "DOWNLOADING PLAYLIST" `
        -Status $Status `
        -PercentComplete $Percent
}

# ============================================================
# CHECK REQUIREMENTS
# ============================================================

if (-not (Get-Command $YtDlp -ErrorAction SilentlyContinue)) {
    Show-Message "[ERROR] yt-dlp is not installed or not in PATH." "Red"
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Get-Command "ffmpeg" -ErrorAction SilentlyContinue)) {
    Show-Message "[ERROR] FFmpeg is not installed or not in PATH." "Red"
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $Cookie)) {
    Show-Message "[ERROR] YouTube cookies file not found." "Red"
    Show-Message $Cookie "Yellow"
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
}
catch {
    Show-Message "[ERROR] Cannot create destination folder." "Red"
    Read-Host "Press Enter to exit"
    exit 1
}

# ============================================================
# MAIN MENU
# ============================================================

while ($true) {

    # Reset destination for every new download
    $DownloadDestination = $Destination

    Show-Header

    Show-Message " Destination : $Destination" "Gray"

    Write-Host ""
    Show-Message "  1. Download Single Video" "Green"
    Show-Message "  2. Download Entire Playlist" "Green"
    Show-Message "  3. Exit" "Red"

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan

    $Choice = Read-Host "Select an option"

    switch ($Choice) {
        "1" {
            $PlaylistFlag = "--no-playlist"
            $IsPlaylist = $false
        }

        "2" {
            $PlaylistFlag = "--yes-playlist"
            $IsPlaylist = $true
        }

        "3" {
            Show-Message "Thank you for using YouTube Downloader!" "Cyan"
            exit 0
        }

        default {
            Show-Message "Invalid selection!" "Red"
            Start-Sleep -Seconds 2
            continue
        }
    }

    # ========================================================
    # URL INPUT
    # ========================================================

    Show-Header

    $Url = Read-Host "Enter YouTube URL"

    if ([string]::IsNullOrWhiteSpace($Url)) {
        Show-Message "[ERROR] URL cannot be empty." "Red"
        Start-Sleep -Seconds 2
        continue
    }

    # ========================================================
    # QUALITY MENU
    # ========================================================

    Show-Header

    Show-Message "SELECT DOWNLOAD QUALITY" "Yellow"

    Write-Host ""
    Show-Message "  1. 8K     - 4320p" "Green"
    Show-Message "  2. 4K     - 2160p" "Green"
    Show-Message "  3. 2K     - 1440p" "Green"
    Show-Message "  4. 1080p" "Green"
    Show-Message "  5. 720p" "Green"
    Show-Message "  6. 480p" "Green"
    Show-Message "  0. Back to Main Menu" "Red"

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan

    $Quality = Read-Host "Select quality"

    $MaxHeight = switch ($Quality) {
        "1" { 4320 }
        "2" { 2160 }
        "3" { 1440 }
        "4" { 1080 }
        "5" { 720 }
        "6" { 480 }
        "0" { 0 }
        default { -1 }
    }

    if ($MaxHeight -eq 0) {
        continue
    }

    if ($MaxHeight -eq -1) {
        Show-Message "[ERROR] Invalid quality selection." "Red"
        Start-Sleep -Seconds 2
        continue
    }

    # ========================================================
    # PLAYLIST FOLDER SELECTION
    # ========================================================

    if ($IsPlaylist) {

        Show-Header

        Show-Message "SELECT PLAYLIST DOWNLOAD LOCATION" "Yellow"

        Write-Host ""
        Show-Message "  1. Default Folder" "Green"
        Show-Message "     $Destination" "Gray"

        Write-Host ""
        Show-Message "  2. Create New Folder" "Green"
        Show-Message "     Create a separate folder inside Downloads" "Gray"

        Write-Host ""
        Write-Host "==================================================" -ForegroundColor Cyan

        $FolderChoice = Read-Host "Select folder option"

        switch ($FolderChoice) {

            "1" {
                $DownloadDestination = $Destination
            }

            "2" {

                Write-Host ""

                $FolderCreated = $false

                while (-not $FolderCreated) {

                    $FolderName = Read-Host "Enter new folder name"

                    if ([string]::IsNullOrWhiteSpace($FolderName)) {
                        Show-Message "[ERROR] Folder name cannot be empty." "Red"
                        continue
                    }

                    $FolderName = $FolderName.Trim()

                    $InvalidChars = [IO.Path]::GetInvalidFileNameChars()

                    if (
                        $FolderName -eq "." -or
                        $FolderName -eq ".." -or
                        $FolderName.IndexOfAny($InvalidChars) -ge 0 -or
                        $FolderName.Contains("/") -or
                        $FolderName.Contains("\")
                    ) {
                        Show-Message "[ERROR] Invalid folder name. Use a simple folder name." "Red"
                        continue
                    }

                    $NewFolderPath = Join-Path -Path $Destination -ChildPath $FolderName

                    try {

                        if (-not (Test-Path -LiteralPath $NewFolderPath)) {

                            New-Item `
                                -ItemType Directory `
                                -Path $NewFolderPath `
                                -Force `
                                -ErrorAction Stop | Out-Null

                            Show-Message "[SUCCESS] New folder created." "Green"
                        }
                        else {
                            Show-Message "[INFO] Folder already exists. Using existing folder." "Yellow"
                        }

                        $DownloadDestination = $NewFolderPath
                        $FolderCreated = $true
                    }
                    catch {
                        Show-Message "[ERROR] Could not create folder: $($_.Exception.Message)" "Red"
                    }
                }
            }

            default {
                Show-Message "[ERROR] Invalid folder selection." "Red"
                Start-Sleep -Seconds 2
                continue
            }
        }
    }

    # ========================================================
    # PLAYLIST COUNT
    # ========================================================

    $TotalVideos = 1

    if ($IsPlaylist) {

        Show-Header

        Show-Message "Checking playlist information..." "Yellow"
        Show-Message "Please wait." "Gray"

        $MetaArgs = @(
            "--ignore-config"
            "--cookies", $Cookie
            "--flat-playlist"
            "--dump-single-json"
            "--no-warnings"
            $Url
        )

        $MetaOutput = & $YtDlp @MetaArgs 2>$null | Out-String
        $MetaExitCode = $LASTEXITCODE

        if ($MetaExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($MetaOutput)) {

            try {
                $PlaylistInfo = $MetaOutput | ConvertFrom-Json

                if ($null -ne $PlaylistInfo.entries) {
                    $TotalVideos = @($PlaylistInfo.entries).Count
                }
                elseif ($PlaylistInfo.id) {
                    $TotalVideos = 1
                }
            }
            catch {
                $TotalVideos = 0
            }
        }
        else {
            $TotalVideos = 0
        }

        if ($TotalVideos -gt 0) {
            Show-Message "Total videos found: $TotalVideos" "Green"
        }
        else {
            Show-Message "[WARNING] Could not determine playlist count." "Yellow"
            Show-Message "Downloads will continue, but remaining count may be unavailable." "Gray"
        }

        Start-Sleep -Seconds 1
    }

    # ========================================================
    # DOWNLOAD SCREEN
    # ========================================================

    Show-Header

    Write-Host " Destination : " -NoNewline -ForegroundColor Gray
    Write-Host $DownloadDestination -ForegroundColor White

    Write-Host " Quality     : " -NoNewline -ForegroundColor Gray
    Write-Host "$($MaxHeight)p maximum" -ForegroundColor White

    if ($IsPlaylist) {
        Write-Host " Total Videos: " -NoNewline -ForegroundColor Gray

        if ($TotalVideos -gt 0) {
            Write-Host $TotalVideos -ForegroundColor White
        }
        else {
            Write-Host "Unknown" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    Show-Message "                 DOWNLOADING" "Yellow"
    Write-Host ""

    # ========================================================
    # DOWNLOAD COUNTERS
    # ========================================================

    $Downloaded = 0
    $Skipped = 0
    $CurrentVideo = "1"
    $CurrentPercent = 0
    $DownloadErrors = @()
    $DuplicateFound = $false
    $CurrentItemSkipped = $false

    # ========================================================
    # YT-DLP ARGUMENTS
    # ========================================================

    $YtArgs = @(
        "--ignore-config"
        "--cookies", $Cookie
        "--newline"
        "--progress"
        "--progress-template", 'download:PROGRESS:%(progress._percent_str)s'
        "--print", 'before_dl:VIDEO_START:%(playlist_index)s'
        "--print", 'after_move:VIDEO_DONE:%(playlist_index)s'
        "--no-warnings"
        "--no-overwrites"
        "-P", $DownloadDestination
        "-o", '%(title)s [%(height)sp] [%(id)s].%(ext)s'
        "-f", "bestvideo[height<=$MaxHeight]+bestaudio/best[height<=$MaxHeight]"
        "--merge-output-format", "mp4"
        $PlaylistFlag
        $Url
    )

    # ========================================================
    # RUN DOWNLOAD AND PROCESS LIVE OUTPUT
    # ========================================================

    & $YtDlp @YtArgs 2>&1 | ForEach-Object {

        $Line = "$_"

        # NEW VIDEO STARTED
        if ($Line -match '^VIDEO_START:(.*)$') {

            $CurrentVideo = $Matches[1]

            if ([string]::IsNullOrWhiteSpace($CurrentVideo) -or $CurrentVideo -eq "NA") {
                $CurrentVideo = [string]($Downloaded + $Skipped + 1)
            }

            $CurrentPercent = 0
            $CurrentItemSkipped = $false

            if ($IsPlaylist -and $TotalVideos -gt 0) {
                Show-ProgressStatus `
                    -Percent 0 `
                    -Total $TotalVideos `
                    -Downloaded $Downloaded `
                    -Skipped $Skipped `
                    -CurrentVideo $CurrentVideo
            }
        }

        # VIDEO DOWNLOAD PROGRESS
        elseif ($Line -match 'PROGRESS:\s*([\d.]+)\s*%') {

            $CurrentPercent = [double]$Matches[1]
            $CurrentPercent = [math]::Min(100, [math]::Max(0, $CurrentPercent))

            if ($IsPlaylist -and $TotalVideos -gt 0) {

                Show-ProgressStatus `
                    -Percent $CurrentPercent `
                    -Total $TotalVideos `
                    -Downloaded $Downloaded `
                    -Skipped $Skipped `
                    -CurrentVideo $CurrentVideo
            }
            else {

                Write-Progress `
                    -Activity "DOWNLOADING VIDEO" `
                    -Status "$([math]::Round($CurrentPercent))% completed" `
                    -PercentComplete $CurrentPercent
            }
        }

        # SUCCESSFULLY COMPLETED VIDEO
        elseif ($Line -match '^VIDEO_DONE:') {

            $Downloaded++

            if ($IsPlaylist -and $TotalVideos -gt 0) {

                $OverallPercent = (($Downloaded + $Skipped) / $TotalVideos) * 100

                Write-Progress `
                    -Activity "DOWNLOADING PLAYLIST" `
                    -Status "Downloaded: $Downloaded | Skipped: $Skipped | Remaining: $([math]::Max(0, $TotalVideos - $Downloaded - $Skipped))" `
                    -PercentComplete ([math]::Min(100, $OverallPercent))
            }
        }

        # DUPLICATE / EXISTING FILE
        elseif (
            $Line -match 'already been downloaded|has already been downloaded|has already been recorded'
        ) {

            if (-not $CurrentItemSkipped) {

                $Skipped++
                $DuplicateFound = $true
                $CurrentItemSkipped = $true

                Write-Progress -Activity "DOWNLOADING" -Completed

                Write-Host ""
                Show-Message "[DUPLICATE] Existing video skipped." "Yellow"
            }
        }

        # DOWNLOAD ERROR
        elseif ($Line -match 'ERROR:|Traceback|Exception:') {

            $DownloadErrors += $Line

            Write-Progress -Activity "DOWNLOADING" -Completed

            Write-Host ""
            Show-Message $Line "Red"
        }
    }

    $DownloadExitCode = $LASTEXITCODE

    Write-Progress -Activity "DOWNLOADING" -Completed

    # ========================================================
    # FINAL DOWNLOAD SUMMARY
    # ========================================================

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Show-Message "                 DOWNLOAD SUMMARY" "Yellow"
    Write-Host "==================================================" -ForegroundColor Cyan

    if ($IsPlaylist) {

        Write-Host ""

        Write-Host " Total Videos : " -NoNewline -ForegroundColor Gray

        if ($TotalVideos -gt 0) {
            Write-Host $TotalVideos -ForegroundColor White
        }
        else {
            Write-Host "Unknown" -ForegroundColor Yellow
        }

        Write-Host " Downloaded  : " -NoNewline -ForegroundColor Gray
        Write-Host $Downloaded -ForegroundColor Green

        Write-Host " Skipped     : " -NoNewline -ForegroundColor Gray
        Write-Host $Skipped -ForegroundColor Yellow

        Write-Host " Remaining   : " -NoNewline -ForegroundColor Gray

        if ($TotalVideos -gt 0) {
            $Remaining = [math]::Max(0, $TotalVideos - $Downloaded - $Skipped)
            Write-Host $Remaining -ForegroundColor White
        }
        else {
            Write-Host "Unknown" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan

    if ($DownloadExitCode -eq 0) {

        if ($IsPlaylist -and $TotalVideos -gt 0 -and ($Downloaded + $Skipped) -lt $TotalVideos) {
            Show-Message "       DOWNLOAD FINISHED WITH UNPROCESSED ITEMS" "Yellow"
        }
        elseif ($Downloaded -gt 0) {
            Show-Message "             DOWNLOAD COMPLETED" "Green"
        }
        elseif ($Skipped -gt 0) {
            Show-Message "          EXISTING DOWNLOADS SKIPPED" "Yellow"
        }
        else {
            Show-Message "             DOWNLOAD FINISHED" "Green"
        }
    }
    else {

        Show-Message "               DOWNLOAD FAILED" "Red"

        if ($DownloadErrors.Count -eq 0) {
            Show-Message "[ERROR] Check URL, cookies, internet connection, or FFmpeg." "Red"
        }
    }

    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""

    # ========================================================
    # DOWNLOAD ANOTHER VIDEO
    # ========================================================

    $Again = Read-Host "Download another video? [Y/N]"

    if ($Again -notmatch '^[Yy]$') {
        break
    }
}

Show-Message "Thank you for using YouTube Downloader!" "Cyan"

