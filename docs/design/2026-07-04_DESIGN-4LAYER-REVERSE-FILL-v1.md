# DESIGN-4LAYER-REVERSE-FILL-v1
## 4층 서사 이해 계층 역채움(Reverse-Fill) 설계도

- 작성: 2026-07-04 (Opus 설계 모드, 4-에이전트 심의 종합)
- 대상: literary-os / seqcard_ko (30작 / 593회 / 38,046씬)
- 위상: **설계 단계**. κ 게이트 통과 전이므로 프라이어 주입·대량 저작은 착수하지 않음. 본 문서 + 30편 파라미터표까지가 산출물이며, 실제 상위 3층 저작(593회)은 집(Sonnet) 파이프라인으로 분리.
- 역할 준수: Opus=설계/심의/오케스트레이션, Sonnet 멀티에이전트=대량 저작. 본 문서는 저작 지시서가 아니라 **저작이 따라야 할 스키마·불변식·검증 게이트**를 규정한다.

---

## 0. 문제의 구조적 정의

### 0.1 진짜 결함 (사용자 자가진단 확인)
"SeqCard"는 이름과 달리 **씬(Scene) 층만** 채웠다. 나머지 상위 3층은 *서사 이해*로서 부재하고, 오직 통계·카운트만 측정되어 있다.

| 층 | 현 파일 | 현 내용 | 상태 |
|---|---|---|---|
| FullSeriesArc (전체 시놉시스) | `{work}_series_arc.json` | core_dist·트라젝토리·전이문법·persist **통계만** | ✗ 서사 부재 |
| EpisodeArc (회차 시놉시스) | `{work}_NN.episode_meta.json` | episode_function(산문 1문장)+core_dist | △ 기능라벨만 |
| SequenceBlueprint (시퀀스 의도) | **파일 없음** | 개수만 측정(장소시퀀스36.5 등) | ✗ 층 자체 부재 |
| SceneBlueprint (씬 의도) | `{work}_NN.seqcard.jsonl` | intent_gist·core·skin 완비 | ✓ 검증됨 |

결과: **하향 top-down 사슬 단절.** 상위 의도가 존재하지 않으니 "화→거시/미시플롯→씬" 자율 산정의 근거가 없다. 이는 사용자의 1차 목표(거시 창작 플래너)의 정중앙 병목이다.

### 0.2 해결 착지점
씬(SSOT)은 30편 전부 존재한다. → **씬을 근거로 상위 3층을 역채움(reverse-fill)** 하여 4층 수직 완결 사례를 구축한다. 이 완결 사례가 LLM-2 거시 플래너의 학습·검증 substrate가 된다.

### 0.3 1차/2차 목표 정렬 (상시 고려)
- **1차 = 거시 창작 플래너**: 본 설계가 채우는 상위 3층이 곧 `FullSeriesArc→EpisodeArc→SequenceBlueprint` top-down 산정의 대상이자 학습 데이터. **SequenceBlueprint는 이번에 신설되는 층**이며, 상위 의도를 씬 예산으로 번역하는 유일한 층 = top-down의 실제 병목.
- **2차(궁극) = 씬 산문 생성**: 완성된 4층이 렌더러에 주입되어 회차/시즌 대본으로 조립. top-down 생성 + bottom-up 검증. 향후 수정-전파(Git-Nexus 원리: DAG/이력/의존성 취함 + merge만 LLM 의미 재생성)로 human-in-the-loop 완성.

---

## 1. 4-에이전트 심의 종합

4개 렌즈(극작·스키마·파이프라인·검증)가 독립 심의 후 강하게 수렴했다.

### 1.1 수렴점
1. **씬 = SSOT(단일 진리원). 상위 층 = 파생·검증 가능한 분할.** 상위 층은 씬을 재구성하는 게 아니라 씬을 *덮는(cover) 분할*이어야 하며, 커버리지 불변식으로 무결성이 강제된다.
2. **시퀀스 = goal-obstacle-turn(가치전환, value_shift) 단위.** 가장 어렵고 가장 가치 높은 층이자 top-down 병목. 경계 = 전환 완료 + POV 이동 + 서브플롯 이동 중 **≥2가 동시 발생**하는 지점. κ 측정 가능.
3. **역채움 = 하이브리드.** 구조적 필드는 결정론적 집계(무LLM), 사실 필드는 원본 텍스트 앵커, 해석 필드는 저작 후 기능적 ablation + κ 검증.
4. **검증 = 3축 분리(절대 평균내지 않음).** A=원본 충실도(원본 대조), B=씬 집계 정합성(무LLM), C=기능적 효용(Critic ablation 전용).

