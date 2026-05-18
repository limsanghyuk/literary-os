# Literary OS V382 — CHANGELOG

## 릴리즈 개요

**버전**: V382  
**기반**: V381 (2015 PASS, 5-gate 릴리즈 시스템)  
**핵심 변경**: 구조적 "핵심 로직 조용한 죽음" 문제 해결  
**테스트**: 2079 PASS (V381 대비 +64)

---

## 변경 사항

### 신설: literary_system/pipeline/ (V382 핵심)

SOVEREIGN_OS V305의 execution_trace / checkpoint 패턴을 Literary OS에 이식.

**literary_system/pipeline/pipeline_state.py**

- `LiteraryPipelineState` — 파이프라인 실행 추적 Pydantic 상태 모델
  - `execution_trace: List[str]` — 노드별 실행 흔적 (타임스탬프 포함)
  - `checkpoints: Dict[str, Dict]` — 인메모리 체크포인트
  - `last_good_node: str` — 마지막 성공 노드
  - `last_disk_checkpoint_path: str` — 디스크 autosave 경로
- `append_trace(state, message)` — 실행 흔적 기록 (전 노드 필수 호출)
- `save_literary_checkpoint(state, node_name, fields)` — 인메모리 상태 스냅샷
- `restore_literary_checkpoint(state, node_name)` — 체크포인트 복원
- `autosave_literary_state(state, label, status, out_root)` — 디스크 영속성
- `prune_trace(state, keep)` — trace 메모리 정리 (최근 N개 유지)
- `run_minimal_pipeline(seed_text, episodes, out_root)` — Gate 6 전용 최소 실행기

**literary_system/pipeline/__init__.py**  
모든 공개 심볼 export.

### 수정: build_opening_orchestrator.py

V382 execution_trace 이식:
- `pipeline_state: LiteraryPipelineState` 인스턴스 변수 추가
- `run_quick()` 내 모든 주요 노드에 `append_trace()` + `save_literary_checkpoint()` 추가
- `run_quick()` 반환 dict에 `pipeline_trace`, `pipeline_checkpoints` 추가
- 트레이스 노드: SeedCompiler → StandardLiteraryAnalyzer → StyleDNAEngine → V312Bridge → Episode_01~03

### 신설: literary_system/gates/release_gate.py Gate 6

`_gate_pipeline_survival()` — 파이프라인 핵심 로직 생존 게이트:
- `run_minimal_pipeline()` 실행 후 `execution_trace` 검사
- 검증 대상: SeriesArcPlanner, CausalPlotGraph, EpisodeRevealBudget, KnowledgeStateTracker, CharacterKnowledgeProseBridge
- 하나라도 trace에 없으면 FAIL
- 버전 문자열 V381 → V382 갱신

### 신설: tests/test_v382_pipeline_survival.py

총 64개 테스트 추가:

1. **TestPipelineStateModule** (10) — LiteraryPipelineState 기본 동작
2. **TestCheckpointSystem** (9) — save/restore/autosave 검증
3. **TestPipelineStructureGuarantee** (17) — 소스 파일 구조 직접 검증  
   - `src.index("X") < src.index("Y")` 패턴으로 파이프라인 순서 보증  
   - SOVEREIGN_OS V305 테스트 패턴 이식
4. **TestCoreLogicSurvival** (14) — 실제 실행 trace 기반 생존 매트릭스
5. **TestForbiddenPatterns** (8) — LLM-0 위반·전역 오염 패턴 침투 방지
6. **TestMinimalPipelineIntegration** (6) — run_minimal_pipeline() 통합 테스트

---

## 해결된 구조적 문제

### 문제: "조용한 죽음" (Silent Death)

새로운 기능을 추가할 때 기존 핵심 모듈이 우회되거나 연결이 끊겨도 테스트가 통과되는 문제.

### 해결 3층 구조

| 층 | 메커니즘 | 파일 |
|---|---|---|
| 코드 | `append_trace()` 전 노드 필수 호출 | pipeline_state.py |
| 테스트 | `execution_trace` 기반 생존 확인 | test_v382_pipeline_survival.py |
| 게이트 | `_gate_pipeline_survival()` 릴리즈 차단 | release_gate.py |

### 원칙

> "모든 노드는 실행될 때 흔적을 남긴다. 흔적이 없으면 실행되지 않은 것이다."
> — SOVEREIGN_OS V305에서 계승

---

## 게이트 결과

```
Gates: 6/6 PASS

[llm_zero]          LLM-0 외부 호출 금지           PASS
[arc_integrity]     SeriesArcPlanner 4막 비율       PASS
[reveal_budget]     RevealBudget BLOCK 게이트       PASS
[knowledge_leakage] READER_ONLY 누수 방지          PASS
[packaging]         cli_entry 패키징 무결성          PASS
[pipeline_survival] 파이프라인 핵심 로직 생존        PASS  ← V382 신설
```

## 테스트 결과

```
V381: 2015 PASS
V382: 2079 PASS (+64)
```

---

## 계보

V312 → V313 → V320~V328 → V370 → V380 → V381 → **V382**

SOVEREIGN_OS V101 ~ V305에서 계승:
- V101: execution_trace 최초 도입
- V305: autosave_every_node, HITL Context-Aware, 파이프라인 구조 보증 테스트
- V382: Literary OS에 완전 이식
