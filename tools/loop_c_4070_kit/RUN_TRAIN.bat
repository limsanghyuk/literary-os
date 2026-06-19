@echo off
chcp 65001 >nul
cd /d %~dp0
echo Running diagnose + train... (live below; also saved to result.txt)
python -u RUN_TRAIN.py
echo.
echo Done. Send result.txt content to Claude.
pause
