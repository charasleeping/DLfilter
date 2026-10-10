@echo off
setlocal
cd /d "%~dp0"
title DLfilter

set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
    echo DLfilter uses uv, see https://docs.astral.sh/uv/, to set up Python and its libraries.
    choice /c YN /m "Install uv now with https://astral.sh/uv/install.ps1"
    if errorlevel 2 (
        echo Cancelled.
        pause
        exit /b 1
    )
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
)
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo Installing libraries. The first run downloads about 1 GB...
uv sync --locked || (echo Setup failed. & pause & exit /b 1)
uv run --no-sync python -m module.fetch_database || (echo Database setup failed. & pause & exit /b 1)

echo Starting DLfilter. Press Ctrl+C to stop.
uv run --no-sync python app.py --open
if errorlevel 1 pause
