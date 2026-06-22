# 2026-06-22 (회사) 인물·사건 생성 로직 실측 + 시놉시스 구상 가능성 = LLM-2 기질 인벤토리

**맥락**: 본 대화(회사, 무GPU)는 같은 날 집 세션의 핸드오프
`2026-06-22_HANDOFF_spe10_v2_graduation_llm2_seed.md` **§4·§6의 후속**이다.
그 핸드오프는 "메인의 거시→미시 계층 플래너(회차 단위 생성본체 조립)가 **LLM-2의 진짜 빈칸**"이고
`world.story_bible.StoryBibleAggregator`는 "노트만·미구현"이라고 빈칸을 *지목*했다.
본 문서는 그 빈칸이 **무엇 위에 얹히는지(=이미 있는 하위 자산)**를 V794 코드로 실측하고,
빈칸을 작가용 산출물 관점(=시놉시스/기획안)으로 **구체화**한다.

**한 줄**: 인물·사건을 *산정*하는 결정론(LLM-0) 로직은 이미 광범위하게 존재한다.
시놉시스(=story_bible)의 7개 구성요소 중 5개는 산출 엔진이 있고, 빈칸은 정확히 2개
(**Synopsis Assembler** + **로그라인/주제 역생성**)다. 이 2개가 곧 LLM-2 플래너의 첫 실체.

---

## 1. 인물 생성 로직 — 실측 인벤토리 (V794)

| 모듈 (파일) | 역할 | LLM |
|---|---|---|
| `analyzer/character_birth_gate.py` (V312) | 인물 **등장 시점 판정**. Literary State(SP 압력·RU 공개소진·ET 감정긴장) 연동. 핵심 게이트키 = `act_necessity` / `pressure_target_defined` / `unique_residue_defined` / **`structure_collapse_if_removed`**(그 인물이 빠지면 구조가 붕괴하는가) | 0 |
| `analyzer/ledger_builder.py` + `schemas/character_ledger.py` | 인물 **원장 생성**. 필드 = character_id·display_name·role_type·pressure_target·residue_binding·act_evolution·memory_weight·prunable | 0 |
| `analyzer/grid_builder.py` + `analyzer/pressure_cast_planner.py` | 씬별 **인물 배치** (foreground 3 / background / suppressed) + 긴장 축 할당 | 0 |
| `orchestrators/character_intent_agent.py` (V326) | 인물별 **동시 의사결정**. 인물 A는 B의 IntentPacket을 못 봄(비공개) → asyncio.gather 병렬. IntentActionType 8종: MOVE/CONFRONT/ACQUIRE/CONCEAL/WAIT/COMMUNICATE/ESCAPE/PLAN | 1/인물 |
| `nkg/cluster/character_cluster.py` · `nie/character_influence_matrix.py` · `multiwork/shared_character_db*.py` | 인물 군집·영향 행렬·작품 간 공유 인물 DB(=인물 관계 데이터의 그래프 기질) | 0 |

**한계(정직)**: 위는 인물을 *구조화·배치·판정*한다. 인물의 이름·성격·배경서사를 **자유 창작하는 전용 생성기는 없다**. 속성을 채우는 것은 생성 본체(LLM).

## 2. 사건 생성 로직 — 실측 인벤토리 (V794)

| 모듈 (파일) | 역할 | LLM |
|---|---|---|
| `arc/series_arc_planner.py` (V380) | 16부작 전체 아크 자동 생성. 4막 분배 기25/승35/전25/결15, S자 텐션곡선, 회차별 감정목표 8패턴 순환 | 0 |
| `arc/causal_plot_graph.py` (V380) | **인과 플롯 그래프**. 에피소드 간 인과·복선 엣지 자동 추론, 4막 검증 (=사건 관계도의 기질) | 0 |
| `episode/episode_planner.py` (V392) | 회차당 **미시 플롯 수 K 동적 산정** (9변수 결정론 함수, conflict_density 포함) | 0 |
| `episode/episode_structure_calculator.py` (V482) | 60분 1화를 **분 단위 씬 슬롯**으로 (콜드오픈 2~4분 / 본편 3막 ~54분 / 예고 1~2분) | 0 |
| `physics/conflict_collision.py` (V383) | 씬별 **갈등 충돌 강도** 계산: conflict_intensity·collision_pairs·`stagnation_warning`(정체 경고) | 0 |
| `agents/conflict_resolver.py` (V701) | 탐지된 충돌 해소 | — |
| `longform/fractal_plot_tree.py` · `episode/microplot_matrix.py` | 프랙탈 플롯 트리 · 화×K 미시플롯 행렬 | 0 |

## 3. 인물 ↔ 사건이 연결되는 메커니즘 (설계의 핵심)

사건은 외부 주입이 아니라 **인물의 욕망 충돌**에서 발생한다:

```
각 인물 IntentPacket 제출(욕망·행동, 비공개·병렬)
  → ConcurrentActionResolver 충돌 탐지
  → ConflictCollisionCalculus 강도 계산(stagnation 경고 포함)
  → 미시 플롯/씬으로 전개
```

= 사용자 로직("주변 인물부터 먼저 생성, 거시/미시 플롯을 구성하라")이 코드에 대응.

