# 4070 학습 킷 — 언어 모델 설치 + 실행 가이드 (보강 v1, 2026-06-17)

**대상**: 개발자 로컬(RTX 4070, Windows). V771 킷의 누락분(모델 설치·인증·패키지·IDE 실행) 보강.
**왜**: 기존 SETUP은 torch/패키지만 다룸. base 모델(Llama)은 **HuggingFace에서 받아야 하고 게이트 인증이 선행**돼야 함 — 안 하면 실행이 401로 실패.

## 0. 전체 순서 한눈에
```
① 레포 + 패키지 설치  → ② GPU/torch 환경(SETUP_4070)  → ③ 언어 모델 인증·다운로드
→ ④ 스모크 실행(합성)  → ⑤ 실데이터(dpo_pairs.jsonl) 학습  → ⑥ 승률 측정
```

## 1. 레포 + 패키지 설치 (킷이 빠뜨린 선행단계)
킷의 `run_first_training.py`는 `literary_system`을 import하므로 레포 안에서 패키지를 깔아야 함.
```powershell
git clone https://github.com/limsanghyuk/literary-os.git
cd literary-os
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -e .                      # literary_system 패키지
```
그다음 `SETUP_4070_WINDOWS.md`대로 torch(CUDA)·transformers·peft·trl·bitsandbytes 설치.

## 2. ★언어 모델 설치 — 두 경로 중 택1
모델은 디스크에 미리 "인스톨"하는 게 아니라 **첫 실행 시 HuggingFace에서 자동 다운로드**된다. 단 다운로드 권한이 필요.

### 경로 A — Llama-3.2-3B (게이트 모델, 권장 기본값)
1. huggingface.co 가입 → 모델 페이지 `meta-llama/Llama-3.2-3B`에서 **"Agree and access" 라이선스 동의**(승인 보통 즉시~수분).
2. HF 토큰 발급: huggingface.co/settings/tokens → Read 토큰.
3. 로그인(토큰은 로컬에만 저장):
```powershell
pip install -U "huggingface_hub[cli]"
huggingface-cli login          # 토큰 붙여넣기  (또는  $env:HF_TOKEN="hf_..." )
```
4. 이제 `--base meta-llama/Llama-3.2-3B`로 실행하면 자동 다운로드(~6GB).

### 경로 B — 게이트 없는 대체 모델 (동의 절차 불요, 즉시)
라이선스 동의가 번거로우면 비게이트 3B 모델로 동일 검증 가능:
```powershell
python run_first_training.py --pairs sample_dpo_smoke.jsonl --smoke --base Qwen/Qwen2.5-3B-Instruct
```
(`Qwen/Qwen2.5-3B-Instruct` 등은 동의 없이 바로 다운로드. 메커니즘 증명엔 충분.)

### 오프라인/사전다운로드(선택)
```powershell
huggingface-cli download meta-llama/Llama-3.2-3B --local-dir C:\models\llama32-3b
# 실행 시  --base C:\models\llama32-3b
```

## 3. 실행 — 명령줄 / VS Code 둘 다 가능
킷은 **명령줄 Python 스크립트**다. VS Code로 돌리려면:
- VS Code에서 `literary-os` 폴더 열기 → 우하단 **Python 인터프리터 = `.venv`** 선택.
- 터미널(Ctrl+`)에서 아래 명령 실행(VS Code "Run" 버튼은 인자 전달이 번거로우니 터미널 권장).

```powershell
# ④ 스모크(환경 점검, 합성 데이터) — 모델 인증 후
python run_first_training.py --pairs sample_dpo_smoke.jsonl --smoke
#   → Preflight PASS + 4쌍 학습 무에러면 환경 OK

# ⑤ 실데이터 학습 (개발자 dpo_pairs.jsonl)
python run_first_training.py --pairs C:\path\dpo_pairs.jsonl --base meta-llama/Llama-3.2-3B --out .\lora_out

# ⑥ 학습 전후 승률 측정
python eval_winrate.py   # (또는 콘솔의 baseline 승률 + 학습 로그 확인)
```

## 4. 사전 점검(실행 전)
```powershell
nvidia-smi
python -c "import torch; print('CUDA', torch.cuda.is_available(), torch.cuda.get_device_name(0))"
python -c "import bitsandbytes, peft, trl, transformers, datasets; print('deps OK')"
python -m literary_system.finetune.train_local --help
```
※ `LocalPreflight`가 GPU·패키지를 점검하고, 실패 시 클라우드(RunPod/Lambda) 폴백을 안내함.

## 5. 자주 나는 오류
- `401 / gated repo`: 2번 경로 A의 라이선스 동의·`huggingface-cli login` 누락 → 동의·로그인 또는 경로 B(Qwen) 사용.
- `CUDA out of memory`: `--rank 8`, batch=1 유지, 다른 GPU 앱 종료. 8GB 노트북은 3B만.
- `bitsandbytes` 임포트 실패(Windows): 최신 버전 재설치(`pip install -U bitsandbytes`), CUDA 빌드 torch 확인.
- `literary_system not found`: 레포 루트에서 `pip install -e .` 했는지 확인.

## 6. 기대치(정직)
17쌍·1회 학습은 **"메커니즘이 작동/지표가 움직이는가"** 확인용. 실제 품질 향상엔 선호쌍 수백 + 여러 라운드 + KL 가드 + 인간 GT 재정렬 필요(별도). 이 1회가 T1(실 GPU loop-C 라운드)의 첫걸음.
