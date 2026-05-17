# Literary OS V329 — Narrative Knowledge Graph (NKG) Phase 1

## 릴리스 정보
- 버전: V329
- 날짜: 2026-05-08
- 기반: V328 (1000 PASS)
- 결과: **1082 PASS** (+82 신규, V328 회귀 0)

## 신규 구현 모듈

### literary_system/nkg/ (Stage 61 Phase 1)

| 파일 | 설명 |
|------|------|
| `schema.py` | NKGNodeType(7), NKGEdgeType(12), 노드 dataclass 7종, NKGEdge |
| `staleness.py` | NKGStalenessTracker — Dirty Flag 점진적 갱신 메커니즘 |
| `graph_store.py` | NKGGraphStore — networkx DiGraph 래퍼 + pickle 직렬화 |
| `pipeline.py` | NKGPipeline — 5단계 DAG (Phase 1~2~5 구현, 3~4 stub) |
| `adapters/scene_node_adapter.py` | SceneNodeAdapter — SceneDraftOutput → NKGSceneNode |

## 핵심 설계 결정
- **역의존성 없음**: schemas는 nkg를 모름, SceneNodeAdapter가 단방향 변환
- **V328 완전 호환**: SGO 코드 수정 0줄, 기존 1000 PASS 보존
- **Dirty Flag**: content_hash 비교로 수정된 장면만 재계산 (Incremental NKG)
- **Dual-layer 준비**: 인과(DAG)/감정/복선/참조 레이어 분리 스키마 확정

## 다음 단계 (V340)
- Phase 3 (edge_infer): CausalEdge/ForeshadowEdge LLM 추출
- Phase 4 (emotional): EmotionalEchoEdge — EmotionalMomentumTracker 직결
- 목표: 1100 PASS
