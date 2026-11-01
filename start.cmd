@echo off
cd /d "%~dp0"
title MyFirstAI Smart - Local AI
py --version >nul 2>&1
if errorlevel 1 (
    echo The Windows Python launcher ^(py^) is not installed.
    echo Install Python 3 from https://www.python.org/downloads/
    pause
    exit /b 1
)
py main.py
if errorlevel 1 echo An error occurred. Check the message above.
echo.
pause
