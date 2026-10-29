@echo off
setlocal enabledelayedexpansion
title DECART LIVE PRO - Setup and Build

echo ========================================================
echo    DECART LIVE PRO - Automated Setup and Build
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Verify Python is installed and accessible
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10-3.13 and ensure "Add Python to PATH" is checked.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [*] Detected: %PY_VER%

:: 2. Create Virtual Environment if it does not exist
if not exist "venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment in .\venv...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
) else (
    echo [*] Existing virtual environment found in .\venv.
)

:: 3. Activate Virtual Environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

:: 4. Install and upgrade dependencies
echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo [*] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install required packages.
    pause
    exit /b 1
)

echo [*] Installing local package (vidu_sdk)...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install vidu_sdk in editable mode.
    pause
    exit /b 1
)

:: 5. Compile Standalone Executable
echo.
echo ========================================================
echo    Building Standalone Executable (build_exe.py)
echo ========================================================
echo.
python build_exe.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build compilation failed. Check logs above.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo    [SUCCESS] Setup and Build Completed Successfully!
echo    Standalone Executable: dist\DecartLivePro.exe
echo    (Also copied to your Desktop if accessible)
echo ========================================================
echo.
pause
