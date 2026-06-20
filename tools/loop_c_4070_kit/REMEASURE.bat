@echo off
chcp 65001 >nul
cd /d %~dp0
echo per-token remeasure (no training, measure only)...
python -u remeasure_4070.py pairs_held.jsonl
echo.
echo Done. Send output to Claude.
pause