### 1.2 각 렌즈의 결정적 기여
- **극작**: 시퀀스=목표-장애-전환. 경계는 "가치가 바뀌는 곳". 씬은 시퀀스의 박자.
- **스키마**: 커버리지 불변식 4종(I-COVER/I-PARTITION/I-COUNT/I-FK), 비연속 시퀀스 허용(member_scene_nos 리스트가 정본, scene_span은 파생), seq_id=(series_id, ep_no, seq_index), work_id 누락 시 fail-closed.
- **파이프라인**: Wave0(무LLM 경계+집계) → Wave1(~8에이전트 회차 샤딩 fan-out) → Wave2(EpisodeArc 스택에서 FullSeriesArc fan-in). 원본 재열람은 사실 필드에만 스코프 → 토큰 10~20× 절감.
- **검증**: 원자 주장 분해 → char-offset 인용 그라운딩, 교차모델 심사, 네거티브 컨트롤(주입 환각), 앵커 3작 완전 그라운딩+κ, 상위층만 human-blind κ. **첫 fail-fast 게이트 = SequenceBlueprint sequence_intent Critic ablation Δ≥0.5**(미달 시 신설 층 DROP/재설계).

---

## 2. ToT: 역채움 전략 3안 비교·선택

### 전략 A — 순수 상향 집계 (Pure Bottom-Up Aggregation)
씬 필드를 결정론적으로 굴려 상위 층을 전부 자동 산출. LLM 저작 없음.

- 장점: 무LLM·재현성 100%·불변식 자동 충족·비용 최소.
- 단점: 통계는 나오지만 **서사 이해(주제·로그라인·의도)는 산출 불가** → 0.1의 결함을 그대로 재생산. 상위층이 다시 "카운트만"이 된다.
- 리스크: **목표 미달**(치명). 1차 목표의 substrate로 무가치.
- 비용: 극저(수분).

### 전략 B — 원본 재저작 (Top-Down Re-Authoring from Original)
원본 대본을 다시 읽어 상위 3층을 처음부터 저작.

- 장점: 최고 서사 충실도·사실 정확도.
- 단점: 원본 30편 전편 재열람 = 토큰 10~20×·작가급 판단 대량 요구. 이미 존재하는 씬(SSOT)과 **분리 저작 → 정합성 붕괴 위험**(상위층이 씬과 어긋남).
- 리스크: 비용 폭증 + I-COVER/I-COUNT 위반(씬-상위 불일치). 병목 재현.
- 비용: 최고.

### 전략 C — 계층 하이브리드 (Deterministic-Lower / Authored-Upper / Original-Anchor-for-Facts) ★채택
필드를 3종으로 분류해 각기 다른 방법으로 채운다.
- **구조 필드**(개수·경계·전이·core 분포·인물 등장 비중) = 씬에서 **결정론적 집계**(무LLM).
- **해석 필드**(시퀀스 의도·회차 시놉시스·주제·로그라인) = 씬 intent_gist 스택을 근거로 **저작**, 원본 미열람.
- **사실 필드**(information_reveal·plant/payoff·인물 원장 사건) = **원본 텍스트 char-offset 앵커** 필수(환각 차단).

- 장점: 목표 달성(서사 이해 산출) + 씬 SSOT와 자동 정합(집계가 씬에서 파생) + 원본 열람을 사실 필드로만 스코프 → 비용 통제 + 커버리지 불변식 강제.
- 단점: 필드 분류 스키마를 먼저 확정해야 함(설계 부담) + 앵커 작품에서 그라운딩 검증 필요.
- 리스크: 필드 오분류 시 환각/누락 → **첫 게이트(ablation Δ≥0.5)와 3축 검증으로 fail-closed**.
- 비용: 중(원본 열람 사실 필드 한정).

### 최약안 제거 & 선택
- **A 제거**: 목표 자체를 못 이룬다(서사 부재 재생산).
- **B 제거**: 비용 폭증 + 씬-상위 정합 붕괴.
- **선택 = C.** 유일하게 (목표 달성)·(SSOT 정합)·(비용 통제)·(검증가능성)을 동시 만족. 4-에이전트 수렴과도 일치.

