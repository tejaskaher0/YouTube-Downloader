@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 start.py --uninstall-shortcut
) else (
    python start.py --uninstall-shortcut
)
echo.
pause
