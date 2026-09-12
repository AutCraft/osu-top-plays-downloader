@echo off
setlocal
title osu! Beatmap Downloader

echo ===================================================
echo             osu! Beatmap Downloader
echo ===================================================
echo.

where bun >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    bun OSUDownloader.js %*
    goto finish
)

where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    node OSUDownloader.js %*
    goto finish
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python OSUDownloader.py %*
    goto finish
)

echo [ERROR] Neither Bun, Node.js, nor Python was found on your system!
echo Please install Bun, Node.js, or Python.
pause
exit /b 1

:finish
echo.
echo ===================================================
set /p OPEN_FOLDER="Open downloaded songs folder? [Y/n]: "
if /i not "%OPEN_FOLDER%"=="n" (
    if exist "songs" start "" "songs"
)
echo.
pause
