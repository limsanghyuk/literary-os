# CHANGELOG V586 (9.1.0) — 2026-05-20

## LOSDB Phase C 시작 — LOSDBClient Facade (ADR-045)

### 신규
- `literary_system/db/losdb_client.py` — LOSDBClient + LOSDBClientRecord
  - available_backends() / get_backend() / register_backend() / unregister_backend()
  - query_by_label(backend, label) — SQL/Vector/Graph 개별 쿼리
  - cross_query(backends, label) — 복수 백엔드 병합 쿼리
  - check_all_connections() — 전체 백엔드 연결 상태
  - schema_info() — 통합 스키마 정보
- `literary_system/db/sql_real_adapter.py` — get_rows(table) 메서드 추가
- `docs/adr/ADR-045.md`
- `docs/proposals/V586_proposal.md`
- `docs/designs/V586_design.md`
- `tests/test_v586_losdb_client.py` — 44개 테스트 PASS

### 변경
- `literary_system/db/__init__.py` — LOSDBClient, LOSDBClientRecord export 추가
- `literary_system/gates/release_gate.py` — Gate G45 추가 (총 44 Gates)
- `literary_system/gates/gate_registry.py` — G45 등록
- `pyproject.toml` — 9.0.0 → 9.1.0

### 수치
- 버전: 9.1.0
- Gates: 44 PASS (G1~G45)
- 신규 테스트: 44개
