# DESIGN-GRADUATION-V2 — SP-E.10 졸업 프로토콜 보강 (실측 기반)

상태: 제안 · 2026-06-21 · 기준 SP-E.10 누적5R 실측(ab3735c). **게이트 완화 아님 — 설계결함 교정.**

## 0. 실측이 드러낸 결함 2건
누적5R: R1 adopt → R2~5 rollback. 원인:
- **결함A 누적 base-KL**: KL을 base 고정기준으로 재면 누적 체이닝서 단조증가(0.06→6.4) → τ초과 불가피. *증분 드리프트가 아니라 누적 거리를 잰 것 = 측정 오설계.*
- **결함B 포화 신호 + 5-improving 기준**: W가 2~3R만에 1.0 포화. "매 라운드 향상"은 포화 신호서 원리적 불가. + 포화 후 full-epoch 학습은 과적합(rewards/rej−220·entropy 3.6→0.81)만 유발.

## 1. 교정 (원리적)
### C1. per-round KL (base→직전 어댑터)
KL을 **직전 adopt 어댑터 기준**으로 측정(증분 드리프트). 누적 누설 은폐 방지 위해 base-KL은 *보조 로그*로 병행하되 게이트는 per-round. → 정상 증분이면 통과, 과적합 폭주는 per-round KL도 커서 여전히 차단(안전 유지).
### C2. 포화-후-유지(mastery-then-maintain) 기준
"5 연속 향상" → **"마스터 도달 후 유지"**:
- 마스터 = W₁ ≥ W_MASTER(0.95) ∧ c3 PASS ∧ per-round KL≤τ.
- 졸업 = 마스터 도달 후 잔여 라운드에서 **W 비퇴행(≥마스터−tol) ∧ c3 PASS ∧ per-round KL≤τ** 유지(롤백0). 추가 향상 불요(포화는 정상).
### C3. 과적합 차단 (마스터 후 유지모드)
W≥0.95 도달 시 학습을 **early-stop 또는 lr/beta↓ 유지학습**으로 전환 → rejected 짓밟기·entropy붕괴 방지. (현 full-epoch가 R3~5 과적합 원인.)

## 2. ★정직한 상한 (핵심)
합성 이진-craft 신호(show/tell·구체/평이·셔플)는 **8B가 1~2R만에 마스터하는 저차원 선호**다. per-round KL+마스터기준으로 "포화 유지형 졸업"은 가능하나, 그건 *"쉬운 신호를 마스터하고 유지함"*이지 *"인간 명작 수준으로 성장"*이 아니다.
→ **진짜 LLM-2 졸업은 더 고차원 신호(실 명작 품질 변별 = 최종시험 영역)** 필요. 본 v2는 "프로토콜이 포화 신호를 정직하게 졸업처리"하게 만드는 것이지, 천장을 올리는 게 아님(ADR-243 정합).

## 3. graduation_invariant 변경안
- `kl` 입력을 `kl_per_round`로(직전 어댑터 기준). base-KL은 audit 필드.
- 불변식: ①말미연속 **non-degrade**(adopt 또는 maintain)≥consec ②rollback0 ③Σpairs≥250 ④W₁ CI하한>0.5 ⑤length-rule≤0.6 ⑥c3 PASS ⑦per-round KL≤τ ⑧마스터(W≥0.95) 1회 이상 달성.
- decision: adopt(향상)|maintain(마스터유지)|rollback(퇴행/드리프트/c3실패).

## 4. 검증 절차 (4070)
개정 키트(train_4070_cumulative_v2): per-round KL + 마스터시 early-stop. 5R 재실행 → maintain 연속이면 졸업. 단 §2 상한 명시 보고.
