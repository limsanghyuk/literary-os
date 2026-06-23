@echo off
chcp 65001 >nul
cd /d %~dp0
echo SP-E.10 v3 - Path B hardsignal, adopt/rollback only, single held (5 rounds, ~30-40min)...
python -u train_4070_cumulative_v3.py
echo.
echo Done. Send round_records_v3.json to Claude.
pause
