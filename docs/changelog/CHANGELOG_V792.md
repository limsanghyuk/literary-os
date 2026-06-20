# CHANGELOG V792 — P0 선호쌍 빌더 (v13.45.0)

## 요약
DESIGN-P0-PAIRING-BUILDER-v1 확정안의 코드 실체화. `literary_system/learning/pairing/`
패키지로 per-token 전용 선호쌍 빌더를 구현. 불변식 I1~I5 코드화 + E4 사후 게이트.

## 추가 (learning/pairing/)
- tokenizer.py  — I5 토크나이저 잠금(tokenizer_sha 동결)
- length_match.py — I2 길이중립(token 5% HARD / char 8% SOFT)
- scoring.py    — I1 per-token 전용 + sum 차단 가드(1/3)
- splits.py     — I4 작품단위 train/held 분리(held≥250, leak fail-fast)
- strategies/   — base(파이프라인 순서강제: 길이매칭→E4) + p1/p3/p2/p4 라벨
- credit.py     — P4 크레딧 스텁(uniform; HIER-PLANNER 도입 시 교체)
- emit.py       — I3 no-verbatim ledger(텍스트 0 · 통계/해시만)
- report.py     — 임계위반·E4 reject·혼합비 실측 리포트
- builder.py    — fail-fast 오케스트레이터

## 테스트
- tests/unit/test_v792_pairing_builder.py — 42 TC (§3 최소 33 충족)
  · I1 sum차단/winner, I2 5%/8% 경계, I3 no-verbatim/ledger, I4 leak/held≥250,
    I5 tokenizer_sha, E4 암기쌍 폐기, mix/allocate, credit 스텁

## 수정 (regression, 본 변경 내 자체 발견·교정)
- G37 DuplicateZero 위반 교정: `BuildResult`→`PairBuildResult`,
  `SplitResult`→`PairSplitResult` (rlhf_dataset_builder / trace_quality_filter 와의 클래스명 충돌 제거)
- 위 충돌이 유발한 G61 C5-TotalGates 캐스케이드도 동반 해소

## 게이트
- Release Gate 90/97 (잔여 7건은 Phase D 미완 WIP: studio_api_contract,
  g80, g82, spd3_exit, spd4 g92/g93/g94 — 본 변경과 무관·기존부터 FAIL)
- G_CONNECTIVITY PASS(고립 0) · 본 변경으로 인한 신규 회귀 0

## 버전
- pyproject 13.40.0 → 13.45.0
