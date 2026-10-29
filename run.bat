@echo off
title DECART LIVE PRO
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [*] Virtual environment not found. Running automated setup first...
    call setup_and_build.bat
    exit /b
)

echo Starting DECART LIVE PRO...
call venv\Scripts\activate.bat
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
