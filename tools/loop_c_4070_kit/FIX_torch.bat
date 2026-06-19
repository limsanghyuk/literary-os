@echo off
chcp 65001 >nul
cd /d %~dp0
echo ================================================================
echo  trl 1.6 requires torch 2.6+ (FSDP2). Upgrading torch (cu124)...
echo  ~2.5GB download. Keep this window open until it finishes.
echo ================================================================
echo.
pip install --upgrade "torch>=2.6" --index-url https://download.pytorch.org/whl/cu124
echo.
echo --- verifying ---
python -c "import torch; print('torch', torch.__version__, '| CUDA', torch.cuda.is_available()); from torch.distributed.fsdp import FSDPModule; print('FSDPModule OK -> trl will import')"
echo.
echo Done. If you saw 'FSDPModule OK', now double-click RUN_TRAIN.bat.
pause
