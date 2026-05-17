# Literary OS V382 — 개발자 컨텍스트

## 빠른 시작

```bash
pip install -e ".[dev]"
pytest tests/ -q                     # → 2015 passed
python tools/run_release_gate.py     # → {"status": "pass", "gates_passed": 5}
python tools/run_runtime_smoke.py    # → 6/6 ok
```

## 핵심 설계 원칙

**LLM-0**: 복선/지식/아크 계산은 모두 로컬. LLM은 산문 생성에만 선택적으로 호출.

**V312 연결**: `SOVEREIGN_BACKEND_PATH` 환경변수로 외부 V312 엔진 연결 가능.
미설정 시 design-layer-only 모드로 동작 (graceful fallback).

```bash
export SOVEREIGN_BACKEND_PATH=/path/to/SOVEREIGN_OS_V312/backend
```

## 계보 (V313 → V381)

| 버전 | 핵심 추가 |
|------|-----------|
| V312 | SOVEREIGN_OS 런타임 (외부 연결) |
| V318 | ClosedLoopRenderOrchestrator |
| V325 | SceneGenerationOrchestrator, SelfLearningCollector |
| V326 | CharacterIntentAgent, MultiLLMRouter |
| V328 | LLMNodeRouter, ProseRenderContract 게이트 |
| V350 | NKGGraphStore, GDAP |
| V360 | KnowledgeStateTracker (5상태) |
| V370 | ContractBridge (GPT-Claude 공유 IR) |
| V380 | SeriesArcPlanner, EpisodeRevealBudget, CharacterKnowledgeProseBridge |
| **V381** | **Release Gate, CI, GitNexus, 5건 버그 수정** |

## GitNexus — 코드 인덱싱

GitNexus는 이 레포의 심볼 그래프를 인덱싱하여 Claude가 코드 구조를 빠르게 파악하도록 돕습니다.

### 초기 설정 (최초 1회)

```bash
# Node.js 18+ 필요
npx gitnexus analyze
```

실행 후 `.gitnexus/` 디렉터리가 생성되고 `CLAUDE.md`가 갱신됩니다.

### 주요 명령

```bash
npx gitnexus status    # 인덱스 최신 여부 확인
npx gitnexus analyze   # 코드 변경 후 재인덱싱
npx gitnexus wiki      # 자동 문서 생성
```

### Claude 사용 시

이 레포에서 작업할 때 Claude는 `.claude/skills/gitnexus/` 아래의 skill 파일을 참조합니다.
인덱스가 stale 상태이면 `npx gitnexus analyze --force`를 실행하세요.

## Release Gate

```bash
python tools/run_release_gate.py
```

5개 gate를 순차 실행:
1. `llm_zero` — 외부 LLM provider 직접 호출 0 검증
2. `arc_integrity` — 4막 비율(기25%/승35%/전25%/결15%) ±7% 이내
3. `reveal_budget` — BLOCK 정책 예외 정상 동작
4. `knowledge_leakage` — READER_ONLY 누수 방지
5. `packaging` — `cli_entry` import 성공

모든 gate 통과 시 `{"status": "pass", "gates_passed": 5}` 출력.

## 모듈 구조 (요약)

```
literary_system/
├── arc/          SeriesArcPlanner, CausalPlotGraph        [V380]
├── ledgers/      EpisodeRevealBudget                      [V380]
├── world/        KnowledgeStateTracker, KnowledgeProseBridge [V360/V380]
├── gates/        run_release_gate (5-gate)                [V381]
├── prose/        StyleDNA, AntiLLM, RhythmRewriter, Contract
├── nkg/          NKGGraphStore, EdgeInfer                 [V350]
├── compiler/     V312Bridge, PromptAssembler
├── orchestrators/ SceneGenerationOrchestrator, CharacterIntentAgent
├── llm_bridge/   LLMNodeRouter, MultiLLMRouter, ClaudeAdapter
└── trace/        SelfLearningCollector, TraceDatasetStore
```

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **literary_os_v400** (12688 symbols, 25629 relationships, 138 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/literary_os_v400/context` | Codebase overview, check index freshness |
| `gitnexus://repo/literary_os_v400/clusters` | All functional areas |
| `gitnexus://repo/literary_os_v400/processes` | All execution flows |
| `gitnexus://repo/literary_os_v400/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->


## V382 핵심 추가: 파이프라인 실행 추적 시스템

SOVEREIGN_OS V305의 execution_trace 패턴을 Literary OS에 이식.

**원칙**: '모든 노드는 실행될 때 흔적을 남긴다. 흔적이 없으면 실행되지 않은 것이다.'

### literary_system/pipeline/

- `LiteraryPipelineState` — 실행 추적 상태 모델 (execution_trace, checkpoints)
- `append_trace(state, msg)` — 노드 진입 시 흔적 기록 (전 노드 필수)
- `save_literary_checkpoint(state, name)` — 인메모리 상태 스냅샷
- `restore_literary_checkpoint(state, name)` — 체크포인트 복원
- `autosave_literary_state(state, label)` — 디스크 영속성
- `run_minimal_pipeline(seed, episodes)` — Gate 6 전용 최소 파이프라인 실행기

### Gate 6: pipeline_survival (V382 신설)

run_minimal_pipeline() 실행 후 모든 핵심 모듈이 execution_trace에 나타나는지 확인.
검증 대상: SeriesArcPlanner, CausalPlotGraph, EpisodeRevealBudget,
KnowledgeStateTracker, CharacterKnowledgeProseBridge

### 신규 개발 규칙 (V382~)

새로운 노드를 추가할 때:
1. 함수 진입 시 append_trace(state, '[Node_XXX] 설명') 반드시 호출
2. 노드 완료 시 save_literary_checkpoint(state, 'node_xxx') 저장
3. run_minimal_pipeline()에 새 노드 추가
4. test_v382_pipeline_survival.py::TestCoreLogicSurvival에 생존 테스트 추가
