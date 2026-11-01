@echo off
cd /d "%~dp0"
py -m unittest discover -p "test_*.py" -v
echo.
pause