### 자기점검 (논리적 약점)
1. "저작 필드가 결국 씬 요약 아니냐?" → ablation Δ≥0.5 게이트가 *부가가치 없는 요약*을 DROP시킨다(무가치 층은 통과 못함).
2. "결정론 집계가 서사를 왜곡하지 않나?" → 집계는 구조 필드 한정, 해석은 저작으로 분리. 축 B(집계 정합)는 무LLM이라 왜곡 여지 없음.
3. "앵커 3작만으로 30작 사실충실 보장?" → 앵커는 방법 검증용. 나머지는 축 B(집계)로 커버, 사실 필드는 앵커 그라운딩 규약을 전작 적용.

---

## 3. 4층 스키마 규정

공통 조인키: `(work_id, scene_no)`. 상위 층은 하위 멤버 리스트를 소유한다(포함관계는 리스트가 정본).

### 3.1 SceneBlueprint (기존, 완비)
현 `seqcard.jsonl` 유지. 필드: work_id, scene_no, heading, title, intent_gist, core, core2, skin. + 8 갭필드(직전 수직슬라이스에서 도출: dramatic_conflict, entry_state, exit_state, plant_ops, payoff_ops, information_reveal, dialogue_intention, subtext_target)는 **별건 ablation 검증 대상**으로 병행(본 설계의 필수 선결 아님).

### 3.2 SequenceBlueprint (신설 — 이번 핵심)
```
seq_id            = (series_id, episode_no, seq_index)   # 정본 식별
member_scene_nos  = [int]                                # 정본 포함관계(비연속 허용)
scene_span        = [min, max]                           # 파생(표시용)
scene_count       = len(member_scene_nos)                # 파생
# --- 해석 필드(저작) ---
sequence_intent   = str      # goal-obstacle-turn 한 문장
goal              = str      # 이 시퀀스가 추구하는 것
obstacle          = str      # 장애
value_shift       = {from, to}  # 진입가치→퇴장가치 (전환)
turn_type         = enum{RISE, FALL, REVEAL, STALL}
# --- 구조 필드(결정론 집계) ---
core_mix          = {CORE: count}     # 멤버 씬 core 집계
pov_char          = str               # 지배 POV(집계)
place_cluster     = str               # 장소 군집(집계)
# --- 예산 필드(파생/공식) ---
scene_budget      = int               # = scene_count
dialogue_budget   = float             # 대사비중 추정
runtime_share     = float             # 회차 분량 비중
```
경계 규칙: value_shift 완료 + POV 이동 + 서브플롯 이동 중 ≥2 동시 = 시퀀스 경계. Wave0 무LLM 후보 경계 → 저작 시 확정.

### 3.3 EpisodeArc (확장)
```
work_id, episode_no
member_seq_ids    = [seq_id]          # 정본 포함관계
episode_synopsis  = str              # 회차 시놉시스(저작, 3~5문장)
episode_function  = str              # 기존 1문장 유지
dramatic_question = str              # 이 회차가 던지는 질문
hook_out          = str              # 회차말 견인(기존 hook_flag 근거)
core_dist         = {CORE: count}    # 집계
char_weight       = {char: share}    # 인물 등장 비중(집계)
```

### 3.4 FullSeriesArc (확장)
```
series_id, episodes_total, scenes_total
logline           = str              # 로그라인(저작, 역생성)
theme             = str              # 주제
premise           = str              # 전제/세계
protagonist_arc   = str              # 주인공 변화 궤적
antagonist_arc    = str
central_conflict  = str              # 중심 갈등축
character_roster  = [{name, role, want, need}]   # 인물 원장
genre_mix         = [str]
member_episode_nos= [int]            # 정본
# 기존 통계 필드 유지(트라젝토리·전이문법·persist)
```

---

## 4. 역채움 방법 — 층별 규약

| 층 | 방법 | LLM | 원본 열람 | 검증축 |
|---|---|---|---|---|
| SceneBlueprint | 기존 유지 | - | - | (완료) |
| SequenceBlueprint | Wave0 무LLM 경계 후보 → intent/goal/obstacle/value_shift 저작; core_mix·pov·place 집계 | 해석필드만 | 사실필드 앵커 | A(앵커)·B·**C(첫 게이트)** |
| EpisodeArc | member_seq 집계 → episode_synopsis·dramatic_question 저작; char_weight·core_dist 집계 | 해석필드만 | 사실필드 앵커 | A·B·C |
| FullSeriesArc | EpisodeArc 스택 fan-in → logline·theme·roster 역생성 저작 | 저작 | 앵커 3작 완전 | A(κ human-blind)·B·C |

