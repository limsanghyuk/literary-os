# 2026-06-21 SP-E.9 5라운드 누적(A) + 통합 인계(B)

## A. 생산혼합 5라운드 — 5/5 ADOPT (4070 단독)
독립 무작위 분할(work-level, held 250) 5회, 각 base에서 epochs=1. per-token 판정.
| 라운드 | per-token W0→W1 | dW_pt | KL |
|---|---|---|---|
| 1 | 0.508→0.708 | +0.200 | 0.060 |
| 2 | 0.448→0.708 | +0.260 | 0.071 |
| 3 | 0.496→0.720 | +0.224 | 0.079 |
| 4 | 0.456→0.680 | +0.224 | 0.066 |
| 5 | 0.468→0.724 | +0.256 | 0.072 |
- **5/5 adopt(롤백0).** W0~0.46(찍기)→W1~0.71 수렴, dW_pt+0.20~0.26, KL 0.06~0.08. 게이트 안정성 실증.
- held=250 per-token W1≈0.71 → 95% CI 하한 ≈0.65 **>0.5** (LADDER §3.3 통과). 길이매칭(tokΔ=0)→길이단순규칙 재현율 0.5 **≤0.60** 통과.

## LADDER §3.3 졸업 계약 대조
| 항목 | 계약 | 실측 | |
|---|---|---|---|
| adopt 라운드 | ≥5 연속 | 5/5 | ✅ |
| held n | ≥250 | 250 | ✅ |
| per-token W CI하한 | >0.5 | ~0.65 | ✅ |
| 길이규칙 재현율 | ≤0.60 | 0.50 | ✅ |
| c3 비퇴행 | PASS | R_path PASS(P3), R_struct=통합몫 | △ |
| KL≤τ | ≤0.50 | 0.06~0.08 | ✅ |

## SP-E.9 전체 궤적 (4070 단독, A100/H100·RunPod 불요)
Round#2 명작닻=길이착시 ROLLBACK(per-token dW0) → P1 셔플=메커니즘(dW+0.05,KL0.41과적합) → P3 craft=기교학습(dW+0.40,KL0.13) → c3 R_path PASS(병리5→2) → 혼합 5/5 ADOPT(dW~0.23,KL~0.07). **깨끗한 per-token loop-C 완전 실증.**

## B. 통합 loopc_closure 인계 (남은 형식 요건)
standalone 4070 킷이 per-token loop-C를 끝까지 증명. 형식 SP-E.10 졸업의 잔여는 통합 파이프라인 몫:
1. **진짜 누적 루프**: 본 5라운드는 *base 독립*(안정성 입증). 졸업의 "5 consecutive"는 누적 어댑터 체이닝 → `loopc_closure.run_round`가 직전 어댑터 위 학습·롤백 운영.
2. **P0 생성기 실체화**: 본 세션이 P1(인과셔플)·P3(show/tell)·P2(구체vs평이) 생성기를 standalone로 구현·검증. `learning/pairing/strategies/{p1,p3,p2}.py`(현 스텁)에 이식. P2 완전 온폴리시(현 모델 생성)·P4 동점 처리 추가.
3. **완전 c3**: R_struct(callback/payoff/tension_band)는 생성본체 계획타깃 필요 → T3 7-pass 출력 씬을 `structural_nonregression`에 연결.
참조 구현: `tools/loop_c_4070_kit/`(train_4070_p0.py per-token+KL, c3_check.py R_path, RUN_ACCUMULATE 5라운드). 데이터·어댑터는 로컬(verbatim·가중치 비커밋).

## 결론
**per-token loop-C가 4070 단독으로 졸업급 안정성(5/5 adopt)에 도달.** 형식 SP-E.10 Exit = 통합 누적루프+완전c3+P0이식 후 발행.
