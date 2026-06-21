@echo off
chcp 65001 >nul
cd /d %~dp0
echo === SP-E.9 accumulation: rounds 2-5 (independent splits, base each, epochs=1) ===
for %%R in (2 3 4 5) do (
  echo.
  echo ===== ROUND %%R =====
  python -u train_4070_p0.py --train r%%R_train.jsonl --held r%%R_held.jsonl --epochs 1 --out ./lora_r%%R
)
echo.
echo All rounds done. Send rounds_ledger.jsonl tail to Claude.
pause
