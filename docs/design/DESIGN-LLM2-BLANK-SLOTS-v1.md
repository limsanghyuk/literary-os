# DESIGN-LLM2-BLANK-SLOTS-v1 — 문학 생성 빈칸 5종 확정 + 기존 기관 정교함 기준선

- 상태: 제안(PROPOSAL · 누적) · 2026-06-24 · 기준 허브 main `e95ac2b` / v14.0.0 (Phase E Exit)
- 성격: 결정 문서 아님. "대화 누적 → 수렴 → 본안" 워크플로의 누적 산출물.
- 연계: DESIGN-LLM2-SYNOPSIS-ASSEMBLER-v1, DESIGN-LLM2-SYNOPSIS-ASSEMBLER-IO-MERGE-v1, project_character_event_synopsis_substrate(메모리)
- 원칙: 미선언 금지 — 모든 기관 주장은 `literary_system/` 실코드 경로로 grounding.

---

## 0. 이 문서가 하는 일 (한 줄)

전수조사로 드러난 **문학 생성 빈칸을 3종 → 5종으로 확정**하고, 각 빈칸의 I/O 계약과 기존 기관과의 접속점을 못 박는다. 그 전제로 **기존 16기관이 "얼마나 정교한가"를 코드 레벨로 측정한 기준선**을 먼저 깐다(빈칸을 채울 때 무엇을 재사용하고 무엇을 새로 지을지가 여기서 갈림).

---

## 1. 작업 방식 (어떻게 조사했나)

1. 허브 main을 read-only 클론(`/tmp/hub2`, HEAD `e95ac2b`), 소스 패키지 `literary_system/` 대상.
2. **1차 전수조사**: 정전(canonical) 문학요소 20종을 코드에 매핑 → HAVE / PARTIAL / MISSING 분류. (서브에이전트, 12 tool-use)
3. **2차 정밀분석**: HAVE로 분류된 16기관 각각을 열어 *알고리즘 종류·정교함 등급·LLM 호출 수·sloc* 측정. (서브에이전트, 12 tool-use)
4. 두 조사를 교차해 빈칸을 재확정(3→5종). 결과를 본 문서로 정리·push.

데이터 출처: 모두 실파일 경로·라인 인용. 추정/기억 의존 0.

---

## 2. 기존 기관 정교함 기준선 (실측)

16기관 전수 측정 결과. **핵심: 15/16이 LLM 0회 = 전 파이프라인이 GPU·과금 없이 도는 결정론 골격.** "지능"은 외부 LLM이 아니라 공식·테이블 안에 박제돼 있다.

### 2.1 등급별 분포

| 등급 | 기관 | 실체 |
|---|---|---|
| **상 (진짜 알고리즘)** | CharacterInfluenceMatrix · CausalPlotGraph · KnowledgeStateTracker | PageRank+Heider 균형 / 실제 DAG 순회 / 5상태 머신+연쇄전파. 학부 알고리즘 수준 실체 |
| **중 (수학공식·계수 동결)** | NarrativeTensionCurve · SequencePlanner · EpisodePlanner · EpisodeStructureCalculator · PayoffScheduler · VoiceManifold · EmotionalMomentumTracker | 손실함수·가중곱·EMA·코사인거리 — 수식은 타당하나 계수가 하드코딩 |
| **하 (룩업·얕은 휴리스틱)** | SeriesArcPlanner · ConflictCollisionCalculus · StyleDNAEngine · MicroPlotMatrix · EpisodeRevealBudget · CharacterIntentAgent | 16칸 감정 룩업 / 가중평균 1줄 / 장르 dict / 컨테이너 / 룰북 게이트 / 키워드 if-else |

### 2.2 쉬운 설명 — 무엇을 어떻게 코딩했나

