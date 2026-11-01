@echo off
cd /d "%~dp0"
title MyFirstAI - Restore Main Launcher
py -c "from pathlib import Path; import shutil; p=Path('backups'); files=sorted(p.glob('*_main_py.backup.py')); assert files, 'No main.py backups found'; shutil.copy2(files[-1], 'main.py'); print('Restored main.py from', files[-1])"
if errorlevel 1 echo Restore failed or no backups available.
pause
