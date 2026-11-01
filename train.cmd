@echo off
cd /d "%~dp0"
title MyFirstAI - Walk Mode (training and self-improvement)
py --version >nul 2>&1
if errorlevel 1 (
  echo Python launcher py is missing. Install Python for Windows.
  pause
  exit /b 1
)
echo Starting unattended local training and self-improvement...
echo You may leave this running while you are away.
echo It stops by itself after its task limit or 30 minutes, whichever is first.
echo Don't shut down, sleep, or unplug the PC during training.
echo.
py -u walk_mode.py
if errorlevel 1 echo Training stopped with an error. See the message above.
echo.
echo Results: logs and proposals folders. Backups: backups folder.
echo You can close this window now.
pause
