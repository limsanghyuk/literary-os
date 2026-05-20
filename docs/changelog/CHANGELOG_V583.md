# V583 변경 이력 — LOSDB Phase B: MigrationEngine 통합 오케스트레이터

## 릴리즈 정보

| 항목 | 값 |
|------|-----|
| 버전 | 8.8.0 |
| 태그 | v8.8.0-V583 |
| 날짜 | 2026-05-20 |
| ADR | ADR-042 |
| Gate | G42 migration_engine_g42 (L1) |

## 신규 컴포넌트

### `literary_system/db/migration_engine.py` (신규)
- `MigrationEngine`: 복수 BaseMigrationAdapter 통합 오케스트레이터
  - `execute(plan)`: MigrationPlan 순차 실행 + 실패 시 역순 롤백 체이닝
  - `rollback_plan(plan)`: MigrationPlan 역순 롤백
  - `adapter_keys()`: 등록 어댑터 키 목록
- `MigrationPlan`: 마이그레이션 실행 계획 dataclass
  - `plan_id`, `migrations`, `target_adapters`, `description`
- `MigrationExecutionRecord`: 실행 결과 감사 레코드
  - `to_json()` / `from_json()` JSON 직렬화 지원

## 수정 파일

| 파일 | 변경 내용 |
|------|-----------|
| `literary_system/db/__init__.py` | MigrationEngine, MigrationPlan, MigrationExecutionRecord export 추가 |
| `literary_system/gates/release_gate.py` | G42 `_gate_migration_engine_g42()` 추가, GATES 목록 41개 |
| `literary_system/gates/gate_registry.py` | ADR-042 / V583 / L1 등록 |
| `pyproject.toml` | 8.7.0 → 8.8.0 |
| `README.md` | 버전 뱃지 갱신 |
| `MANIFEST.md` | 41 Gates, V583 갱신 |

## 레거시 테스트 업데이트

| 파일 | 수정 |
|------|------|
| `tests/test_v582_sql_real_adapter.py` | TC35/TC37: gate count 40 → 41 |
| `tests/test_v581_db_migration.py` | total_gates 40 → 41 |
| `tests/test_v580_async_performance.py` | len(GATES) 40 → 41 |

## 테스트

- 신규: 40개 (TC01~TC40, test_v583_migration_engine.py)
- 전체: 5,784+ PASS 예상

## Gate 현황

| Gate | ID | ADR | Layer |
|------|-----|-----|-------|
| G40 | db_migration_g40 | ADR-040 | L1 |
| G41 | sql_real_adapter_g41 | ADR-041 | L1 |
| **G42** | **migration_engine_g42** | **ADR-042** | **L1** |

**총 41 Gates PASS**

## 보안 원칙

- LLM-0 원칙 유지: 외부 LLM 호출 0건
- DEV_MODE 기본값: "false" (ADR-034)
- G32 LoggingDiscipline: print() 없음, logging 모듈 사용
