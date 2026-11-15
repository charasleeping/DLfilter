@echo off
setlocal
cd /d "%~dp0"
title DLfilter
if exist "bin\dlfilter.exe" (
    "bin\dlfilter.exe" serve --open
) else if exist "target\release\dlfilter.exe" (
    "target\release\dlfilter.exe" serve --open
) else (
    echo Native server not found. Install a native release or run: cargo build --release --locked
    pause
    exit /b 1
)
if errorlevel 1 pause
