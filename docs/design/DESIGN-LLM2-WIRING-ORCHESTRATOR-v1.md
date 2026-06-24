# DESIGN-LLM2-WIRING-ORCHESTRATOR-v1 — 고립 기관 배선 오케스트레이터 초안 설계도

- 상태: 제안(PROPOSAL · 초안) · 2026-06-24 · 기준 허브 main `85b1973` / v14.0.0 (Phase E Exit)
- 성격: 결정 문서 아님. 배선(wiring) 아키텍처 초안 — 전문가 토의 기반 수렴안. 절대 미선언.
- 연계 정본: DESIGN-LLM2-SYNOPSIS-ASSEMBLER-IO-MERGE-v1(Stage 어댑터·GenerativePort), DESIGN-LLM2-BLANK-SLOTS-v1(빈칸 5종), DESIGN-LLM2-CAPACITY-DIVISION-v1(get_episode_brief), BLUEPRINT-MASTER-ADR001-to-LLM3-v1
- 원인 문서: 2026-06-24 배선 감사 — 16기관 중 15개가 `generate_series` 경로에서 미호출(고립 섬). 본 문서가 그 배선 순서를 못 박는다.

---

## 0. 문제 정의 (구조적)

졸업(v14.0.0)은 **판단(Critic)**을 LLM화했으나, **생성 골격의 배선**은 그대로다. 코드 감사 실측(HEAD `85b1973`):

| 사실 | 근거 (file:line) |
|---|---|
| 최상위 생성기 = `DramaEpisodeGenerator.generate_series` | `pipelines/drama_episode_generator.py:242` |
| 입력 = 사람이 박은 상수 | `DramaSeriesConfig:37-48` (`logline="진실을 추적하는 검사와…"`) |
| 생성경로가 호출하는 기관 = **1개**(`EpisodeStructureCalculator`)뿐 | `scene_generation_pipeline.py:220,242` |
| 나머지 12기관 = 정의됐으나 미호출(고립) | grep: `drama_episode_generator.py`가 어느 것도 import 안 함 |
| 4기관 체인(아크→인과→리빌→지식) | `pipeline/pipeline_state.py:213 run_minimal_pipeline` — **게이트 검사용**, 산문 0 |
| 부작 간 상태 = 미스레딩(각 화 독립) | `generate_series:259-262`가 `ep_idx`만 전달 |

**문제 한 줄**: 기관은 다 있으나 **데이터가 organ→organ으로 흐르지 않는다.** "스스로 16/24부작 창작"은 ① 배선 순서(위상정렬) ② 통합 상태 버스 ③ 화↔화 피드백 — 이 셋을 못 박아야 가능하다.

---

## 1. 결정적 발견 — 통합 버스는 이미 존재한다

배선이 가능한 이유는 **중앙 상태 객체가 이미 설계돼 있고, 스칼라 기관들의 산출이 그 필드와 정확히 일치**하기 때문이다(I/O 계약 실측):

`NarrativeStateTensor` (`episode/episode_state.py:82`) 필드: `conflict_pressure`, `avg_emotional_momentum`, `scene_energy_required`, `avg_curiosity_gradient`, `active_characters`, `used_reveal_budget` …

| 스칼라 기관 | 산출 | → 텐서 필드 |
|---|---|---|
| `ConflictCollisionCalculus.calculate()` | `ConflictCollisionResult.intensity` | `conflict_pressure` |
| `EmotionalMomentumTracker.update()` | `EmotionalVector` | `avg_emotional_momentum` |
| `NarrativeTensionCurve.record()` | `TensionPoint` | `scene_energy_required` |
| `CharacterInfluenceMatrix.compute_pagerank()` | `Dict[str,float]` | 인물 티어링/`active_characters` |

그리고 `EpisodePlanner.plan(series_config, episode_idx, narrative_state)` (`episode/episode_planner.py:66`)는 **이 텐서를 읽어** 다음 화를 계획한다.

→ **결론**: 화 N의 기관들이 텐서에 스칼라를 써넣고(write-back), 화 N+1의 `EpisodePlanner`가 그 텐서를 읽으면 **화↔화 피드백 루프가 타입 정합으로 자동 성립**한다. 배선은 신규 발명이 아니라 *이미 맞물리게 설계된 톱니를 끼우는 일*이다.

