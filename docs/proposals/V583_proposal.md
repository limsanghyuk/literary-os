# V583 제안서 — LOSDB Phase B: MigrationEngine 통합 오케스트레이터

## 배경

V582에서 SQLiteRealAdapter(SQL 레이어)의 REAL 구현과 losdb CLI가 완성됐다.
LOSDB 3-layer 아키텍처(SQL / Graph / Vector) 중 SQL 레이어만 REAL이고,
나머지 두 레이어는 BaseMigrationAdapter Mock 상태다.

V583은 3개 어댑터를 통합 조율하는 `MigrationEngine` 오케스트레이터 계층을 구축한다.
이는 향후 Graph/Vector REAL 어댑터가 추가될 때 엔진 교체 없이 "꽂기"만 하면 되는
확장 가능한 구조를 제공한다.

## 목표

- `MigrationEngine`: 복수 어댑터를 받아 순차 실행·롤백 체이닝 제공
- `MigrationPlan`: 실행할 마이그레이션 + 대상 어댑터 목록 선언
- `MigrationExecutionRecord`: 실행 결과 감사 레코드 (JSON 직렬화)
- Gate G42 `migration_engine_g42` (ADR-042, V583, L1)

## 비기능 요구사항

- 외부 의존성 없음 (stdlib only)
- LLM-0 원칙 유지
- DEV_MODE 기본값 "false" 유지
- G32 LoggingDiscipline 준수 (print() 없음)

## 제약

- Graph/Vector 어댑터는 Mock 상태로 유지 (REAL 연결 없음)
- SQLiteRealAdapter만 REAL 실행
- CI 환경에서 완전 자동 실행 가능

## 기대 효과

- 41 Gates → 41 Gates (G42 추가로 41 total)
- 5,744 → 5,780+ PASS 예상
- LOSDB 아키텍처 완성도: SQL(REAL) + Engine(REAL) + Graph/Vector(Mock-ready)
