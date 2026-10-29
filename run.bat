@echo off
title DECART LIVE PRO
echo Starting DECART LIVE PRO...
cd /d "%~dp0"
call venv\Scripts\activate
python app.py
pause