---

## 2. 전문가 패널 토의 (4관점 · 심도)

배선 아키텍처를 두고 4인 가상 패널이 토의·반론·수렴했다.

### 2.1 쟁점 — "어떻게 잇는가"

**서사시스템 아키텍트**: 순서가 곧 극작이다. 거시(아크)→인과(DAG)→복선원장(16부 전역)→화별 비트→미시→씬. **복선원장(PayoffScheduler)은 루프 밖**에 둬야 한다. 화 루프 안에 넣으면 16부 전역 복선을 매 화 재계산 = 일관성 붕괴. CAPACITY-DIVISION의 `get_episode_brief`가 정답: 원장은 밖, 회차 brief만 안으로.

**파이프라인 아키텍트**: 동의하나 결합도가 관건. 12기관을 직접 서로 호출시키면 12×12 결합 폭증. **중앙 god-object도 금지**(IO-MERGE에서 B안 기각 사유 = 80모듈 결합·트랙분리 위배). 해법 = 얇은 **Stage 어댑터층**: 각 Stage가 v794 시그니처를 *그대로* 호출, 기관 코드 무수정. 통합은 `NarrativeStateTensor` 버스 하나로만.

**LLM 이양 전문가**: 배선의 *교체점*을 지금 박아야 졸업 후 스왑이 무봉합이다. 각 창작 Stage 뒤에 `GenerativePort` 1개 — 초기엔 `FormulaFallbackPort`(공식), 뒤에 `LLM1Port`→`FrontierPort`. 계약 불변, 구현만 교체. 그래야 "공식 발동률 0 수렴 = 졸업지표"가 측정된다.

**극작/도메인 전문가**: 순서가 북엔드(도입98%·결말98.7%)·톤 유지(16부)를 깨면 안 된다. `VoiceManifold`·`StyleDNAEngine`은 씬 생성 *뒤* 검증 패스로 — 생성 전 강제하면 문체가 사전에 동결돼 드리프트 측정 불가. 톤은 *측정*하되 *구속*은 사후.

### 2.2 합의

순서 = **거시 DAG(루프 밖 1회) → 복선원장(루프 밖) → 화 루프{비트→미시→시퀀스→씬, 텐서 write-back} → 스타일 검증(사후)**. 통합 = 텐서 버스. 결합 차단 = Stage 어댑터. 교체점 = GenerativePort. 복선·지식 = 외부 원장 + brief 주입.

---

## 3. 아키텍처 결정 — ToT 3안

| 안 | 구조 | 장점 | 단점 | 리스크 | 비용 |
|---|---|---|---|---|---|
| **A. 중앙 StoryState god-object** | 모든 기관이 1개 상태객체 read/write | 단순·직관 | 80모듈 결합폭증·트랙분리 위배·테스트 격리 불가 | 변경 1곳→전역 회귀 | 고 |
| **B. 단계 파이프라인 + 텐서 버스 + 어댑터** | 위상정렬 Stage, 통합은 `NarrativeStateTensor`만, 기관 무수정 | 기존 precedent(run_minimal_pipeline)과 동형·결정론·재현가능·교체점 명확 | Stage 경계 설계 필요 | 어댑터가 시그니처 drift 시 깨짐(테스트로 차단) | 중 |
| **C. 블랙보드/이벤트버스** | 기관이 blackboard 구독·발행 | 유연·느슨결합 | 순서 비결정→재현성 손상, 위상이 사실 명확한데 과설계 | 디버깅·졸업측정 난해 | 중~고 |

**최비합리 제거 → A.** god-object는 IO-MERGE에서 이미 기각된 패턴(결합폭증·트랙분리 위배). 재론 불가.

**B vs C**: 본 도메인은 위상순서가 *명확*(거시→미시→씬은 극작상 단방향). C의 유연성은 불필요한 자유도이고 졸업측정(결정론 adopt/rollback)을 해친다. → **B 채택.**

**채택 = B. 단계 파이프라인 + NarrativeStateTensor 통합 버스 + Stage 어댑터(기관 무수정) + GenerativePort 교체점.** precedent(`run_minimal_pipeline`)의 연장이라 위험 최소.

---

## 4. 배선 순서 (위상정렬 · 실 시그니처 결속)

