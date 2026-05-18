# CHANGELOG — V546 Cleanup (Phase 6 Stage A)

**릴리즈일**: 2026-05-17  
**버전**: 6.0.0 (v5.5.1 → v6.0.0)  
**기준**: V545 HF (5210 PASS)

## Phase 6 Stage A 해소 항목

| 문제 | 해소 모듈 | ADR |
|------|-----------|-----|
| P1: CIM ↔ NarrativeGraph 단절 | GraphSyncOrchestrator | ADR-027 |
| P2: 이중 업데이트 오버헤드 | GraphSyncOrchestrator | ADR-027 |
| P3: Gate25~28 release_gate 미등록 | GateHierarchyManager + release_gate 확장 | ADR-028 |
| P4: NIL × PBP 통합 정책 | ADR-029 (문서) | ADR-029 |
| P5: LLM-0 정적 시행 장치 부재 | LLM0StaticGate | ADR-031 |
| P6: AutoRepair 5단계 안전망 미완 | SafetyAugmentedAutoRepair | ADR-030 |
| P7: ADR 목록 수동 관리 | ADRIndexGenerator | — |
| P8: Retroactive Blueprint 미등록 | CHANGELOG_V546.md + ADR-027~031 정식 등록 | — |

## 신규 모듈 (5개)

- `literary_system/graph_intelligence/graph_sync_orchestrator.py`
- `literary_system/graph_intelligence/gate_hierarchy_manager.py`
- `literary_system/graph_intelligence/llm0_static_gate.py`
- `literary_system/graph_intelligence/asd/safety_augmented_auto_repair.py`
- `literary_system/graph_intelligence/adr_index_generator.py`

## ADR 신설 (5건)

- ADR-027: CIM-NarrativeGraph 단일 동기화 채널
- ADR-028: Gate 계층 L1~L4 통합 카탈로그
- ADR-029: NIL × PlanBuildProtocol 통합 정책
- ADR-030: AutoRepair 5단계 안전망
- ADR-031: LLM-0 정적 분석 게이트

## release_gate 확장

Gate 22개 → 27개 (Gate25~28 + LLM0Static)
