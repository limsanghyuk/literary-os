# Literary OS V530 — Phase 4 GIG SP1 릴리즈 노트

**버전:** 5.3.0 (V530)  
**릴리즈 일자:** 2026-05-17  
**테스트:** 5097 PASS / 20 SKIP / 0 FAIL  
**기준선:** V525 (5061 PASS) → +36 PASS  

---

## Phase 4 GIG (Graph Intelligence Gate) SP1 개요

GitNexus/OpenCode 아키텍처에서 영감을 받아 Literary OS에 서사 지식 그래프 인텔리전스를
도입하는 Phase 4의 첫 번째 서브페이즈. 씬 수정 전 나레이티브 블래스트 반경을 계산하고
Plan→Build→Gate 프로토콜을 강제하는 Gate26을 구현한다.

---

## 신규 패키지: `literary_system/graph_intelligence/`

### V526 — NarrativeGraphSchema (`narrative_graph_schema.py`)
- 노드 타입 10종: CHARACTER / SCENE / EVENT / SECRET / REVEAL / MOTIF /
  RELATIONSHIP / EMOTION_PRESSURE / TIME_DELTA / DIALOGUE_INTENT
- 엣지 타입 10종: CAUSES / KNOWS / HIDES / REVEALS / DEPENDS_ON /
  CONTRADICTS / ESCALATES / RELIEVES / FORESHADOWS / ECHOES
- `NarrativeImpactReport` 데이터클래스 + `summary()` 메서드

### V527 — NarrativeGraphStore (`narrative_graph_store.py`)
- 인메모리 Python dict 기반 그래프 (adj + radj 인덱스)
- BFS `neighbors()` / `reverse_neighbors()` depth-N 탐색
- `nodes_by_type()` / `edges_by_type()` / `connected_scenes()` API
- 노드 삭제 시 연결 엣지 자동 cascade 제거

### V528 — NarrativeGraphIndexer (`narrative_graph_indexer.py`)
- `IndexInput` DTO — NIL 루프 출력 구조 미러링
- 씬/캐릭터/이벤트/시크릿/리빌/모티프/관계/감정압/시간델타/대화의도 자동 인덱싱
- 멱등(idempotent) + 점진적(incremental) 설계
- LLM-0 준수 (ADR-015)

### V529 — NarrativeImpactAnalyzer (`narrative_impact_analyzer.py`)
- depth-1 직접 / depth-2 간접 블래스트 반경 BFS 계산
- 리빌 노드 자동 감지
- 포어섀도우 브레이크 감지 (FORESHADOWS 엣지 순회)
- 위험 점수 공식: `min(direct×0.20 + indirect×0.08 + reveals×0.30 + breaks×0.25, 1.0)`
- 위험 레벨: critical/high/medium/low → decision: hold/split_required/review/proceed

### V529b — SceneChangePreGate / Gate26 (`scene_change_pre_gate.py`)
- G26-1: direct_impact_count ≤ 15
- G26-2: reveal_count ≤ 3
- G26-3: foreshadow_break_count ≤ 2
- G26-4: risk_score ≤ 0.75
- `Gate26Result.summary()` 인간 가독 보고서
- 임계값 인스턴스별 오버라이드 지원

### V530 — 테스트 + ADR-023
- `tests/test_v526_v530_narrative_graph.py` — 36종 전체 PASS
- `docs/adr/ADR-023-narrative-graph-intelligence.md` — 설계 결정 문서화

---

## 테스트 통계

| 테스트 클래스 | 수량 | 결과 |
|-------------|------|------|
| TestNarrativeGraphSchema | 8 | ✓ |
| TestNarrativeGraphStore | 8 | ✓ |
| TestNarrativeGraphIndexer | 9 | ✓ |
| TestNarrativeImpactAnalyzer | 6 | ✓ |
| TestSceneChangePreGate | 5 | ✓ |
| **합계** | **36** | **ALL PASS** |

---

## 다음 개발 기준선 (SP2)

- 버전: 5.3.0 (V530)
- 대상: V531~V534 CodeDependencyGraph + StagePatchImpactCalculator + PlanBuildProtocol
- Gate27 (코드 의존성 게이트) 추가 예정
