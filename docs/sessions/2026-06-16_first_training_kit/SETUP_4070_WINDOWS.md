# Windows + RTX 4070 QLoRA 환경 구성

## 사전
- Windows 10/11, RTX 4070(데스크톱 12GB 권장 / 노트북 8GB도 3B는 가능)
- 최신 NVIDIA 드라이버, Python 3.10/3.11

## 설치 (PowerShell)
```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
# CUDA 12.1 빌드 torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets peft trl accelerate
# Windows용 bitsandbytes (4bit)
pip install bitsandbytes
```

## 확인
```powershell
nvidia-smi                 # GPU·VRAM 표시되어야 함
python -c "import torch; print('CUDA', torch.cuda.is_available(), torch.cuda.get_device_name(0))"
python -m literary_system.finetune.train_local --help
```

## VRAM 팁(12GB)
- 3B QLoRA ≈ 6GB (안전). 8B QLoRA ≈ 11.5GB (빠듯 — 배치 1, grad_accum↑, seq len↓)
- OOM 시: `--rank 8`, per_device_batch=1 유지, 다른 GPU 앱 종료
- 노트북 8GB: 3B만 권장

## 게이트우드
실행 전 `LocalPreflight`가 GPU·패키지를 점검합니다. 실패하면 클라우드(RunPod/Lambda) 폴백 안내가 출력됩니다.
