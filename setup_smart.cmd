@echo off
cd /d "%~dp0"
title MyFirstAI Smart - Download Local Model
echo =========================================
echo   MyFirstAI Smart - One-Time Setup
echo =========================================
echo.
where ollama >nul 2>&1
if errorlevel 1 (
    echo Ollama is not installed or not on PATH.
    echo First install the free Ollama app from https://ollama.com/download/windows
    echo Then open Ollama and rerun this file.
    echo.
    pause
    exit /b 1
)
echo This downloads a free pretrained code model (~1.9 GB).
echo No API keys are needed.
echo.
ollama pull qwen2.5-coder:3b
if errorlevel 1 (
    echo Model download failed. Make sure Ollama is open and you have internet.
    pause
    exit /b 1
)
echo.
echo DONE! Double-click start.cmd to launch MyFirstAI Smart.
echo For a stronger (larger) model later, use: ollama pull qwen2.5-coder:7b
pause