---

## 4. 시놉시스(=story_bible) 7요소 ↔ 코드 매핑 + 빈칸 2개

드라마 기획안(시놉시스) = 주제·기획의도 / 로그라인 / 전체 줄거리 / 인물소개+관계도 / 사건 관계도 / 회차별 설계도.

| 시놉시스 구성 | 담당 모듈 | 상태 |
|---|---|---|
| 주제 / 기획의도 | — | **빈칸** |
| 로그라인 | `drama_episode_generator.logline` (default 플레이스홀더 보유) | **입력으로만** 받음 (역생성 없음) |
| 전체 줄거리 / 거시 아크 | `arc/series_arc_planner.py` | 있음 |
| 인물 소개 / 관계도 | `character_ledger` + `grid_builder` + `nkg/character_cluster`·`character_influence_matrix` | 데이터 있음 (관계도 렌더 없음) |
| 사건 관계도 | `arc/causal_plot_graph.py` + `conflict_collision` | 있음 (그래프) |
| 회차별 미시플롯 | `episode/episode_planner.py` + `microplot_matrix` | 있음 |
| 회차별 분량표(분) | `episode/episode_structure_calculator.py` | 있음 |
| (조립) `sdk/sdk_models.py:86 synopsis: str` | 단순 pass-through 필드 | 생성 아님 |

**빈칸 = 정확히 2개**
1. **Synopsis Assembler** — 위 흩어진 산출물(아크 그래프 + 인물 원장 + 인과 그래프 + 회차 구조)을 하나의 *읽을 수 있는 기획안*으로 묶고, 그래프를 인물관계도/사건관계도로 렌더링. **데이터가 이미 있으므로 GPU 불요·얇은 상층 레이어.** = 핸드오프 §4가 지목한 `StoryBibleAggregator`(미구현)의 작가 산출물 형태.
2. **로그라인·주제 역생성** — 현재 로그라인은 *입력*. 작가가 시드("나의아저씨+키다리아저씨+소공녀 16부작")만 주면 주제·로그라인을 **스스로 뽑아내는** 부분이 비어 있음.

---

## 5. 왜 이것이 LLM-2 기획의 일부인가 (사용자 통찰)

사다리: LLM-0(결정론) → **LLM-1(쌍대 Critic·현재)** → LLM-1.5 → **LLM-2(생성 주력)** → LLM-3(천장=모작).

- §1·§2의 인물·사건 산정 로직(전부 LLM-0)은 **LLM-2 플래너가 오케스트레이션할 하위 자산**이다. LLM-2는 맨땅이 아니라 이 기질 위에 선다.
- 시놉시스 = 계층 자율 생성의 **최상위 출력**이자, 거시→미시 플래너(=LLM-2 빈칸)의 *가시적 산출물*. 즉 "Synopsis Assembler를 만든다 = LLM-2 메인 플래너의 첫 실체를 만든다".
- 또한 시놉시스는 2단계(작가 협업·수정-전파)의 **첫 진입 화면**이 될 자연스러운 산출물 — 작가가 보고 고치는 대상이 바로 이 문서.

## 6. 권고 (3안 비교 → C안)

- **A안(LLM 자유 생성)**: 시놉시스 통째를 LLM에 위임 → 빠르나 구조 정합·공식 검증이라는 차별점이 죽음. 기각.
- **B안(엔진 데이터 덤프)**: 산출물을 표로 출력 → 정확하나 설득용 기획안 가독성 미달. 부분 채택.
- **C안(Assembler + 선택적 LLM 윤문) ★권고**: 구조·인물·사건·회차표는 결정론 엔진이 산출(사실) → Assembler가 기획안 골격으로 조립 → 주제문·로그라인·줄거리 산문만 LLM 윤문. = "판단은 로컬, 서술만 LLM" 원칙 일치, 최소비용 MVP, 핸드오프 §6.1(LLM-2 오케스트레이터 설계)과 직결.

## 7. 자기점검 (논리적 약점)

- 본 인벤토리는 V794 zip 정적 실측이다. 모듈 *존재*는 확인했으나 end-to-end 결선(아크→인물→사건→회차가 한 번에 흐르는지)은 별도 실측 필요 — 핸드오프 §4 "노드는 있으나 엣지 배선 미확인"과 동일 캐비엇.
- "빈칸 2개"는 시놉시스 산출 관점의 최소집합. 작가 협업(수정-전파)까지 포함하면 빈칸은 더 큼(2단계, 의도적 후순위).
- 트랙 분리: 본 문서는 **본 트랙(LLM-0→3 자율화)** 소속. 제품전략 B(SaaS UI)와 혼합 금지.

## 8. 다음 단계 권고

1. **Synopsis Assembler 입출력 계약 설계서** — 어떤 모듈 출력(ArcPlotGraph·CharacterLedger·CausalPlotGraph·EpisodeStructure)을 받아 기획안 어느 섹션으로 매핑하는지. (회사·무GPU 가능, 핸드오프 §6.1과 같은 작업)
2. 인물관계도·사건관계도 **렌더 스펙**(그래프→가독 다이어그램).
3. 로그라인/주제 역생성기 = LLM 윤문 단계로 분리 명세.
