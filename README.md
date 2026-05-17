# Literary OS V430 — Studio API + Docker + OTel + LLM Gateway

> **판단은 로컬, 생성만 LLM, 학습은 누적**
> V430 = V411(완전통합) + Studio API(FastAPI) + Docker + OpenTelemetry + LLM Gateway + Release Gate 8종

[![Tests](https://img.shields.io/badge/tests-2015%20PASS-brightgreen)]()
[![Version](https://img.shields.io/badge/version-4.3.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()

---

## 빠른 시작

```bash
# 1. 설치
pip install -e .
# 또는 의존성만
pip install -r requirements.txt

# LLM 어댑터 사용 시 (선택)
export ANTHROPIC_API_KEY=your_key_here

# 2. 전체 테스트 실행
pytest tests/ -q
# → 2015 passed

# 3. V380 신규 테스트만 실행
pytest tests/test_v380_*.py -v
# → 192 passed (7개 파일)
```

---

## V380 신규 기능 — 3분 예제

### 1. SeriesArcPlanner — 16부작 아크 자동 생성

```python
from literary_system.arc import SeriesArcPlanner, CausalPlotGraph

planner = SeriesArcPlanner(total_episodes=16, series_title="미스터 선샤인")
graph   = planner.plan()

# 텐션 곡선 확인
for ep_id, tension in graph.tension_curve():
    print(f"{ep_id}: {tension:.2f}")
# ep_1: 0.12  ...  ep_8: 0.85  ...  ep_16: 0.32

# 에피소드 노드 조회
node = graph.get_node("ep_1")
print(node.act)               # ArcAct.GI
print(node.emotional_target)  # "기대감"
print(node.tension_level)     # 0.12
```

### 2. EpisodeRevealBudget — 복선 예산 게이팅

```python
from literary_system.ledgers.episode_reveal_budget import (
    EpisodeRevealBudget, RevealPolicy, RevealBlockedError
)

budget = EpisodeRevealBudget()

# ep_3에서 비밀A는 암시만 허용
budget.set_policy("ep_3", "secret_A", RevealPolicy.FORESHADOW_ONLY)
# 전 에피소드에서 비밀B 완전 차단
budget.set_global_block("secret_B")

# 산문 생성 직전 게이트 검사
try:
    budget.check("ep_3", "secret_A", direct_reveal=True)
except RevealBlockedError as e:
    print(e)  # FORESHADOW_ONLY 위반

# 일괄 검사 (예외 없이 위반 목록 반환)
violations = budget.check_all("ep_5", ["secret_A", "secret_B", "fact_C"])
# → ["secret_B"]

# 아크 그래프에서 자동 구성 (node.forbidden_reveals 기반)
budget = EpisodeRevealBudget.from_arc_graph(graph)
```

### 3. CharacterKnowledgeProseBridge — 인물 지식 → 산문 제약

```python
from literary_system.world.character_knowledge_prose_bridge import (
    CharacterKnowledgeProseBridge, KnowledgeLeakageError
)
from literary_system.world.knowledge_state_tracker import KnowledgeStateTracker

tracker = KnowledgeStateTracker()
bridge  = CharacterKnowledgeProseBridge(tracker=tracker)

# READER_ONLY 누수 검사
try:
    bridge.check("eugene", "killer_identity")
except KnowledgeLeakageError as e:
    print(e)  # READER_ONLY → 산문 노출 금지

# 렌더 제약 조회
c = bridge.get_constraint("ae_shin", "war_secret")
print(c.render_mode)      # "suggestive"
print(c.behavioral_hint)  # "시선 회피, 말끝 흐림, 간접 질문으로 암시"

# ProseRenderContract에 지식 제약 주입 (원본 불변)
enriched = bridge.enrich_contract(contract, "ae_shin", ["war_secret", "identity"])

# 지식 비대칭 압력 수치화 (0.0~1.0)
pressure = bridge.asymmetry_pressure("ae_shin", "eugene", ["killer_identity"])
```

### 4. 전체 파이프라인 통합

```python
from literary_system.arc import SeriesArcPlanner
from literary_system.ledgers.episode_reveal_budget import EpisodeRevealBudget
from literary_system.world.character_knowledge_prose_bridge import CharacterKnowledgeProseBridge
from literary_system.world.knowledge_state_tracker import KnowledgeStateTracker
from literary_system.nkg.nkg_graph_store import NKGGraphStore

# 1. 아크 생성
arc    = SeriesArcPlanner(total_episodes=16, series_title="시리즈명").plan()

# 2. 복선 예산 자동 구성
budget = EpisodeRevealBudget.from_arc_graph(arc)

# 3. NKG 동기화
nkg   = NKGGraphStore()
count = arc.sync_to_nkg(nkg)  # → EpisodeNode + CausalLink + ForeshadowingOf

# 4. 인물 지식 브리지
bridge = CharacterKnowledgeProseBridge(tracker=KnowledgeStateTracker())

# 5. 에피소드별 산문 생성 루프
for ep_id, tension in arc.tension_curve():
    violations = budget.check_all(ep_id, all_facts)
    if violations:
        continue
    bridge.assert_no_leakage(char_ids, all_facts)
    # → LLM 산문 생성
```

---

## 아키텍처 레이어

```
Layer 0  │ LLM (ClaudeAdapter / MultiLLMRouter)
─────────┼──────────────────────────────────────────────────────────────
Layer 1  │ V312Bridge · PromptAssembler · ActionPacketParser
Layer 1.5│ SnapshotManager · SequencePlanner · SceneFocusInjector
─────────┼──────────────────────────────────────────────────────────────
Layer 2  │ DRSEScorer · KnowledgeBoundaryGate · SpatialConstraintGate
         │ LocalJudgmentValidator · LearnedCoefficientStore
         │ EpisodeRevealBudget                              [V380 신규]
─────────┼──────────────────────────────────────────────────────────────
Layer 3  │ MAEOrchestrator · CoefficientMapper
         │ SceneGenerationOrchestrator
         │ CharacterKnowledgeProseBridge                   [V380 신규]
─────────┼──────────────────────────────────────────────────────────────
Layer 4  │ SelfLearningCollector · MultiLLMRouter
         │ SeriesArcPlanner · CausalPlotGraph               [V380 신규]
─────────┼──────────────────────────────────────────────────────────────
Layer 5  │ NKGGraphStore (ArcPlotNode ↔ EpisodeNode 동기화)[V380 확장]
```

---

## 모듈 구조

```
literary_system/
├── arc/                              # [V380 신규] 서사 아크 패키지
│   ├── __init__.py
│   ├── schema.py                     # ArcAct · ArcPlotEdgeType · ArcPlotNode · ArcPlotEdge
│   ├── causal_plot_graph.py          # CausalPlotGraph (방향성 아크 그래프)
│   └── series_arc_planner.py         # SeriesArcPlanner (16부작 자동 생성)
├── ledgers/                          # [V380 신규] 복선 예산 패키지
│   ├── __init__.py
│   └── episode_reveal_budget.py      # EpisodeRevealBudget · RevealPolicy
├── world/
│   ├── knowledge_state_tracker.py    # KnowledgeStateTracker (V315~)
│   ├── character_knowledge_prose_bridge.py  # [V380 신규] KnowledgeProseBridge
│   └── ...
├── nkg/
│   ├── nkg_graph_store.py            # NKGGraphStore (V380 sync_to_nkg 확장)
│   └── schema.py                     # EpisodeNode · CausalLink · ForeshadowingOf
└── orchestrators/
    ├── sequence_planner.py
    └── scene_generation_orchestrator.py

tests/
├── test_v380_arc_schema.py           # 18 tests
├── test_v380_causal_plot_graph.py    # 42 tests
├── test_v380_series_arc_planner.py   # 44 tests
├── test_v380_episode_reveal_budget.py  # 52 tests
├── test_v380_knowledge_bridge.py     # 51 tests
├── test_v380_integration.py          # 12 tests
└── test_v380_extended.py             # 45 tests
```

---

## 핵심 API 레퍼런스

### `SeriesArcPlanner`

```python
SeriesArcPlanner(total_episodes=16, series_title="시리즈", tension_mode="sigmoid")
# tension_mode: "sigmoid" (S자형 곡선) | "linear" (선형)
# raises ValueError if total_episodes < 2

.plan(graph=None) -> CausalPlotGraph
# 4막 분배 기25%/승35%/전25%/결15%, 16종 감정 목표, 엣지 자동 추론

.plan_custom(episode_specs: List[Dict]) -> CausalPlotGraph
# 커스텀 스펙: {"episode_id", "title", "act", "tension_level", ...}
```

### `CausalPlotGraph`

```python
.add_node(node) / .get_node(id) / .remove_node(id)
.get_nodes_by_act(act: ArcAct) -> List[ArcPlotNode]
.add_edge(edge) / .get_edges(id, direction="out")

.infer_causal_edges() -> List[ArcPlotEdge]
.infer_foreshadow_edges() -> List[ArcPlotEdge]       # 기/승→전/결 + CALLBACK 역방향
.infer_emotional_escalation_edges() -> List[ArcPlotEdge]

.tension_curve() -> List[Tuple[str, float]]
.validate_act_structure() -> bool
.sync_to_nkg(nkg_store) -> int                        # 동기화된 노드 수 반환
```

### `EpisodeRevealBudget`

```python
.set_policy(episode_id, fact_id, policy, delay_to=None, reason="")
.set_global_block(fact_id) / .remove_global_block(fact_id)
.get_policy(episode_id, fact_id) -> RevealPolicy      # 기본값: ALLOW

.check(episode_id, fact_id, direct_reveal=True)
# BLOCK → RevealBlockedError
# FORESHADOW_ONLY + direct_reveal=True → RevealForeshadowOnlyError

.check_all(episode_id, fact_ids, direct_reveal=True) -> List[str]
.episode_summary(episode_id) -> Dict[str, RevealPolicy]
.fact_journey(fact_id) -> List[Tuple[str, RevealPolicy]]

@classmethod
.from_arc_graph(graph: CausalPlotGraph) -> EpisodeRevealBudget
```

### `CharacterKnowledgeProseBridge`

```python
CharacterKnowledgeProseBridge(tracker: KnowledgeStateTracker)

.check(char_id, fact_id, allow_suspect=True)           # READER_ONLY → KnowledgeLeakageError
.check_scene(char_id, fact_ids) -> List[str]           # 위반 fact_id 목록
.assert_no_leakage(char_ids, fact_ids)                 # 첫 위반 시 예외

.get_constraint(char_id, fact_id) -> KnowledgeRenderConstraint
# .render_mode: "direct"|"suggestive"|"ignorant"|"mistaken"|"blocked"

.enrich_contract(contract, char_id, fact_ids) -> ProseRenderContract  # 원본 불변
.asymmetry_pressure(char_a, char_b, fact_ids) -> float  # 0.0~1.0
.blocked_facts_for(char_id) -> List[str]
```

---

## 5상태 → 산문 렌더 모드 매핑

| KnowledgeStatus | render_mode | behavioral_hint |
|:----------------|:------------|:----------------|
| `KNOWS` | `direct` | 해당 사실을 자연스럽게 행동/대사에 반영 |
| `SUSPECTS` | `suggestive` | 시선 회피, 말끝 흐림, 간접 질문으로 암시 |
| `UNAWARE` | `ignorant` | 해당 사실과 무관하게 행동 — 직접 언급 금지 |
| `MISBELIEVES` | `mistaken` | 잘못된 믿음 기반 행동 — 왜곡된 확신 |
| `READER_ONLY` | `blocked` | 산문 노출 절대 금지 → `KnowledgeLeakageError` |

---

## 설계 원칙

1. **LLM-0 라우팅**: 복선/지식 게이팅, 아크 구조 계산은 모두 로컬. LLM은 산문 생성만.
2. **불변 계약**: `enrich_contract()`는 원본을 수정하지 않음 (`dataclasses.replace` 사용).
3. **계층적 예외**: `RevealBudgetViolationError` → `RevealBlockedError` / `RevealForeshadowOnlyError`.  `ProseContractViolationError` → `KnowledgeLeakageError` / `UnawarnessViolationError`.
4. **단방향 NKG 동기화**: Arc → NKG 방향만. NKG 변경이 Arc를 오염시키지 않음.
5. **4막 비율 고정**: 기25% / 승35% / 전25% / 결15% — `ACT_RATIOS` 상수로 관리.

---

## 테스트 현황

| 버전 | PASS | 신규 테스트 파일 |
|:-----|-----:|:----------------|
| V370 기반 | 1823 | — |
| V380 신규 | +192 | `test_v380_arc_schema.py` (18) |
| | | `test_v380_causal_plot_graph.py` (42) |
| | | `test_v380_series_arc_planner.py` (44) |
| | | `test_v380_episode_reveal_budget.py` (52) |
| | | `test_v380_knowledge_bridge.py` (51) |
| | | `test_v380_integration.py` (12) |
| | | `test_v380_extended.py` (45) |
| **V380 합계** | **2015** | **7개 파일** |

```bash
# 커버리지 포함 실행
pytest tests/ --cov=literary_system --cov-report=term-missing -q
```

---

## V370 → V380 마이그레이션

V370 코드는 변경 없이 V380과 호환됩니다. V380은 신규 패키지(`arc/`, `ledgers/`)와
기존 `world/` 브리지 클래스를 추가하는 방식으로만 확장합니다.

```python
# V370 기존 코드 — 그대로 동작
from literary_system.world.knowledge_state_tracker import KnowledgeStateTracker
tracker = KnowledgeStateTracker()

# V380 확장 — 기존 tracker 재사용
from literary_system.world.character_knowledge_prose_bridge import CharacterKnowledgeProseBridge
bridge = CharacterKnowledgeProseBridge(tracker=tracker)
```

---

## 버전 히스토리

| 버전 | PASS | 핵심 기능 |
|:-----|-----:|:----------|
| V325 | 722 | SceneGenerationOrchestrator · SelfLearningCollector |
| V326 | 865 | MultiLLMRouter · GeminiAdapter |
| V328 | 1023 | ProseRenderContract · SurfaceOnlyContractGate |
| V350 | 1082 | NKGGraphStore · KnowledgeBoundaryGate · GDAP |
| V360 | 1421 | KnowledgeStateTracker · CharacterKnowledgeGraph |
| V370 | 1823 | ProseRenderContract V2 · EpisodeNode NKG |
| **V380** | **2015** | **SeriesArcPlanner · EpisodeRevealBudget · CharacterKnowledgeProseBridge** |

---

## V380 목표 점수

| 평가 항목 | V370 | V380 목표 | 달성 |
|:----------|-----:|----------:|:-----|
| 서사 아크 관리 | 7.5 | 9.8 | ✅ |
| 복선 예산 관리 | 8.5 | 10.0 | ✅ |
| 캐릭터 지식 전파 | 8.0 | 10.0 | ✅ |

---

*Literary OS V430 — Released 2026-05-15*
                                               