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

## v13.45.1 — 검증 라운드 하드닝 (2026-06-20)
독립 에이전트 코드 감사 결과 발견·검증된 결함 2건 수정(+테스트 3):
- **G-A (E4 의미 정합):** strategies/base.py — ref_text 없는 후보의 E4 라벨을
  "pass"→"skipped". 미평가를 통과로 오기록하던 문제 차단(암기게이트 무력화 방지).
- **G-B (I4 fail-closed):** splits.py — work_id 누락/빈값 쌍을 단일 ""버킷으로
  병합해 train/held 누수를 유발하던 경로를 ValueError로 차단.
- 테스트 45 passed(+3: e4_skipped_recorded, i4_empty_work_id, i4_missing_work_id)
- 회귀 217 passed · Release Gate 90/97 유지(신규 회귀 0) · Integrity SHA256 2061 일치
- 감사 캐비엇(미수정·문서화): winner_pertoken=P0 미사용 DEAD CODE(GPU단 이관),
  pertoken_winrate.pairwise_winner는 scheme="sum" 여전히 허용(GPU 채점 단계 리스크),
  I1 "3중 차단"은 빌드시 1차(assert_no_sum)+ledger 하드코딩 2중이 실제(과대표현 정정).
