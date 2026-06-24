# DESIGN-LLM2-CAPACITY-DIVISION-v1 — "8B로 16/24부작이 가능한가" 역할분담 [PROPOSAL·누적]

- 상태: PROPOSAL · 2026-06-24 · DESIGN-LLM2-SYNOPSIS-ASSEMBLER-v1의 실현가능성 보강
- 질문(사용자): 판단은 로컬(Llama-3.1-8B)인데, 8B로 16/24부작 전체 시놉시스+회차별 시놉시스+인물+서브플롯+인과/사건을 기획하는 건 어렵지 않은가.

## 0. 답: 맞다 — 8B 단독으론 못 한다. 그래서 시스템은 8B에게 그걸 안 시킨다.
거시 골격은 **결정론 엔진(전부 "LLM 호출 0회", 실코드 확인)**이 외부 메모리로 들고 계산한다. 8B는 **바운디드 로컬 작업**(한 회차/씬 산문 + 쌍대 노트)만 한다. 어려운 거시 판단(진짜 인과 강제력)은 **프론티어 LLM 패스**(③)가 맡는다. = "부품→조립 + 통제권 이양"의 핵심.

## 1. 왜 8B 단독 거시기획이 불가능한가 (정직)
- 16부 대본 ≈ 수만 줄(예: 열여덟스물아홉 14부 678씬). 8B 컨텍스트(8K~128K)에 다 넣어도 **장거리 일관성**(1화 복선→14화 회수, 인물 톤 유지)이 8B의 구조적 약점.
- 자기편향·환각으로 **떡밥-회수 정합/4막 균형**을 스스로 못 지킴 → 그래서 "공식이 골격, LLM이 산문"이 설계 원칙(LLM-0~1).

## 2. ★역할분담 — 누가 무엇을 드는가 (실코드 grounding)
| 산출물(사용자 지목) | 담당 | 실코드 | LLM 호출 |
|---|---|---|---|
| 드라마 전체 시놉시스(거시 아크·4막·텐션) | 결정론 | `arc/series_arc_planner.py::SeriesArcPlanner.plan()` | **0회** |
| 인과·복선 엣지(에피소드 간) | 결정론(후보) + ★프론티어(확정) | `arc/causal_plot_graph.py::CausalPlotGraph` (패턴 0회) + ③ LLM 인과패스 | 0회→프론티어 |
| 각 회 시놉시스(미시플롯 수 K) | 결정론 | `episode/episode_planner.py::EpisodePlanner.plan()` (9변수 함수) | **0회** |
| 복선 setup→payoff 스케줄 | 결정론 | `causal_plan/payoff_scheduler.py::PayoffScheduler` (★`get_episode_brief`) | **0회** |
| 회차 내 시퀀스·씬 수 | 결정론 | `orchestrators/sequence_planner.py::SequencePlanner.plan()` | **0회** |
| 등장인물(등장판정·원장·배치) | 결정론 | `analyzer/orchestrator.py` (character_birth/ledger/grid/pressure_cast) | 0회 |
| 서브플롯 트랙(메인/서브 분리) | 결정론+분석 | CausalPlotGraph 트랙 + ②파일럿 3기준(종결위치·인과종속·회수책임) | 0회 |
| 구조 비퇴행 검증(floor) | 결정론 | `critic/structure_conformance.py` (c3, tension_proxy) | **0회** |
| 품질 평가 닻 | 평가 | `critic/next_episode_bench.py` (M2 은닉GT 쌍대) | generate=주입 |
| **회차/씬 산문 생성** | **8B (로컬)** | 생성 LLM | 8B |
| **쌍대 Critic 노트** | **8B→프론티어** | `critic/llm_critics.py` 5축 | 8B(현)→프론티어(F) |
| **거시 인과 강제력 판정** | **프론티어** | ③ LLM 인과패스 | 프론티어 |

## 3. ★핵심 메커니즘 — `get_episode_brief`: 8B가 16부를 안 봐도 되는 이유
PayoffScheduler는 16부 전체의 복선 원장을 **외부에서** 들고, 회차 r에 대해 `get_episode_brief(r)` = "이 회차에 심을 residue / 터뜨릴 payoff / 예산"만 반환. → 8B는 **그 회차 브리프 + 직전 상태 요약**(바운디드)만 받아 **그 회차만** 쓴다. 장거리 상태(인과 엣지·복선 잔액)는 CausalPlotGraph·PayoffScheduler가 **외부 메모리**로 보유. = LLM의 장거리 약점을 결정론 엔진이 메우는 구조. SequencePlanner.plan()이 회차→시퀀스→씬 수를 미리 깔아주므로 8B는 "씬 한 칸"만 채운다.

## 4. 조립 흐름 (Synopsis Assembler가 호출)
```
SynopsisRequest(장르·전제·제약 episodes=16/24)
 → [로그라인 역생성(빈칸)] → theme
 → SeriesArcPlanner.plan() → CausalPlotGraph(4막·텐션·복선예산)   [결정론]
 → ★프론티어 LLM 인과패스 → causal_spine 확정(강제력)            [프론티어, ③]
 → EpisodePlanner.plan(ep) → 회차별 K·비트                        [결정론]
 → SequencePlanner.plan(ep) → 시퀀스·씬 수                        [결정론]
 → PayoffScheduler.generate_schedule → 회차별 get_episode_brief   [결정론]
 → 인물엔진 → 인물 세트                                            [결정론]
 → (회차 루프) 8B가 get_episode_brief로 그 회차 산문 생성          [8B 로컬]
 → structure_conformance(c3) floor + NextEpisodeBench 평가         [결정론+평가]
 → 미흡 시 PayoffScheduler.rebalance → 후속 회차 재계획(수정 전파)  [결정론]
```

## 5. 정직한 경계 (이게 다음 의제)
- 결정론 엔진이 **구조적으로 유효한** 골격은 주지만 **명작 수준의 골격**을 주는지는 미증명(3팀 결론: 분포·패턴은 증상이지 원인 아님). → ★그래서 F.2에서 거시 인과·강제력 판정을 프론티어 LLM으로 올리는 게 핵심.
- `CausalPlotGraph.infer_causal_edges`가 패턴기반(LLM0회)이라 (b)에서 진짜 인과와 0.56 → 이 골격의 인과는 *후보*일 뿐, 프론티어 확정 패스가 필수.
- 8B의 산문 품질 자체는 loop-C 졸업(show/tell 한 축)만 실증 — 회차 전체 산문의 일관성은 미검증.
- **수정 전파 엔진**: PayoffScheduler.rebalance가 기반이나, 작가 개입→인과 재계산의 완전판은 빈칸(구체화 의제).

## 6. 결론
사용자 우려는 정확하다. 답은 "8B에게 거시기획을 안 시킨다"이다: **거시 골격=결정론 엔진(외부 메모리·재현가능), 어려운 판단=프론티어, 로컬 산문·노트=8B.** 단, 결정론 골격이 "유효"를 넘어 "명작"이 되려면 거시 인과 판정의 프론티어 이양(F.2)과 양성 평가축이 필요 — 이게 Phase F~G의 본질.
