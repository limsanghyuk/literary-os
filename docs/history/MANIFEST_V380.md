# Literary OS V380 — MANIFEST

## 릴리스 정보
- **버전**: V380
- **기반**: V370 (1823 PASS) → V380 (2015 PASS)
- **신규 테스트**: +192개
- **빌드 상태**: ✅ 2015 PASS / 2 SKIP / 0 FAIL

---

## V380 신규 모듈 — 서사 아크 통합

### literary_system/arc/ 패키지 (신규)

| 파일 | 설명 |
|------|------|
| `arc/__init__.py` | 패키지 공개 API |
| `arc/schema.py` | ArcAct(기/승/전/결), ArcPlotEdgeType(4종), ArcPlotNode, ArcPlotEdge |
| `arc/causal_plot_graph.py` | CausalPlotGraph — 에피소드 간 인과·복선 그래프 |
| `arc/series_arc_planner.py` | SeriesArcPlanner — 16부작 아크 자동 생성 |

### literary_system/ledgers/ 패키지 (신규)

| 파일 | 설명 |
|------|------|
| `ledgers/__init__.py` | 패키지 공개 API |
| `ledgers/episode_reveal_budget.py` | EpisodeRevealBudget — ALLOW/FORESHADOW_ONLY/DELAY/BLOCK 4단계 정책 |

### literary_system/world/ 확장

| 파일 | 설명 |
|------|------|
| `world/character_knowledge_prose_bridge.py` | CharacterKnowledgeProseBridge — 5상태 → ProseRenderContract 연결 |

---

## 아키텍처 계층

```
V380 서사 아크 통합 레이어
════════════════════════════════════════════════════════════
SeriesArcPlanner
  └─ CausalPlotGraph (16 ArcPlotNode + 자동 추론 엣지)
       ├─ infer_causal_edges()          — ArcPlotNode.causal_inputs 기반
       ├─ infer_foreshadow_edges()      — 기/승 → 전/결 복선 연결
       ├─ infer_emotional_escalation_edges() — 텐션 상승 구간 연결
       └─ sync_to_nkg(NKGGraphStore)   — NKG EpisodeNode로 단방향 동기화

EpisodeRevealBudget
  ├─ set_policy(episode_id, fact_id, ALLOW|FORESHADOW_ONLY|DELAY|BLOCK)
  ├─ check(episode_id, fact_id)        — CLRO 렌더링 전 게이트
  ├─ check_all(episode_id, fact_ids)   — 일괄 검사
  └─ from_arc_graph(CausalPlotGraph)   — 아크 노드에서 자동 구성

CharacterKnowledgeProseBridge
  ├─ check(char_id, fact_id)           — READER_ONLY 누수 차단
  ├─ check_scene(char_id, fact_ids)    — 씬 단위 일괄 검사
  ├─ assert_no_leakage(chars, facts)   — 복수 인물 누수 검증
  ├─ enrich_contract(contract, ...)    — ProseRenderContract 메타데이터 주입
  └─ asymmetry_pressure(a, b, facts)   — 지식 비대칭 압력 수치화

V370 이하 레이어 (변경 없음)
  ├─ DKGPipeline v2 (7단계)
  ├─ NKGGraphStore + EdgeInferEngine
  ├─ ProseRenderContract + CLRO v2
  ├─ KoreanAntiLLMFilter + EmotionToBehaviorRenderer
  └─ ReaderSurfaceScorer + StyleDNA v2
```

---

## 설계 원칙 준수

| 원칙 | V380 구현 |
|------|-----------|
| **LLM 0회** | 모든 arc/ledger/bridge 로직 — 완전 로컬 룰 기반 |
| **계층 누적** | V370 코드 0줄 수정 — arc/ledgers/world 레이어 추가만 |
| **코드화 우선** | RevealBlockedError/KnowledgeLeakageError — 규칙이 예외로 강제됨 |
| **ProseRenderContract 호환** | CharacterKnowledgeProseBridge.enrich_contract() 연동 |

---

## V380 목표 점수 (로드맵 대비)

| 항목 | V370 시점 | V380 목표 | V380 달성 수단 |
|------|-----------|-----------|----------------|
| 서사 아크 관리 | 8.0 | 9.8 | SeriesArcPlanner + CausalPlotGraph |
| 복선 예산 관리 | 8.5 | 10.0 | EpisodeRevealBudget 4단계 정책 |
| 캐릭터 지식 전파 | 8.5 | 10.0 | CharacterKnowledgeProseBridge |
| 서사 그래프 구조 | 8.5 | 10.0 | DKG + NKG + ArcNode 삼각 통합 |
| 테스트 체계 | 9.9 | 10.0 | 2015 PASS (목표 2000 초과) |

---

## 테스트 분포

| 테스트 파일 | 테스트 수 |
|-------------|----------|
| test_v380_arc_schema.py | 18 |
| test_v380_causal_plot_graph.py | 42 |
| test_v380_series_arc_planner.py | 44 |
| test_v380_episode_reveal_budget.py | 52 |
| test_v380_knowledge_bridge.py | 51 |
| test_v380_integration.py | 12 |
| test_v380_extended.py | 45 |
| V370 기존 테스트 | 1823 |
| **총계** | **2015 PASS** |
