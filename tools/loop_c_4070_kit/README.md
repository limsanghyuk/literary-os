# loop_c_4070_kit — 실 GPU loop-C QLoRA DPO 킷 (집 RTX 4070 검증)

실 Llama-3.1-8B를 소비자 GPU(4070 12GB)에서 QLoRA DPO 학습하고 **held-out ΔW + KL**을 측정하는 단독 킷.
2026-06-19 집 4070에서 라운드 #1(메커니즘 실증)·#2(held-out) 검증. 상세 = `docs/sessions/2026-06-19_HANDOFF_*`.

## 파일
- `RUN_TRAIN.py` — import bisect(0xC0000005 우회 환경변수) + 학습 호출 + result.txt tee. 진입점.
- `RUN_TRAIN.bat` — 더블클릭용(`python -u RUN_TRAIN.py`).
- `train_4070.py` — QLoRA DPO 본체. held-out W/M + KL/token proxy + rounds_ledger.jsonl.
- `FIX_torch.bat` — torch 2.6+cu124 업그레이드(trl 1.6 FSDP2 요구 해소).
- `make_pairs.py` — 명작 닻 선호쌍 생성(chosen=명작, rejected=gpt-4o-mini draft, 심판 없음). 코퍼스 경로 조정 필요.

## 로컬 전용(레포 미포함, 직접 준비)
- `hf_token.txt`(HF 토큰 1줄) · `pairs_train.jsonl`/`pairs_held.jsonl`(명작 원문 verbatim 포함) · `lora_out_4070/`(학습 산출 어댑터).

## 스택 (검증됨)
Python 3.10 / torch **2.6.0+cu124** / transformers 5.12.1 / trl 1.6.0 / peft 0.19.1 / bitsandbytes 0.49.2 / datasets 5.0.0.
Llama-3.1-8B-Instruct(HF 게이트 승인 필요) 4bit nf4 + QLoRA(q/k/v/o_proj r16). 비게이트 대안=Qwen2.5-7B-Instruct.

## 실행
1. `FIX_torch.bat` (1회, torch 정렬) → 2. `hf_token.txt` 작성 + 데이터 준비 → 3. `RUN_TRAIN.bat`.
결과: result.txt 최종 블록 + rounds_ledger.jsonl + lora_out_4070/adapter_model.safetensors(ΔW).
