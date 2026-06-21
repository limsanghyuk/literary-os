# 2026-06-21 SP-E.9 라운드#3 — 생산 혼합(P1+P3+P2) 첫 ADOPT (졸업 누적 1/5)

순서 4. 생산 혼합비 근사로 통합 라운드 → 졸업 누적 시작.

## 데이터 (혼합, work_id 무작위화로 train/held 대표성)
- P1 15%(인과셔플·길이보존) + P3 55%(show-don't-tell) + P2 20%(구체vs평이, API). **P4 동점=DPO 비대상 보류, P2=API근사(완전 온폴리시는 4070 모델-인-루프 후속).**
- 개발자 build() 게이팅: 토큰정확트림 후 length_match 540/540 통과. work-level split **train 290(P1 57/P3 166/P2 67) / held 250(P1 33/P3 164/P2 53)·누설0**.

## 결과 (held 250, epochs=1, ~4분)
| 지표 | W0 | W1 | Δ |
|---|---|---|---|
| per-token 승률 | 0.508(찍기) | 0.708 | **dW_pt +0.200** |
| sum 승률 | 0.324 | 0.524 | +0.200 |
| per-token 마진 | −0.022 | +0.132 | +0.153 |
| KL/token | — | **0.0596** | τ=0.50 |

**G_LOOPC_WINRATE(per-token): [PASS] dW>0 · [PASS] KL≤τ → ADOPT.** (c3 R_path는 P3 라운드서 PASS 입증; 본 라운드 미재측정)

## 해석
- W0=0.508: 혼합 신호서 base 출발점 우연. W1=0.708: 71% 좋은쪽 학습·일반화.
- KL 0.0596: 누적 최저(P1 0.406→P3 0.127→혼합 0.06). 혼합+epochs1이 과적합 차단 = 가장 건전.

## SP-E.9 종합 (4070 단독, A100/H100·RunPod 불요)
Round#2 길이착시 ROLLBACK → P1 메커니즘 → P3 craft ADOPT(c1∧c2∧c3_path) → **혼합 ADOPT**. 깨끗한 per-token loop-C 완전 실증.

## 졸업(SP-E.10) 남은 길
- 누적 **1/5** adopt(생산혼합). 형식 졸업=adopt 5연속·per-token W CI하한>0.5·c3 PASS.
- 권고: 5연속 누적은 통합 loopc_closure(누적 어댑터·자동 라운드)에서 운영. P2 완전 온폴리시·P4 동점 처리·R_struct(생성본체)는 통합 파이프라인 몫.