- **거시아크 `SeriesArcPlanner`** (209줄, 하): 16부작 막 배분·감정목표·텐션곡선 생성. 그러나 감정목표는 `_EMOTIONAL_TARGETS_16` = "기대감…평온" **16칸 고정 리스트**, 4막비율 `[0.25,0.35,0.25,0.15]` 상수. 시그모이드 하나 외엔 룩업테이블 순환.
- **인과그래프 `CausalPlotGraph`** (297줄, 상): 16부작을 방향 그래프로 보고 인과/복선/감정상승 엣지를 자동 추론. 진짜 DAG(`_out`/`_in` 인접리스트), `infer_foreshadow_edges()`가 기·승 노드→전·결 노드로 복선+역방향 CALLBACK 엣지 생성. **단 엣지 추론 규칙은 act 기반 휴리스틱**(=개발자가 LLM 인과분류 패스로 격상하려는 지점).
- **회차구조 `EpisodeStructureCalculator`** (446줄, 중): 60분 1화를 콜드오픈+5막+예고편 분(分) 타임라인으로 펼침. 막별 시간비율 테이블(SETUP 0.15…RESIDUE 0.10)로 산술 분할.
- **회차비트 `EpisodePlanner`** (230줄, 중): 화당 미시플롯 수 K 산정. `K = 4 × act_mult × √(runtime/60) × (0.8+0.4·reveal) × density × conflict × momentum → clamp[2,8]`. 9변수 곱이나 본질은 base 4에 보정계수 곱, 계수 전부 하드코딩.
- **미시플롯 `MicroPlotMatrix`** (70줄, 하): 16개 EpisodePlan 담는 dataclass 컨테이너. 연산 없음(`k_curve()`/`summary()` 집계뷰만). **`SequencePlanner`**(456줄, 중)가 실제 분해: `시퀀스수=(runtime/11min)×막계수×압력×플롯 → clamp[3,8]`, `씬수=지속/(타입기준×(1.20−0.40·tension))`.
- **복선 `PayoffScheduler`** (271줄, 중): 16화에 복선 공개 "예산"을 전략별(slow_burn 등) 배분. `generate_schedule()` + `rebalance()`가 surplus를 잔여화에 균등 흡수. 예산 회계 로직(임계값 룰테이블).
- **정보통제 `EpisodeRevealBudget`**(237줄, 하, 룰북 게이트 ALLOW/FORESHADOW_ONLY/DELAY/BLOCK) + **`KnowledgeStateTracker`**(478줄, 상): "누가 무엇을 아는가" 5상태 머신 + `analyze_asymmetry()`가 (a_knows,b_knows,reader_knows) 분기로 장면 압력 산출, `cascade_chain()` depth-3 연쇄 예측. 구조는 정교, 압력 점수는 하드코딩 상수.
- **긴장곡선 `NarrativeTensionCurve`** (205줄, 중): `t_ideal(t)=0.60+0.40·sin(2πt−0.50)+0.20·sin(6πt)`(푸리에), `L=(1/N)Σ(actual−ideal)²`. 진짜 손실함수지만 계수 3개 동결, `update_fourier_coefficients()` 학습 후크는 V518 미연결.
- **인물의도 `CharacterIntentAgent`** (285줄, 하·유일 LLM): `decide_sync()`가 `bridge.generate()`로 의도 JSON 요청, bridge=None이면 `_heuristic_intent()` 키워드 매핑("도주"→ESCAPE) 폴백. asyncio 병렬 구조는 깔끔하나 핵심 판단은 LLM 위임 or if-else.
- **관계망 `CharacterInfluenceMatrix`** (348줄, 상): 비대칭 영향력 행렬 W[n×n]에서 위계·긴장삼각형 산출. `compute_pagerank()` 실제 PageRank(d=0.85, 50 iter) + Heider `balance()=sign(W_ab)·sign(W_bc)·sign(W_ca)` + heap 삼각필터 + 온라인 `update()`. **가장 정직한 알고리즘.**
- **갈등 `ConflictCollisionCalculus`** (72줄, 하): `calculate()=Σ(wa·wb)/(n(n-1)/2)` 가중평균 1줄. 폴더명 `physics/`·이름 "Calculus"와 달리 물리방정식 없음.
- **감정선 `EmotionalMomentumTracker`** (82줄, 중): 4D 감정벡터(긴장/공감/공포/카타르시스) EMA `0.85·이전+0.15·delta`. delta는 키워드셋 매칭.
- **문체 `StyleDNAEngine`** (264줄, 하): 장르→문체프로파일(금지어/선호기법) `_PROFILES` 15개 dict 룩업 + `validate()` 금지어 부분문자열 검사.
- **POV드리프트 `VoiceManifold`** (182줄, 중): 13차원 문체벡터로 1~3화 앵커 대비 이탈 감지. `cosine_distance()` 실제 코사인 + 임계(0.15/0.30) 판정. **단 13차원을 채우는 특징추출기는 이 파일 밖(부재).**

### 2.3 기준선 결론 (빈칸 설계에 주는 함의)

