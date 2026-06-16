# 4070 첫 실 학습 실행 킷 (V771)

목적: **RTX 4070에서 첫 QLoRA DPO 학습 1회**를 돌려 baseline 승률(현재 0.588)이 실제로 움직이는지 측정.
→ 1회 = RLAIF 메커니즘 증명. 품질 향상은 이후 데이터 확대 + 반복(별도).

## 0. 중요 — 데이터
이 킷에는 **저작권 보호로 실제 명작/생성 텍스트가 없습니다.** 개발자의 로컬 전체 데이터
`dpo_pairs.jsonl`(포맷: `{func,genre,ref_id,winner,draft,ref}` 줄단위 JSON)을 직접 가리켜야 합니다.
없으면 먼저 `sample_dpo_smoke.jsonl`(합성)로 파이프라인만 점검하세요.

## 1. 순서
1) `SETUP_4070_WINDOWS.md` 따라 환경 구성(torch+CUDA, bitsandbytes, peft, trl, transformers, datasets)
2) 스모크: `python run_first_training.py --pairs sample_dpo_smoke.jsonl --smoke`
   → Preflight PASS + 4쌍 학습이 에러 없이 끝나면 환경 OK
3) 실데이터: `python run_first_training.py --pairs C:\path\dpo_pairs.jsonl --base meta-llama/Llama-3.2-3B`
4) 측정: 콘솔의 baseline 승률 + 학습 로그 확인. 학습 후 재생성 평가는 eval_winrate.py 참조

## 2. 기대치(솔직히)
- 17쌍은 매우 적습니다. 1회로 큰 향상은 기대하지 마세요 — **"움직이는가"**만 봅니다.
- 의미있는 향상엔 선호쌍 수백 + 여러 라운드 + KL 가드레일 + 인간 GT 재정렬이 필요합니다.

## 3. 파일
- `SETUP_4070_WINDOWS.md` — Windows/4070 설치 가이드
- `run_first_training.py` — 원샷 러너(계획→Preflight→변환→학습)
- `eval_winrate.py` — 학습 전후 승률 측정 보조
- `sample_dpo_smoke.jsonl` — 합성 스모크 데이터(저작권 무관)
