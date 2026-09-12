@echo off
where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pythonw gui.py
    exit /b 0
)
python gui.py