> **가장 큰 함정**: "동적 연산"이라 불리는 것들의 *입력*은 동적이지만 *변환 계수*는 전부 동결돼 있다. 주석은 "실측 한국 드라마 기준"이라 하나 코드에 데이터 피팅 흔적 0 = 전부 사람이 손으로 정한 상수. **학습 모델이 아니라 정교하게 튜닝된 룰엔진.**

함의 셋:
1. **재사용 가능**: 상급 3기관(CIM·PlotGraph·KnowledgeTracker)은 그래프/행렬 실체라 빈칸의 *하부 연산*으로 그대로 쓴다.
2. **격상 대상**: 중·하급의 동결 계수층이 곧 "공식 floor → LLM 이양"의 대상. 빈칸 채울 때 새 로직이 아니라 *이 계수들을 생성모델 초안으로 푸는* 형태여야 한다(인터페이스 불변).
3. **빈칸의 본질**: 16기관 중 *무에서 콘텐츠를 창작*하는 것은 사실상 없다(CharacterIntentAgent의 LLM 위임이 유일 근사). 그래서 아래 5빈칸은 전부 "창작 머리" 쪽에 몰려 있다.

---

## 3. 빈칸 5종 확정

기존 설계의 빈칸 3종(Synopsis Assembler · 로그라인 역생성 · 수정전파)에 전수조사가 2종(세계관 생성 · 주제도출)을 추가하고, 개발자 causal_spine 병합 1건을 계약화한다. 아래 5개로 확정.

### 빈칸 ① 세계관/설정/lore 생성기 [신규 발굴 · MISSING]
- **무엇**: 장르·전제로부터 무대·규칙·세계관(사극의 시대고증, SF의 물리법칙, 미스터리의 범죄설정)을 생성.
- **빈칸 근거**: `world/` 디렉토리엔 `knowledge_state_tracker.py`(누가 뭘 아는가)·`character_knowledge_prose_bridge.py`만 존재 = **지식 상태 추적만, 세계 생성기 0**. `grep "class .*World\|Setting\|Lore"` = 0건.
- **왜 중요**: 장르물에서 설정이 갈등·복선의 가능공간을 규정한다. lore 없이는 causal_spine이 임의값을 추론.
- **I/O 초안**: `WorldSpec(genre, era, rules[], locations[], factions[]) ← GenerativePort.build_world(SynopsisRequest)`. SynopsisDraft에 `world: WorldSpec` 슬롯 추가(현 7요소 → 8요소).
- **접속**: KnowledgeStateTracker가 WorldSpec.rules를 사실(fact) 원장으로 소비. 생성=Port, 검증=KnowledgeStateTracker.

### 빈칸 ② 주제(theme) 도출기 [신규 발굴 · PARTIAL→정의필요]
- **무엇**: premise → 작품 주제·모티프를 *역생성*.
- **빈칸 근거**: `theme`은 SynopsisDraft 슬롯②에 있으나 **입력 필드**일 뿐. 코드상 모티프는 `pass2_causality`가 하드코딩 기본목록 `["비밀","배신","구원"]`에서 식재 = 도출 로직 0. `ThemeNode`(nkg)·`MotifResidueGraph`는 *추적·재현 감사*만.
- **I/O 초안**: `theme, motifs[] ← GenerativePort.derive_theme(premise, genre)`. S1(로그라인 역생성)과 동시 산출.
- **접속**: MotifResidueGraph가 motifs[]를 입력받아 재현 감사. 생성=Port, 재현검증=공식.

### 빈칸 ③ 인물 *창작*기 [기존 부분정의 · 검증만 존재]
- **무엇**: 무에서 인물 세트(이름·성격·관계·목표)를 지어냄.
- **빈칸 근거**: `evaluate_character_birth()`는 **제안된 인물 리스트를 6개 구조질문+Literary State로 검증하는 게이트**일 뿐, 인물을 *발명*하지 않음. 프로필 저장은 `CharacterProfile`(storage). 창작 단계 미정의.
- **I/O 초안**: `characters: list[CharacterSpec] ← GenerativePort.cast(logline, theme, world, constraints)` → `evaluate_character_birth()` 검증 루프(실패 시 재생성 ≤k회).
- **접속**: 생성=Port, 검증=birth_gate(기존), 관계=CharacterInfluenceMatrix(기존 상급기관 재사용), 의도=CharacterIntentAgent.

