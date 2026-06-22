# 2026-06-21 SP-E.10 누적 5라운드 실측 — graduated=False (게이트 정상작동)

V794 누적 어댑터 체이닝 5라운드(4070, base→r1→...→r5). graduation_invariant 공식 판정.

## 결과
| R | W0→W1 | KL(base) | c3 | 판정 |
|---|---|---|---|---|
| 1 | 0.508→0.728 | 0.064 | PASS | **adopt** |
| 2 | 0.728→0.976 | 0.625 | PASS | rollback |
| 3 | 0.984→1.000 | 3.097 | PASS | rollback |
| 4 | 1.000→0.996 | 5.266 | PASS | rollback |
| 5 | 0.996→0.996 | 6.413 | PASS | rollback |

**graduation_invariant: graduated=False** (말미 연속 adopt 0<5). exit_version=None.

## 진단 — 실패 아니라 게이트가 진짜 문제 적발
1. **신호 포화**: W 0.51→1.0을 2~3라운드 만에 도달. 혼합(P1+P3+P2)이 너무 쉬워 모델이 금방 마스터 → 이후 향상 여지 0 → adopt 불가.
2. **누적 base-KL 폭발**: 누적 체이닝이라 어댑터가 base에서 점점 멀어짐 → base-anchored KL 0.06→6.4 무한 증가 → τ=0.50 초과 rollback. rewards/rejected −220·entropy 3.6→0.81 = 과적합/보상해킹 → 게이트 정확 차단.

## 함의 (졸업 프로토콜 재설계 필요)
"5 consecutive adopt(매 라운드 향상)"는 현 셋업과 구조적으로 충돌:
- **신호가 포화**되면 향상 불가 → 매 라운드 더 어려운/신선한 신호 필요(같은 혼합 반복 금지).
- **누적 base-KL은 단조증가** → (a)per-round KL(직전 어댑터 기준)로 전환 or (b)포화 후엔 KL τ 완화/누적 예산 or (c)학습 정규화(lr/beta↓)로 드리프트 억제.
- **또는 졸업 기준 재정의**: W 포화(≥0.95)+c3 PASS면 "마스터"로 인정(추가향상 불요).

## 핵심 (정직)
- per-token loop-C 메커니즘 자체는 건전(R1 + 앞선 5 독립라운드 모두 clean adopt, KL 0.06~0.08).
- 문제는 **누적 졸업 프로토콜의 KL/포화 처리** — V794 graduation_invariant가 이를 정확히 적발(게이트 신뢰성 입증).
- SP-E.10 졸업 미달 → 프로토콜 보강(per-round KL/포화기준) 후 재라운드 권고.
