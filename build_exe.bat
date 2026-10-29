@echo off
title Build DECART LIVE PRO Standalone Executable
cd /d "%~dp0"
echo ============================================================
echo   BUILDING DECART LIVE PRO STANDALONE EXECUTABLE
echo ============================================================
echo.

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe build_exe.py
) else (
    python build_exe.py
)

pause