### 빈칸 ④ track_axis(작품군 축) [개발자 제안 · 미계약]
- **무엇**: 작품을 시간선형/진영형 등 거시 서사축으로 분류해 1급 산출로 둠.
- **빈칸 근거**: 개발자 SYNOPSIS-ASSEMBLER-v1이 1급축으로 제안했으나 내 SynopsisDraft 슬롯엔 미반영.
- **I/O 초안**: `track_axis: TrackAxis(temporal_linear | faction_based | ...) ← GenerativePort.classify_track(premise, world)`. macro_arc 생성의 사전 파라미터.
- **접속**: SeriesArcPlanner.plan()의 막 배분 전략을 track_axis로 분기(현재는 4막 고정 → 축별 분기).

### 빈칸 ⑤ causal_spine 1급화 + 수정전파 계약 [개발자 핵심 ↔ 내 IO 병합]
- **무엇(a)**: CausalPlotGraph(룰 인과 = recall/후보) 위에 **프론티어 LLM 강제력 판정**(precision)을 얹어 진짜 인과 DAG를 1급 산출로 격상. 인물분포는 부산물로 강등.
- **빈칸 근거(a)**: 파일럿 실측 — 룰 인과 vs 진짜 인과 일치 0.56, 위음성 8/32(사물·정보·사건 인과를 룰이 놓침). → CausalPlotGraph.infer_causal_edges(패턴, LLM 0회)만으로 부족.
- **무엇(b)**: 노드 수정 시 후속 전역 재창작(human-in-the-loop)을 위한 **수정전파 엔진**. 단방향 DAG·idempotent로 막지 않게 설계(별도 문서). 본 계약에선 *접속점만* 정의.
- **I/O 초안**: ⑤macro_arc 슬롯을 `CausalPlotGraph`(현) → `CausalSpine(graph, force_judgments[], provenance)`로 승격. force_judgment = GenerativePort(FrontierPort 졸업 후). 수정전파는 `propagate(edit_node) → affected_subgraph` 인터페이스만 노출.
- **접속**: 이것이 **내 IO-v1 아키텍처(Stage/GenerativePort/DoD) ↔ 개발자 §3 causal_spine의 병합 지점**. GenerativePort.judge_causality가 S4 안에 끼어듦, 계약 불변.

---

## 4. 종합 — SynopsisDraft 7 → 9요소 + 우선순위

| 슬롯 | 7요소(기존) | 9요소(확정) | 빈칸 |
|---|---|---|---|
| ① | 로그라인 | 로그라인 | (역생성 = 기존빈칸) |
| ② | 주제 | 주제 | **② 도출기** |
| — | — | **세계관/lore** | **① 신규** |
| — | — | **track_axis** | **④ 신규** |
| ③ | 인물세트 | 인물세트 | **③ 창작기** |
| ④ | 중심갈등 | 중심갈등 | — |
| ⑤ | 거시아크 | **causal_spine(승격)** | **⑤ 병합** |
| ⑥ | 화별비트 | 화별비트 | — |
| ⑦ | 복선스케줄 | 복선스케줄 | — |

**구현 우선순위(권고)**: ⑤(causal_spine 병합 — 개발자 핵심과 직결, 파일럿 근거 보유) → ③(인물창작 — 검증게이트 이미 있어 생성만 얹으면 됨) → ②(주제도출 — S1과 동시) → ①(세계관 — 가장 큰 신규, 장르물 필수) → ④(track_axis — 아크 분기, 비교적 독립).

---

## 5. 결과·다음

- **산출**: 본 문서(빈칸 5종 확정 + 16기관 정교함 기준선). SynopsisDraft 7→9요소 확정.
- **검증**: 모든 기관 주장 실파일·라인 grounding(2.2). 빈칸 근거 전부 grep 0건 또는 "검증만 존재" 실측.
- **다음 누적 의제**: ② 넓은 실측 설계서(거시일관성+다축 블라인드+메타게이트), ① 통합 청사진 1장.

### 자기점검 (논리적 약점)
1. SynopsisDraft 9요소는 잠정 — 졸업 후 평가슬롯 추가 가능(미선언).
2. 빈칸 ①세계관의 I/O는 장르 의존성이 커 단일 WorldSpec으로 사극·SF·현대물을 다 담을지 미검증.
3. 우선순위 ⑤먼저는 "파일럿 근거 보유"에 기댄 것 — FrontierPort 미졸업 상태라 force_judgment 품질은 미보장(절대 미선언).
4. 16기관 정교함 등급은 코드 구조 기준 — 실제 산출물 품질(생성 드라마의 좋음)과는 별개. 등급 "상"이 곧 "좋은 드라마"를 뜻하지 않음.
