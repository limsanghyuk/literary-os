# CHANGELOG — V582

> 버전: 8.7.0  
> 릴리즈일: 2026-05-20  
> 브랜치: `582-sql-real-adapter`  
> 상태: **PRODUCTION READY** — 37 tests PASS / 40 Gates PASS

---

## Summary

V582는 LOSDB Phase A의 두 번째 단계입니다. V581에서 MOCK 전용 어댑터로 출발한 LOSDB에  
SQLiteRealAdapter(sqlite3 REAL 구현)와 LOSDB CLI를 추가하여 실제 마이그레이션 실행 능력을 획득합니다.

---

## 신규 파일

### `literary_system/db/sql_real_adapter.py`
- `SQLiteRealAdapter(BaseMigrationAdapter)` — sqlite3 표준 라이브러리 기반 REAL 어댑터
- MOCK=False 시 `:memory:` 또는 파일 DB에 실제 DDL 실행
- `losdb_migrations` 테이블 자동 생성/관리
- SchemaRegistry 연동 (`register` + `record_migration`)
- `list_applied()`, `table_exists()`, `close()`, `schema_info()` 제공
- 외부 의존 0 (stdlib sqlite3만 사용)

### `literary_system/db/cli.py`
- `main(argv)` LOSDB CLI 진입점 (G32 준수: `print()` 0건, `_emit()`/`sys.stdout.write()` 사용)
- 서브커맨드: `status`, `analyze`, `health`, `migrate`
- `--json` 최상위 플래그 지원 (`losdb --json status`)
- argparse 기반 파서, 반환값 0/1로 CI 통합 가능

---

## 수정 파일

### `literary_system/db/__init__.py`
- `SQLiteRealAdapter` 공개 API 추가

### `literary_system/gates/release_gate.py`
- `_gate_sql_real_adapter_g41()` 추가 (Gate 41, ADR-041, L1)
- GATES 리스트에 `sql_real_adapter_g41` 등록
- 총 게이트 수: 39 → 40

### `literary_system/gates/gate_registry.py`
- `_META`에 `db_migration_g40` (ADR-040, V581, L1) 추가
- `_META`에 `sql_real_adapter_g41` (ADR-041, V582, L1) 추가

---

## 테스트

### `tests/test_v582_sql_real_adapter.py` (신규, 37개 테스트)

| 그룹 | 범위 | PASS |
|------|------|------|
| A (TC01-08) | SQLiteRealAdapter MOCK 모드 | 8/8 |
| B (TC09-16) | SQLiteRealAdapter REAL :memory: | 8/8 |
| C (TC17-22) | 고급 기능 (close, table_exists, 상속) | 6/6 |
| D (TC23-30) | LOSDB CLI 명령 | 8/8 |
| E (TC31-37) | Gate G41 + 전체 40게이트 PASS | 7/7 |

---

## Gate

| Gate | ID | ADR | Layer | 버전 |
|------|----|-----|-------|------|
| G41 | `sql_real_adapter_g41` | ADR-041 | L1 | V582 |

---

## ADR

- **ADR-041**: LOSDB Phase A — SQLiteRealAdapter REAL 어댑터 + LOSDB CLI

---

## 릴리즈 게이트 현황

```
총 게이트: 40/40 PASS
신규: G41 (sql_real_adapter_g41)
```
