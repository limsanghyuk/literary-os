# Literary OS V360 — 파일 매니페스트

## 디렉토리 구조

```
literary_system/
├── nkg/
│   ├── __init__.py                    # V360 alias export
│   ├── schema.py                      # 확장 노드/엣지 타입
│   ├── graph_store.py                 # V360 전용 쿼리 확장
│   ├── staleness.py                   # DKGStalenessTrackerV2 + LRU 캐시
│   ├── semantic_model.py              # 3단계 상태 머신
│   ├── change_detector.py             # 씬 변경 감지 + dry-run
│   ├── adapters/
│   │   └── scene_node_adapter.py      # V329 레거시
│   ├── cluster/
│   │   └── character_cluster.py       # Leiden 알고리즘 (순수 Python)
│   ├── process/
│   │   └── process_detector.py        # BFS 씬 흐름 탐지
│   └── search/
│       └── engine.py                  # BM25 + LightVector RRF K=60
├── gdap/
│   ├── schema.py                      # DKG 노드/엣지 (V350)
│   ├── graph_store.py                 # DKG 그래프 스토어
│   ├── staleness.py                   # DKG Staleness (V350)
│   ├── guardrails.py                  # GR-01~GR-05
│   ├── blast_radius.py                # BlastRadiusCalculator v2
│   ├── plan_gate.py                   # PlanBuildGate v2
│   └── pipeline.py                    # DKGPipeline v2 (7단계)
├── scope/
│   ├── resolver.py                    # NarrativeScopeResolver
│   └── plugins/
│       ├── genre_plugin_literary.py
│       ├── genre_plugin_noir.py
│       ├── genre_plugin_fantasy.py
│       ├── genre_plugin_romance.py
│       └── genre_plugin_historical.py
└── contract/
    └── bridge.py                      # ContractBridge v1

tests/
├── conftest.py                        # collect_ignore (레거시 격리)
├── test_v360_cluster.py               # CharacterClusterDetector (26)
├── test_v360_process.py               # NKGProcessDetector (25)
├── test_v360_guardrails.py            # NKGGuardrails (35)
├── test_v360_staleness.py             # DKGStalenessTrackerV2 (24)
├── test_v360_scope.py                 # NarrativeScopeResolver (32)
├── test_v360_semantic_model.py        # NKGSemanticModel (25)
├── test_v360_search.py                # NKGSearchEngine (22)
├── test_v360_contract.py              # ContractBridge v1 (22)
├── test_v360_pipeline.py              # DKGPipeline v2 (30)
├── test_v360_blast_radius.py          # BlastRadiusCalculator (12)
├── test_v360_graph_store.py           # NKGGraphStore V360 (21)
├── test_v360_schema.py                # V360 Schema (35)
├── test_v360_integration.py           # E2E 통합 (25)
├── test_v360_staleness_extended.py    # Staleness 심화 (19)
├── test_v360_search_extended.py       # Search 심화 (23)
├── test_v360_scope_extended.py        # Scope 심화 (38)
└── test_v360_contract_extended.py     # Contract 심화 (35)
```

## 테스트 통계
- 총 PASS: 1500
- SKIP: 2 (레거시 호환 테스트)
- 실행 시간: ~1.6초
