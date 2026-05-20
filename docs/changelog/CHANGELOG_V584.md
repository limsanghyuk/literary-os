# CHANGELOG V584 (8.9.0) — VectorRealAdapter

**날짜**: 2026-05-20  
**태그**: v8.9.0-V584  

## 신규

### literary_system/db/vector_real_adapter.py (신규, 359 lines)
- `VectorRealAdapter` — LOSDB vector 레이어 REAL 구현
- `VectorRecord` — 벡터 레코드 데이터클래스
- `_cosine_similarity()` — numpy-optional 코사인 유사도
- `_l2_distance()` — numpy-optional L2 거리
- numpy 설치 시 자동 가속, 없으면 순수 Python fallback
- JSON 영속화 (`save()` / `load()`)
- rollback 전략: apply() 전 스냅샷 → rollback() 복원
- Gate G43 (ADR-043) 7체크포인트 ALL PASS

### tests/test_v584_vector_real_adapter.py (신규, 354 lines)
- TC01~TC40 + TC12b/TC29b/TC34b (총 43개 PASS)

### docs/adr/ADR-043.md (신규)

## 수정

### literary_system/db/migration_manager.py
- `Migration.vector_ops: object = None` 필드 추가 (하위 호환)

### literary_system/db/__init__.py
- `VectorRealAdapter`, `VectorRecord` export 추가

### literary_system/gates/release_gate.py
- `_gate_vector_real_adapter_g43()` 추가 (7체크포인트)
- GATES 42번째 항목 추가

### literary_system/gates/gate_registry.py
- `vector_real_adapter_g43`: (ADR-043, V584, L1) 추가

### pyproject.toml
- version: 8.8.0 → 8.9.0

### 레거시 테스트 gate count 업데이트
- test_v583_migration_engine.py: 41 → 42 (3개소)
- test_v582_sql_real_adapter.py: 41 → 42 (3개소)
- test_v581_db_migration.py: 41 → 42 (1개소)
- test_v580_async_performance.py: 41 → 42 (1개소)

## Gate

| Gate | 이름 | ADR | 상태 |
|------|------|-----|------|
| G43 | vector_real_adapter_g43 | ADR-043 | PASS |

총 42 Gates PASS (G1~G43)