원칙: **하위층은 결정론 집계로 우선 채우고, 상위층으로 갈수록 저작 비중↑.** 원본 재열람은 FullSeriesArc(파이프라인 에이전트) + 사실 필드로만 스코프.

---

## 5. 검증 게이트

### 5.1 커버리지 불변식 (무LLM, 전작 강제)
- **I-COVER**: 모든 scene_no가 정확히 하나의 seq에 속함(∪ member_scene_nos = 전체 씬).
- **I-PARTITION**: 시퀀스 간 member_scene_nos 교집합 = ∅.
- **I-COUNT**: Σ scene_count = episode scene_count; Σ episode = series scenes_total.
- **I-FK**: 모든 seq_id/scene_no 참조 무결성. work_id 누락 = **fail-closed**(ValueError, 건너뛰기 금지).

### 5.2 3축 분리 검증 (절대 평균 금지)
- **축 A — 원본 충실도**: 원자 주장 분해 → char-offset 인용 그라운딩. 앵커 3작 완전 적용. 사실 필드 필수.
- **축 B — 집계 정합성**: 무LLM. core_mix·char_weight·count가 씬에서 실제로 파생되는지 재계산 대조.
- **축 C — 기능적 효용**: Critic ablation 전용. 해당 층 의도를 제거 vs 주입한 렌더 결과를 Critic이 채점.

### 5.3 게이트 순서 (fail-fast)
1. **G1 (첫 관문) = SequenceBlueprint sequence_intent Critic ablation Δ≥0.5.** 미달 → 신설 층 DROP/재설계(더 진행 안 함).
2. G2 = 커버리지 불변식 전작 PASS.
3. G3 = 앵커 3작 축A 그라운딩 + 네거티브 컨트롤(주입 환각 탐지율).
4. G4 = FullSeriesArc κ≥0.6 human-blind(AI-judge-AI 편향 회피).

프라이어 주입은 **G1~G4 통과 후**로 보류(현 단계는 분석·PoC).

---

## 6. 산출 프라이어 4종 (게이트 통과 후 주입)
1. `P(seq_intent_{t+1} | seq_intent_t, position_norm, genre_mix)` — **학습**.
2. 인물 배분표 `[role][position_bucket] = scene_share` — **결정론**(집계).
3. `P(episode_function_class_{n+1} | class_n, arc_position, total_episodes)` — **학습**.
4. `budget(runtime, genre) → (scene_count, dialogue_ratio, sequence_count)` — **결정론**(공식).

---

## 7. Sonnet 파이프라인 위상 (집 실행용 — 본 세션 미착수)
- **Wave0** (무LLM): 시퀀스 경계 후보 검출 + 구조 필드 집계. 전작 배치.
- **Wave1** (~8 에이전트 fan-out): 회차 샤딩 저작(SequenceBlueprint + EpisodeArc 해석필드). 16~54부 범위 → 에이전트당 가변 회차(파라미터표 §wave 참조).
- **Wave2** (fan-in): EpisodeArc 스택 → FullSeriesArc 역생성 저작.
- 병합 검증: 결정론 정합성 체크(I-COVER/COUNT). 원본 재열람 = 사실 필드만 → 토큰 10~20× 절감.
- 총량 추정 ~5M 토큰(원본 재열람 제외). **Opus 순차 저작 금지, Sonnet 병렬 표준.**

---

## 8. 결론 & 다음
- 채택: **전략 C(계층 하이브리드)**. 씬=SSOT, 시퀀스=goal-obstacle-turn 신설 층, 3축 분리 검증, 첫 게이트=ablation Δ≥0.5.
- 산출물: 본 설계도 + `30WORK-4LAYER-PARAMETER-TABLE`(§동봉).
- **미착수(의도적 분리)**: 593회 상위 3층 실제 저작 = 집 Sonnet 파이프라인. G1 게이트 시제품(앵커 1작 SequenceBlueprint ablation)이 다음 실측 관문.

## 부록. 출처
- 로컬 실측: `/db/seqcard_ko/_ALL_series_arc.json` (30작/593회/38,046씬), `{work}_series_arc.json`·`episode_meta.json`·`seqcard.jsonl`.
- 기존 메모리: SeqCard v1 데이터화 아키텍처, 시퀀스 4계층 분할 측정(장소시퀀스36.5), SceneBlueprint 수직슬라이스(ablation-2 renderer_prompt_constraints VALIDATED 1.13×), 세션 핸드오프 5계층 매핑.
