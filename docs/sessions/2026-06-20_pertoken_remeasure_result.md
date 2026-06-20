# 2026-06-20 per-token 재측정 결과 — Round#2 ADOPT-candidate는 길이 인공물 (무효)

**기준**: SGATE-v788(`ec1b5e2`) §5 절차 실행. Round#2 어댑터(lora_out_4070)로 held 56쌍 logp ledger 방출(학습 없이 측정만), `pertoken_winrate` 로직으로 재측정.

## 결과 (held 56쌍, ref-win = 모델이 명작을 draft보다 위로 랭크한 비율)
| 방식 | W0 | W1 | dW |
|---|---|---|---|
| sum (길이편향, Round#2 방식) | 0.161 | 0.357 | **+0.196** |
| **per-token (길이정규화)** | **0.000** | **0.000** | **+0.000** |
| per-token 마진(ref−draft) | -1.513 | -1.079 | +0.434 |

## 판정: LENGTH ARTIFACT — Round#2 "ADOPT-candidate" 무효
- per-token 승률이 학습 전·후 모두 **0.000**: 토큰당 기준으로 모델은 56쌍 전부에서 명작 ref를 draft 아래로 랭크(명작 각본 밀도↑ → 토큰당 logp가 일반 산문보다 낮음).
- 보고된 dW_sum +0.196은 **전적으로 길이 효과**(ref 424자 < draft 593자, sum-logp는 짧은 쪽 유리). 길이 진단: "짧은 쪽=승자" 귀무모형이 라벨 95.5% 재현.
- 미세 신호: per-token 마진은 +0.434/token 이동(학습이 모델을 명작 쪽으로 약간 밀긴 함). 그러나 승자 역전엔 한참 부족 → Round#1 패턴과 동일(마진 이동·임계 미달).

## 결론 (개발자 SGATE/DELIBERATION 검증)
- 개발자 V788 길이교란 지적 + SPE의 "명작닻 데이터 BLOCK" 판정이 **실측으로 확인**됨.
- G_LOOPC_WINRATE c1(ΔW>0)은 **per-token에서 FAIL** → 이 라운드는 ROLLBACK(어댑터 폐기).
- per-token을 ΔW 표준으로(ADR-LADDER-3) 의무화하는 근거 실증.

## 다음 (DELIBERATION-v1 §3 처방대로)
1. 페어링 재설계: **15/55/20/10**(P1 등급화열화 길이매칭 / P3 AI간 초고 주력·암기위험0 / P2 온폴리시 / P4 동점).
2. 모든 쌍 **길이매칭** + **E4 암기게이트**(memorization_gate) 통과 + 작품단위 train/held 분리.
3. 학습 시 **logp ledger(sumlogp+n_tokens) 방출** → per-token으로만 판정. held≥250.
4. c3 구조게이트 켜기(생성 씬 연결).

데이터 원칙: ledger는 logp·토큰수 숫자만(명작 원문 비포함). 본 문서 verbatim 없음.