I/O 계약 실측 기반. 각 Stage = 얇은 어댑터, 괄호 안은 v794 실 호출.

### 4.1 매크로 셋업 (루프 밖 · 작품당 1회)

```
S0  SeedCompiler.compile(seed_text)                         → seed
S1  SeriesArcPlanner(total_episodes,…).plan(graph=None)     → CausalPlotGraph   [arc/series_arc_planner.py:95]
S2  graph.infer_causal_edges()                              → List[ArcPlotEdge] [arc/causal_plot_graph.py:104]
S3  EpisodeRevealBudget.from_arc_graph(graph)               → budget            [ledgers/episode_reveal_budget.py:220]
       ※ precedent 갭 교정: 현재 minimal은 fresh budget을 쓴다 → graph 주입으로 연결
S4  KnowledgeStateTracker(project_id).register_fact(…)      → 지식 원장          [world/knowledge_state_tracker.py:100]
S5  PayoffScheduler.generate_schedule(project_id, N,
       residue_ids=⟨graph 노드 forbidden_reveals에서 파생⟩,
       strategy, macroarc_pressure_curve)                   → PayoffSchedule    [causal_plan/payoff_scheduler.py:61]
       ※ 16부 전역 복선원장 = 루프 밖 보유(CAPACITY-DIVISION §3)
       ※ [재검토 교정] graph.residue_ids는 존재 안 함(유령 속성) → 노드 specs/forbidden_reveals에서 파생
       ※ [재검토 교정] kwarg명 = macroarc_pressure_curve (curve 아님)
S6  SeriesConfig 구성 + NarrativeStateTensor 초기화          → 통합 버스 생성     [episode/episode_state.py:82,119]
```

### 4.2 화 루프 (ep_idx = 1..N · 텐서를 관통)

```
for ep in 1..N:
  S7  brief = PayoffScheduler.get_episode_brief(payoff_schedule, ep)      ← 원장→회차 brief 주입 [payoff_scheduler.py:140]
       ※ [재검토 교정] 이미 구현됨(자기점검#1 정정) — 신규구현 아님, 결속만
  S8  EpisodePlanner.plan(series_config, episode_idx=ep, narrative_state=tensor)  → EpisodePlan [episode/episode_planner.py:66]
       ※ [재검토 교정] 3인자 모두 필수 위치인자(narrative_state 선택 아님)
  S9  EpisodeStructureCalculator.calculate(EpisodeStructureConfig)        → EpisodeStructure [episode/episode_structure_calculator.py:260]
  S10 SequencePlanner.plan(macro_arc_packet, episode_no=ep,…)             → list[SequencePlan] [orchestrators/sequence_planner.py:230]
  S11 CharacterIntentAgent.decide_sync(tension) ▸ Collector.collect_sync  → list[IntentPacket] [orchestrators/character_intent_agent.py:140]
  S12 ConflictCollisionCalculus.calculate(ids, edges, weights)            → ConflictCollisionResult [physics/conflict_collision.py:29]
  S13 [씬 생성] SceneGenerationPipeline.run() ▸ GenerativePort.generate    → 산문 텍스트  [scene_generation_pipeline.py:296]
  S14 EmotionalMomentumTracker.update(scene_record, seq_plan)             → EmotionalVector [emotion/…:44]
  S15 NarrativeTensionCurve.record(scene_idx, total, actual_tension)      → TensionPoint  [nie/…:109]
  ── S17(MicroPlotMatrix.build)는 루프 밖으로 이동 — 전체 EpisodePlan 리스트 필요 ──
  S16 ── write-back ──  tensor.conflict_pressure        ← S12.intensity
                        tensor.avg_emotional_momentum   ← S14
                        tensor.scene_energy_required    ← S15
                        tensor.used_reveal_budget       ← S13 소비
       → 화 N+1의 S8(EpisodePlanner)이 갱신된 텐서를 읽음 = 화↔화 피드백 폐회로

S17  MicroPlotMatrix.build(누적된 전체 EpisodePlan 리스트)                → MicroPlotMatrix [episode/microplot_matrix.py:69]
       ※ [재검토 교정] 루프 안 아님 — build()는 List[EpisodePlan] 전체를 요구. 루프 종료 후 1회 호출
```

