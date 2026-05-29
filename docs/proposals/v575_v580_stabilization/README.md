# V575 → V580 안정화 7주 로드맵

> **합의안 v2.0** (2026-05-19) — V574 Principal Engineer Report 비판 → CSPE 감수 → 3인 최종 합의

## 문서

- [`PROPOSAL_v2.docx`](PROPOSAL_v2.docx) — 합의안 제안서 v2.0
- [`DESIGN_v2.docx`](DESIGN_v2.docx) — 시스템 설계도 v2.0
- [`V574_Principal_Engineer_Report.docx`](V574_Principal_Engineer_Report.docx) — 기반 보고서 (Critical 4 + High 6)

## 한눈에 보기

V574 (7.9.0, 690 py / 118,996 LOC, 5,471 PASS, 87% cov, 20/30 Gate)의 Critical 4건과 High 6건을 V574.1 핫픽스 + V575~V580 7주에 해소하여 V580 시점 프로덕션 A 등급 진입.

## V574 Critical 4건 매핑

| # | Critical 결함 | 합의안 매핑 |
|---|---|---|
| CR-1 | DEV_MODE 기본값 = true | **V574.1 핫픽스 0.5일** |
| CR-2 | LLM 어댑터 4세대 공존 | **V577 어댑터 통합 1.5주** |
| CR-3 | 0% 커버리지 21 파일 | **V576 Test Fortification** |
| CR-4 | 중복 클래스 88개 | **V579 Duplicate Resolution** |

## v1 → v2 변경 핵심 (13건)

| # | 범주 | V574 보고서 | v2 합의안 |
|---|---|---|---|
| C-01 | Critical 즉시 핫픽스 | V575 1주에 보안만 | **V574.1 0.5일 분리 (DEV_MODE + desc + ruff CI)** |
| C-02 | Preflight 의무화 | 미명시 | **§3 12단계 V575~V580 전수 + 위험도 R/Y/G** |
| C-03 | Survival Matrix | v1.1 유지 | **v1.2 (multiwork + 어댑터 v4 반영)** |
| C-04 | Gate Registry | V578 언급만 | **GATE_REGISTRY.py 단일 소스 + CI 강제** |
| C-05 | 어댑터 canonical | V577 후순위 | **V577 첫 1일 결정 (adapters_live/* 우선)** |
| C-06 | ADR 1~13 | retroactive 권고 | **git log + grep 자동 추출 (V578)** |
| C-08 | mypy strict | V579 일괄 | **5단계 점진 (Stage1 V576 → ... → Stage5 Phase 7)** |
| C-09 | 커버리지 | V575 88% | **V575 88% → V576 90% → V578 92% → V580 95%** |
| C-10 | 성능 베이스라인 | V580에서만 | **V575 측정 + V580 회귀 비교** |
| C-11 | multiwork 검증 | dead 분류 | **V577 첫 1일 import 그래프 검증** |
| C-12 | README 정합성 | 미명시 | **README ↔ pyproject ↔ git tag CI 강제** |

(전체 13건은 PROPOSAL_v2.docx §1 변경 이력 참조.)

## V574.1 즉시 핫픽스 (0.5일)

| # | 항목 | 파일 |
|---|---|---|
| H-01 | DEV_MODE 기본값 → false | `apps/studio_api/auth/middleware.py:29` |
| H-02 | pyproject description 갱신 | `pyproject.toml` |
| H-03 | README 버전 → V574 | `README.md` |
| H-04 | CI ruff 추가 | `.github/workflows/ci.yml` |
| H-05 | CI 버전 정합 검사 | `tools/check_version_consistency.py` (신규) |

## V575 → V580 단계 요약

| 버전 | 제목 | 기간 | 신설 게이트 | Preflight |
|---|---|---|---|---|
| V575 | Security & Hygiene | 1주 | **G32** LoggingDiscipline | 🟡 Y |
| V576 | Test Fortification | 1주 | **G33** SchemaRoundTrip, **G34** AuthRegression | 🟡 Y |
| V577 | LLM Adapter Consolidation | 1.5주 | **G35** AdapterCanonical | 🔴 R |
| V578 | Gate Registry & ADR | 1주 | **G36** GateRegistry | 🔴 R |
| V579 | Duplicate + mypy | 1주 | **G37** DuplicateZero | 🔴 R |
| V580 | Async + Performance | 1.5주 | **G38** AsyncDiscipline, **G39** PerformanceRegression | 🔴 R |

## 7개 ADR (V575~V580 신설)

| ADR | 제목 | 버전 |
|---|---|---|
| ADR-032 | Gate Registry Single Source | V578 |
| ADR-034 | LLM Adapter Canonical | V577 |
| ADR-035 | mypy Gradual Strict | V576~V580 |
| ADR-036 | Coverage Gate Progression | V575~V580 |
| ADR-037 | Preflight Protocol 의무화 | V575~V580 |
| ADR-038 | ADR Retroactive Automation | V578 |
| ADR-039 | Performance Baseline | V575/V580 |

(ADR-033은 V574에 기존 등록 유지.)

## V580 종료 조건

| # | 항목 | V574 | V580 목표 |
|---|---|---|---|
| 1 | Critical 결함 | 4건 | **0건** |
| 2 | High 결함 | 6건 | **0건** |
| 3 | Gate 등록 | 20/30 | **39/39** |
| 4 | 커버리지 | 87% | **≥ 95%** |
| 5 | 테스트 PASS | 5,471 | **≥ 6,000** |
| 6 | Studio API SKIP | 22 | **0** |
| 7 | print() 잔존 | 28 | **0** |
| 8 | 중복 클래스 | 88 | **0** |
| 9 | 어댑터 세대 | 4 | **1 (canonical)** |
| 10 | ADR 누락 | 1~13 + 032 | **0건** |

## 진입 전 Preflight 의무

각 V575~V580 단계는 Claude-Native Preflight Guide v1.1 §3의 12단계를 위험도 R/Y/G에 따라 의무 실행한다. 가이드는 [`../../workflow/PREFLIGHT_GUIDE_v1.1.md`](../../workflow/PREFLIGHT_GUIDE_v1.1.md) 참조.
