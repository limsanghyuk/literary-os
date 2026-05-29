# Literary OS V380 — CHANGELOG

## V380 신규 컴포넌트

### literary_system/arc/ (서사 아크 패키지 신규)

**arc/schema.py**
- `ArcAct` — 기/승/전/결 4막 Enum
- `ArcPlotEdgeType` — CAUSAL / FORESHADOW / CALLBACK / EMOTIONAL_ESCALATION
- `ArcPlotNode` — 에피소드 단위 아크 노드 (episode_id, act, reveal_budget, emotional_target, causal_inputs, tension_level, forbidden_reveals)
- `ArcPlotEdge` — 에피소드 간 방향성 엣지

**arc/causal_plot_graph.py**
- `CausalPlotGraph` — 16부작 전체 아크 방향성 그래프
  - `add_node() / get_node() / remove_node()` CRUD
  - `infer_causal_edges()` — causal_inputs 선언 기반 CAUSAL 엣지 자동 생성
  - `infer_foreshadow_edges()` — 기/승→전/결 복선 심기 + CALLBACK 역방향 쌍 자동 생성
  - `infer_emotional_escalation_edges()` — 텐션 상승 구간 EMOTIONAL_ESCALATION 엣지
  - `tension_curve()` — (episode_id, tension_level) 순서 리스트
  - `validate_act_structure()` — 4막 구조 유효성 검증
  - `sync_to_nkg(NKGGraphStore)` — NKG EpisodeNode / CausalLink 엣지 단방향 동기화

**arc/series_arc_planner.py**
- `SeriesArcPlanner` — 16부작 드라마 아크 자동 생성
  - `plan(graph=None)` — 4막 분배(기25%/승35%/전25%/결15%), S자형 텐션 곡선, 감정 목표 16종 순환, 엣지 자동 추론
  - `plan_custom(episode_specs)` — 커스텀 스펙 리스트로 그래프 생성
  - `tension_mode` — "sigmoid" | "linear" 선택

### literary_system/ledgers/ (에피소드 복선 예산 패키지 신규)

**ledgers/episode_reveal_budget.py**
- `RevealPolicy` — ALLOW / FORESHADOW_ONLY / DELAY / BLOCK 4단계 Enum
- `EpisodeRevealPolicy` — 에피소드×사실 정책 단위 (episode_id, fact_id, policy, delay_to)
- `EpisodeRevealBudget` — 전체 에피소드 복선 예산 관리자
  - `set_policy()` / `get_policy()` / `set_global_block()`
  - `check(episode_id, fact_id, direct_reveal=True)` — CLRO 진입 전 게이트
  - `check_all(episode_id, fact_ids)` — 일괄 검사 (예외 없이 위반 목록 반환)
  - `episode_summary()` / `fact_journey()` — 요약 조회
  - `from_arc_graph(CausalPlotGraph)` — 아크 노드 forbidden_reveals에서 자동 구성
- `RevealBlockedError(RevealBudgetViolationError)` — BLOCK 정책 위반 예외
- `RevealForeshadowOnlyError(RevealBudgetViolationError)` — FORESHADOW_ONLY 직접 공개 차단

### literary_system/world/ 확장

**world/character_knowledge_prose_bridge.py** (신규)
- `CharacterKnowledgeProseBridge` — KnowledgeStateTracker ↔ ProseRenderContract 브리지
  - `check(char_id, fact_id)` — READER_ONLY 누수 시 KnowledgeLeakageError 발생
  - `check_scene(char_id, fact_ids)` — 씬 단위 일괄 검사
  - `assert_no_leakage(char_ids, fact_ids)` — 복수 인물 누수 일괄 검증
  - `get_constraint(char_id, fact_id)` → KnowledgeRenderConstraint (render_mode, behavioral_hint)
  - `enrich_contract(contract, char_id, fact_ids)` — ProseRenderContract 메타데이터에 지식 제약 주입
  - `asymmetry_pressure(char_a, char_b, fact_ids)` — 지식 비대칭 압력 수치화 (0.0~1.0)
  - `blocked_facts_for(char_id)` — READER_ONLY 사실 ID 목록
- `KnowledgeLeakageError(ProseContractViolationError)` — READER_ONLY 누수 예외
- `UnawarnessViolationError(ProseContractViolationError)` — UNAWARE 위반 예외
- `KnowledgeRenderConstraint` — 인물×사실 렌더링 제약 레코드

### 5상태 → 산문 렌더 모드 매핑

| KnowledgeStatus | render_mode | behavioral_hint |
|-----------------|-------------|-----------------|
| KNOWS | direct | 해당 사실을 자연스럽게 행동/대사에 반영 |
| SUSPECTS | suggestive | 시선 회피, 말끝 흐림, 간접 질문으로 암시 |
| UNAWARE | ignorant | 해당 사실과 무관하게 행동 — 직접 언급 금지 |
| MISBELIEVES | mistaken | 잘못된 믿음 기반 행동 — 왜곡된 확신 |
| READER_ONLY | blocked | 산문 노출 절대 금지 → KnowledgeLeakageError |

## V380 버그 수정

- `CausalPlotGraph.remove_edges_for()` — `_in` 딕셔너리에서 연결 노드의 역방향 참조가 정리되지 않던 버그 수정

## 테스트 현황

| 버전 | PASS | 신규 |
|------|------|------|
| V370 기반 | 1823 | — |
| V380 신규 | +192 | 6개 테스트 파일 |
| **V380 합계** | **2015** | **+192** |