### 4.3 사후 검증 패스 (전 화 완료 후 · 비구속)

```
S18 VoiceManifold.analyze_drift(episode_vectors, growth_episodes)  → VoiceDriftReport  [longform/voice_manifold.py:108]
S19 StyleDNAEngine.validate(text, dna)                             → dict (톤 정합)    [style/style_dna_engine.py:236]
       ※ 측정만, 생성 구속 아님 (드리프트 측정 보존 — 도메인 전문가 요구)
```

**경계**: S1·S5·S8·S10 = 공식(졸업 후 Port 초안으로 완화 대상). S13 = 유일 생성본체(GenerativePort). S18·S19 = 측정(②BROAD-MEASUREMENT의 A3·B축 입력).

---

## 5. Stage 어댑터 · GenerativePort 계약

```python
class Stage(Protocol):
    name: str
    def run(self, ctx: WiringContext) -> WiringContext: ...   # 기관 무수정, 시그니처만 호출

class WiringContext:           # 통합 버스 래퍼 (god-object 아님 — 읽기전용 핸들 모음)
    seed; series_config; causal_graph; reveal_budget
    knowledge; payoff_schedule; tensor: NarrativeStateTensor
    episode_plans: list; scenes: list; provenance: list

class GenerativePort(Protocol):
    def generate(self, prompt, ctx) -> ProseResult: ...
# 구현 3종 (판단이양 축 계약화)
#   FormulaFallbackPort  → 공식/템플릿, 무GPU E2E 배관증명용 (발동률 측정 기준선)
#   LLM1Port             → 졸업한 LLM-1 (현재)
#   FrontierPort         → 프론티어 LLM (LLM-2 목표, 계약 무변경 스왑)
```

핵심 불변식: **어댑터는 기관 코드를 수정하지 않는다**(시그니처 drift는 어댑터 테스트가 fail-closed로 차단). 통합은 `WiringContext.tensor` 한 곳으로만 — 결합도 O(N) 유지.

---

## 6. 실험 순서 (무GPU 우선 · DoD)

| 단계 | 작업 | GPU | DoD |
|---|---|---|---|
| W1 | S0~S6 매크로 셋업 어댑터 + WiringContext | 무 | 텐서·원장·DAG 생성, 타입 통과 |
| W2 | S7~S17 화 루프 어댑터, `FormulaFallbackPort` | 무 | **무GPU E2E 1작품 16화 조립 통과(배관증명)** |
| W3 | S16 write-back + 화↔화 피드백 단위검증 | 무 | 화 N 산출이 화 N+1 EpisodePlanner 입력에 반영됨을 assert |
| W4 | S18~S19 사후 검증 패스 | 무 | VoiceDrift·StyleDNA 리포트 산출(측정만) |
| W5 | `FormulaFallbackPort`→`LLM1Port` 스왑, 1작품 비교 | 집 GPU | 동일 계약, 공식 발동률 측정 |
| W6 | ②BROAD-MEASUREMENT 메타게이트 결속 | 집 GPU | axis-balance adopt/rollback |

**8항 DoD 체크리스트**: ①기관 코드 무수정(diff=0) ②WiringContext 통합 1버스 ③S3 graph 주입 갭 교정 ④복선원장 루프 밖 ⑤화↔화 피드백 assert 통과 ⑥FormulaFallbackPort 무GPU E2E 16화 ⑦GenerativePort 3구현 계약 동일 ⑧사후 검증 비구속(드리프트 측정 보존).

---

## 8. 재검토 결과 — 독립 감사 (코드 시그니처 대비)

설계 직후 독립 감사관이 본 배선을 실 코드와 대조했다. **결론: "수정 후 빌드 가능"(buildable-with-fixes).** 핵심 주장은 검증 통과, 차단 결함 2건은 교정 반영.

| # | 검증 항목 | 판정 | 근거 |
|---|---|---|---|
| 1 | S-step 메서드 존재·시그니처 | ✅ 대부분 PASS | 14개 모두 인용 line ±1 일치 |
| 2 | **핵심: 화↔화 피드백 루프** | ✅ **PASS(필드단위 검증)** | `EpisodePlanner.plan`이 `narrative_state.conflict_pressure`(:85)·`avg_emotional_momentum`(:86)·`scen