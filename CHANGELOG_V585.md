# CHANGELOG V585 (9.0.0) — 2026-05-20

## LOSDB Phase B 완료 — GraphRealAdapter (ADR-044)

### 신규
- `literary_system/db/graph_real_adapter.py` — GraphRealAdapter + GraphRecord + GraphEdgeRecord (395 lines)
- `tests/test_v585_graph_real_adapter.py` — 43개 테스트 (TC01~TC43)
- `docs/adr/ADR-044.md`
- `docs/designs/V585_design.md`
- `docs/proposals/V585_proposal.md`

### 수정
- `literary_system/db/migration_manager.py` — Migration.graph_ops: object = None 추가
- `literary_system/db/__init__.py` — GraphRealAdapter, GraphRecord, GraphEdgeRecord export
- `literary_system/gates/release_gate.py` — _gate_graph_real_adapter_g44() 추가
- `literary_system/gates/gate_registry.py` — graph_real_adapter_g44 등록
- `pyproject.toml` — version 9.0.0
- 레거시 테스트 gate count 42→43

### 핵심 수치
- 전체 테스트: 5,810+ → 5,853+ PASS
- Gates: 43 PASS (G1~G44)
- LOSDB Phase B: SQL ✅ + Vector ✅ + Graph ✅ 완료
