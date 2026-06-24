# Manifest — V795 (Phase E Exit · SP-E.10 졸업 릴리즈 v14.0.0)

| 항목 | 값 |
|------|----|
| 버전 | 14.0.0 |
| 태그 | v14.0.0 |
| 날짜 | 2026-06-24 |
| 단계 | Phase E Exit — SP-E.10 졸업(LLM-1 실증) |
| TC | 11,462 누적 (test_inventory.json 권위) |
| Gates | 97 (90 PASS · 잔여 7 = Phase D 미완 WIP) |
| ADR | ADR-249 (SP-E.10 졸업) |
| 무결성 | SHA256SUMS.txt 2,102 항목 |
| 증거 원장 | tools/loop_c_4070_kit/round_records_v3.json |

## SP-E.10 졸업 달성 (집 RTX 4070 실측 · graduation_invariant 6/6 · violations 0)

- [x] per-token loop-C show/tell **5라운드 연속 ADOPT** (W₁ 0.600→0.620→0.644→0.708→0.808)
- [x] 전 라운드 W₁ CI하한 > 0.5
- [x] 전 라운드 length_rule_rate = 0 (완전 길이중립)
- [x] 전 라운드 c3 PASS
- [x] Σ held 쌍수 = 1,250 ≥ 250
- [x] 개발자 `loopc_closure.py::graduation_invariant` 교차통과 → exit_version = v14.0.0

## 누적 진척 (V792~V795)

- V792 — P0 선호쌍 빌더 learning/pairing/ (I1~I5 불변식 코드화)
- V793 — 전략 후보 생성기 p1~p4 실구현
- V794 — c3 생성배선 + 누적 어댑터 체이닝 + graduation_invariant
- **V795 — SP-E.10 졸업 / Phase E Exit (v14.0.0)**

## 경계 (조기 성공 선언 금지)

- 졸업 = show/tell 한 craft 축. 거시 기획(작가팀 대체)은 차기 단계(LLM-2 거시플래너).
- rejected = AI 생성 평이체. 인간 명작 직접대조는 미래 시험.
- floor는 방향 쏠림 미차단(3-전문가팀 심의) → 차기 단계 양성축·축간 균형 메타게이트.
