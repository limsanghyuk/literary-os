# 2026-06-19 — 실 4070 QLoRA DPO 라운드 #1 + 수백 쌍 데이터 파이프라인

집 RTX 4070에서 실 Llama-3.1-8B QLoRA DPO를 **처음 끝까지 완주**. 샌드박스 GPU 부재로 막혀 있던
loop-C 마지막 미증명 조각(실 가중치 학습 1라운드) 해소. 이어서 held-out 평가가 가능한 수백 쌍 라운드를 준비.

## 1. 확정된 동작 스택 (재현용)
- 집 RTX 4070 12GB / 시스템 RAM 64GB / Python 3.10 (Windows).
- **torch 2.6.0+cu124** (필수), transformers 5.12.1, trl 1.6.0, peft 0.19.1, bitsandbytes 0.49.2, datasets 5.0.0, numpy 2.2.6.
- 모델 meta-llama/Llama-3.1-8B-Instruct (HF 게이트 승인 + 토큰), 4bit nf4 + QLoRA(q/k/v/o_proj, r16, beta0.1, lr5e-5).
- 킷: 단독 폴더(로컬 전용). RUN_TRAIN(누적 import bisect + 환경변수 패치 + 학습) + train_4070.py.

## 2. 진단 체인 (4개 블로커 → 해결) — 재현 시 그대로 적용
1. `huggingface-cli not found` → hub 1.x는 CLI가 `hf`. HF_TOKEN env로 우회.
2. import 시 **무음 네이티브 크래시(0xC0000005 access violation)** → OpenMP/MKL 다중 런타임 충돌.
   환경변수 `KMP_DUPLICATE_LIB_OK=TRUE` + `MKL_THREADING_LAYER=GNU` + `MKL_SERVICE_FORCE_INTEL=1` + `OMP_NUM_THREADS=1` 로 해소.
   진단법: 각 import를 **별도 subprocess로 누적식**(torch→datasets→transformers→peft→trl→bnb) 실행해 0xC0000005 나는 추가 지점 격리.
3. `+trl` 단계 크래시 = `cannot import name 'FSDPModule' from torch.distributed.fsdp` → **trl 1.6은 torch 2.6+ (FSDP2) 요구**.
   torch 2.5.1+cu121 → 2.6.0+cu124 업그레이드로 해소(4070 드라이버 cu124 호환).
4. `401 GatedRepoError` → HF 토큰 미전달 + Llama 게이트. 토큰 로컬 주입 + 게이트 승인으로 해소.
- 파일툴이 virtiofs 마운트 대용량 쓰기를 truncate → **heredoc→/tmp→cp** 패턴으로 작성해야 안전(반복 확인).

## 3. 라운드 #1 결과 (24쌍, 3에폭, ~90초)
| 지표 | 학습 전 | 학습 후 | 비고 |
|---|---|---|---|
| abs-pref-acc (W) | 0.458 | 0.458 | dW +0.000 — **절대 순서 지표 둔감** |
| reward-margin (M) | +27.70 | +43.77 | **dM +16.07 — 학습 확정** |
| rewards/margins | 0.281 | 1.331 | DPO 내부 4.7배 |
| rewards/accuracies | 0.575 | 1.000 | |
| logps/chosen | -812.8 | -797.4 | chosen 확률 상승 |
| logps/rejected | -833.3 | -847.7 | rejected 확률 하락 |

**해석**: DPO는 *기준모델 대비 상대 선호(마진)* 를 최적화 → 결정적 상승. acc(절대 순서)는 24쌍으로는 틀린 쌍의
큰 격차를 못 뒤집어 평평. dW=0은 **지표 둔감이지 무변화 아님**(dM로 확정). LoRA 정상 작동.

## 4. 게이트 판정 — 메커니즘 PASS / 채택 보류(DEFERRED)
이 dM은 **학습에 쓴 24쌍 위 in-sample** 값 = 일반화/품질향상 증거 아님(과적합·보상해킹 가능).
G_LOOPC_WINRATE(ΔW>0 ∧ KL≤τ ∧ 구조비퇴행): ΔW는 in-sample만, KL·구조 미측정 → **어댑터 폐기, 채택 보류**.
게이트가 정직하게 거름(tiny-gpt2 / OpenAI 6지표 라운드와 동일 패턴, 단 이번은 실 8B/실 4070 — 인프라 완전 실증).

## 5. 수백 쌍 데이터 파이프라인 (라운드 #2 준비) — 방법론
self-preference 편향 제거를 위해 **LLM 심판 제거, 명작 정적 닻(ADR-243 M2 정신) 채택**:
- **chosen = 실제 명작 씬** (corpus_ko 41,506개 사용가능 풀, 250~650자), **rejected = gpt-4o-mini 생성 draft**.
- 심판 없음 → 편향 0. 학습 목표(생성46% vs 명작54% 격차 좁히기)와 직접 정합.
- 280쌍 생성(고유 명작 171편, 7기능×6장르 분산), 중복 제거, **결정적 80/20 → train 224 / held 56**.
- 생성은 샌드박스에서 스레드 병렬 + 시간분할(백그라운드 프로세스가 호출 종료 시 소멸하므로 포그라운드 청크).
- **주의: 선호쌍에는 명작 원문(verbatim)이 들어가므로 허브 비커밋. 로컬 전용.** 본 문서는 방법론·수치만 기록.

## 6. train_4070 v3 — held-out 평가 설계
- train split 학습 → **held split(미학습 56쌍)에서 W0→W1, M0→M1 측정** = 진짜 일반화 여부.
- **KL/token proxy**: held chosen에서 adapter-ON(정책) vs `disable_adapter()`(기준) 로짓의 per-token KL(π‖ref) 평균. τ=0.50 가드.
- 출력: G_LOOPC_WINRATE 부분판정 `[dW>0]`, `[KL≤τ]`, 구조비퇴행은 literary_system 게이트로 위임(N/A 표기).
- held dW>0 ∧ KL≤τ → "ADOPT-candidate → 구조게이트 실행" / else ROLLBACK.

## 7. 다음
1. 라운드 #2 실행(집 4070, ~15분) → held dW·KL 실측 → 채택/롤백 확정.
2. 채택 후보 시: 생성 샘플에 공식 채점(drama_genre_drse 등) 돌려 **구조 비퇴행** 확인 → G_LOOPC_WINRATE 완전 판정.
3. Path B(클라우드): RunPod 키 확보 시 CloudTrainingNode 병행(키 미제공 상태).

관련: 2026-06-18_real_6metrics, 2026-06-19_install_4070_train_design, 2026-06-19_cloud_dW_finding.
