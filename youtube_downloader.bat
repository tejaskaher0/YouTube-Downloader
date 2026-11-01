
@echo off
setlocal
title YouTube Downloader

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0youtube_downloader.ps1"

if errorlevel 1 (
    echo.
    echo [ERROR] Downloader encountered a problem.
    pause
)

endlocal

