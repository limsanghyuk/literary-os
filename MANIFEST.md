# Literary OS V328 — MANIFEST

## 릴리스 정보
- **버전**: V328
- **기반**: V327 (806 PASS) → V328 (1000 PASS)
- **신규 테스트**: +194개
- **빌드 상태**: ✅ 1000 PASS / 2 SKIP

---

## V328 신규 모듈

### 단절 해소 (Disconnection Fixes)
| 단절ID | 모듈 | 파일 |
|--------|------|------|
| C | SGOLoopBridge: E2ELoop↔SGO 통합 | `orchestrators/sgo_loop_bridge.py` |
| D | SceneGraphQueryEngine: GraphRAG 검색 | `retrieval/scene_graph_query_engine.py` |
| E | MiseEnSceneCompiler: DRSEEngine 직접 배선 | `drse/mise_en_scene_compiler.py` |
| F | CausalContinuationPlanBuilder: 핸드오프 인과 계획 | `causal/causal_continuation_plan_builder.py` |
| G | LLMNodeRouter + OllamaAdapter: 멀티 어댑터 | `llm_bridge/llm_node_router.py`, `ollama_adapter.py` |
| H | DataChunker: TraceStore→SLMBuilder 파이프라인 | `slm/data_chunker.py` |
| I | ReferencePackSteering: 분석 조향 | `analyzer/reference_pack_steering.py` |

### 신규 기능 (New Features)
| 기능 | 파일 |
|------|------|
| EmotionalMomentumTracker: 4D 감정 벡터 (DECAY=0.85, ALPHA=0.15) | `emotion/emotional_momentum_tracker.py` |
| SceneDraftOutput: Pydantic 구조화 씬 출력 스키마 | `schemas/scene_draft_output.py` |

### SGO V328 변경사항
- `mise_compiler`, `char_state_gate`, `emotion_tracker` 파라미터 추가
- `_build_prompt()`: MiseEnScene 힌트 + 감정 모멘텀 힌트 주입
- `_run_single_scene()`: EmotionalMomentumTracker.update() + SceneDraftOutput.from_scene_record() 호출
- `_DefaultSceneMetrics`: MAEOrchestrator 필요 필드 전체 구비

---

## 아키텍처 계층
```
E2ELoop
  └─ SGOLoopBridge (V328-C)
       └─ SceneGenerationOrchestrator (SGO)
            ├─ MiseEnSceneCompiler (V328-E) ──→ DRSEEngine
            ├─ SceneGraphQueryEngine (V328-D) → RelationGraphStore
            ├─ EmotionalMomentumTracker (V328-T17)
            ├─ SceneDraftOutput (V328-T17)
            ├─ LLMNodeRouter (V328-G)
            │    └─ OllamaAdapter / ClaudeAdapter / MockLLMBridge
            ├─ MAEOrchestrator → CoefficientMapper → LearnedCoefficientStore
            ├─ SelfLearningCollector (V327-P1)
            ├─ KnowledgeStateTracker (V327-P3)
            └─ ConcurrentIntentCollector + ConcurrentActionResolver (V327-P2)
DataChunker (V328-H) ──→ SLMDatasetBuilder
CausalContinuationPlanBuilder (V328-F) ──→ HandoffStore
ReferencePackSteering (V328-I) ──→ AnalyzerOrchestrator
```

---

## 테스트 분포
| 테스트 파일 | 테스트 수 |
|-------------|----------|
| test_v328_task12_mise_en_scene.py | 9 |
| test_v328_task13_graph_query.py | 7 |
| test_v328_task14_llm_router.py | 13 |
| test_v328_task15_sgo_loop_bridge.py | 10 |
| test_v328_task16_data_causal.py | 17 |
| test_v328_task17_emotion_schema.py | 38 |
| test_v328_extended_coverage.py | 56 |
| test_v328_sgo_deep_integration.py | 45 |
| V327 기존 테스트 | 806 |
| **총계** | **1000 PASS** |
