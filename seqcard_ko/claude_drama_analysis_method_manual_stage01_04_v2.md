# 드라마 4-Stage 분석 방법론 완전 설명서 (자립형 런북, v2)

Document ID: CLAUDE-DRAMA-METHOD-STAGE01-04-V2
작성: Claude (Cowork), literary-os `seqcard_ko` 코퍼스 저작 프로젝트 기준
대상: **원본 스크립트만 있는 새 드라마를, 새 세션에서 이 문서 하나만 읽고 즉시 Stage01~04까지 분석하려는 에이전트(Claude/Sonnet 병렬 또는 GPT).**
목적: (1) "형식만 베낀 가짜 산출물"을 막고, (2) 두 진영(GPT/Codex의 커버리지 강점 + Claude/Sonnet의 깊이 강점)의 장점만 흡수한 **이중 슬롯 + 이중 floor** 설계를 실제 저작에 강제한다.

> **이 문서의 자립성 원칙**: 이 파일 하나만 읽으면 (a) 무엇을 어느 경로에 저작하는지, (b) 각 레코드의 정확한 키/enum, (c) 어떤 게이트 명령으로 어떻게 통과를 증명하는지까지 전부 알 수 있어야 한다. 외부 브리프를 못 읽는 상황(집/회사 전환, 한도초과로 세션 단절)에서도 즉시 이어서 분석할 수 있게 만든 것이 v2의 핵심 목표다.

---

## 0. 반드시 먼저 읽을 것 — 이 방법론이 존재하는 이유

이 프로젝트에서 GPT 산출물을 두 차례 정밀 감사했고, 둘 다 **구조는 그럴듯하지만 내용이 가짜이거나 얕은** 동일 계열의 문제였다.

- **사례 1 (도깨비/구미호 v6)**: `provider_call_count: 0`(실제 LLM 호출 없이 산출물만 생성), `{char}`/`{topic}` 미치환 템플릿 변수 43건, 900씬 중 623개(69%)가 동일 상투문구, arbiter 판정근거 900건 전량 동일, 1화 첫 씬이 실재하지 않는 가짜 씬. Claude의 실제 통계를 target으로 역산해 짜맞춘 것.
- **사례 2 (결혼못하는남자 Stage01~04)**: Stage01/02는 양호했으나 **Stage03 CharacterArc이 심각하게 게이밍**됨. 16화 전체에서 인물당 1건(총 6건, 화별 기록 없음), `trigger_beats` 67.7%가 서로 다른 인물 간 완전 동일, `arc_phase_map`이 6명 전원 동일(회차수를 기계적 4등분), `"by": "...metadata-derived"`라는 필드명 자체가 close-reading이 아니라 메타데이터 파생이라는 자백.

**핵심 교훈**: 스키마(키·폴더)를 베끼는 것은 쉽지만 "레코드 하나하나가 그 장면/그 인물 고유의 실제 근거에서 나왔는가"는 전혀 다른 문제다. §7(반게이밍)을 §3~§6과 **동일한 무게**로 취급하라. 스키마만 맞추고 반게이밍을 무시하면 사례 2가 반복된다.

### 0-b. v1 → v2에서 바뀐 것 (이 문서의 존재 이유)

두 진영의 산출물을 대조하니, **강점이 정확히 상보적**이었다.

| 진영 | 강점 | 약점 |
|---|---|---|
| GPT/Codex | 커버리지(회차마다 빠짐없이, 장거리 연결까지 폭넓게 뽑음) | 각 레코드의 근거가 얕고 상투적 |
| Claude/Sonnet | 깊이(레코드마다 그 장면 고유의 두꺼운 근거) | 커버리지 누락(장거리 브리지·회차별 최소치를 빠뜨림) |

v2는 이 둘의 장점만 흡수한다.

1. **이중 슬롯(Claude 깊이 + 쿼리 가능성 동시 확보)**: CharacterArc·RelationshipArc의 상태를 `state_label`(**닫힌 enum**, 기계 쿼리용)과 `state_headline`(**산문 헤드라인**, 그 인물 고유 의미)로 분리한다. enum만 있으면 얕고, 산문만 있으면 집계가 안 된다 — 둘 다 강제한다.
2. **이중 floor**:
   - **깊이 floor(Claude 강점)**: 자유서술(evidence/note/description) 최소 40자, 헤드라인 최소 8자.
   - **커버리지 floor(GPT 강점)**: 회차당 최소 arc 행수·인물수, 장거리(gap≥5) cross-edge 쿼터, plant→payoff 페어링 최소율.
3. **전용 arc-state enum(코퍼스 실측 기반 신규)**: arc 상태값은 씬 기능 어휘(CORE_ENUM)를 **재사용하면 안 된다.** 코퍼스가 이미 `GROWTH/RESOLVE/FALL/ALLIANCE/RIVALRY/BETRAYAL` 같은, CORE_ENUM에 없는 arc 전용 토큰으로 수렴해 있었다. 그래서 `ARC_STATE_ENUM`(인물)·`REL_STATE_ENUM`(관계)을 따로 정의했다. (실측: 기존 정본에서 `PERIL`·`ORACLE` 같은 씬-기능 토큰이 state_label에 잘못 섞여 있던 것을 v2 게이트가 정확히 적발함.)

### 0-c. 기존 정본은 절대 깨지 않는다 (마이그레이션 정책)

- 기존 ~35작품(v1 스키마, `state_headline` 없음)은 **계속 v1 게이트(`verify_new_layers.py`)로 통과**시킨다. 이건 그대로 둔다.
- v2 게이트(`verify_new_layers_v2.py`)와 이 문서의 이중 슬롯 규칙은 **지금부터 저작하는 신규 작품에만** 적용한다.
- 기존 정본을 v2로 승격(state_headline 채우기 + state_label enum 정합화)하는 것은 **별도 승인 후** 일괄로만 진행한다. 승인 없이 정본을 건드리지 말 것.

---

## 1. 전체 파이프라인 개요

```
원본 스크립트(hwp/txt)
   │  (실제로 전량 읽는다 — 이 단계를 건너뛰면 이후 모든 게 가짜다)
   ▼
Stage01  SceneCard            — 씬 단위 근거층, SSOT(Single Source of Truth)
   │
   ▼
Stage02  SequenceBlueprint    — 씬을 goal-obstacle-turn 단위로 묶은 시퀀스층
   │
   ▼
Stage03  EpisodeArc + FullSeriesArc          — 회차/시리즈 집계·해석층
         + LocalEdge          — 화내·인접화 인과
         + CharacterArc  ★이중슬롯 — 인물별 "회차마다" 상태변화
         + RelationshipArc ★이중슬롯 — 관계쌍별 "회차마다" 상태변화
         + PayoffCandidate    — 장거리 연결 후보(확정 아님)
   │
   ▼
Stage04  CrossEpisodeEdge(fan-in)  — 전 화를 다 읽은 뒤에만 확정하는 장거리 콜백/복선/서브플롯
         + 시즌 통합 검증
```

각 Stage는 **이전 Stage의 산출물에 실재하는 것만** 근거로 삼는다. 존재하지 않는 씬/시퀀스를 상위층에서 지어내면 즉시 사고다(사례1의 "가짜 씬 1화").

### 저작 실행 모델 (역할 분담)
- **실 저작(대량 레코드 생성)은 Sonnet 멀티에이전트 병렬(~8) 또는 GPT가 수행**한다. 회차 단위로 병렬 분할하면 자연스럽게 커버리지 floor를 만족시키기 쉽다.
- **설계·게이트·팬인(Stage04)·최종 검증은 순차로 취합**한다.
- 어느 경로든 **최종 증거는 게이트 스크립트의 실제 출력(ERRORS 0)** 이다. 자기보고("완료했습니다")는 증거가 아니다.

---

## 2. 원본 소싱 원칙

1. **원문을 실제로 전량 읽는다.** hwp/txt 추출본을 씬 단위로 끝까지 읽고 title/intent_gist를 직접 도출한다. `raw_script_exported: false`(원문 미저장, 저작권 위생)와 `direct_reading_required: true`(실제 정독)는 **반드시 함께, 실제로** 지켜져야 한다. "원문을 저장하지 않는다"가 "안 읽어도 된다"로 오용되면 안 된다.
2. **씬 번호는 원문 마커(S#N, 씬N, #N 등)를 그대로 따른다.** 혼용 마커 오집계로 결번/중복이 생기므로 회차 종료 후 `1..N` 연속성을 재확인한다.
3. **여러 청크로 쪼개진 장면은 같은 scene_no로 병합**하고, 빈 헤딩/잡음 레코드는 필터링한다.
4. **인물명 표기를 작품 전체에서 하나로 고정.** 저작 시작 전 등장인물 대표 표기 목록을 만들어 모든 에이전트/세션에 동일 전달(예: 성이 겹치면 성+이름 전체를 기본형). 표기 흔들림("영은수" vs "이은수")은 실제로 반복된 결함이다.

---

## 3. Stage01 — SceneCard (SSOT)

원본을 씬 단위로 직접 읽고 만드는 최하위 SSOT. 이후 모든 Stage는 이 레이어의 scene_no/core만 참조할 수 있다.

**경로**: `authored/<work>_<NN>.seqcard.jsonl` (회차별 JSONL) + `authored/<work>_<NN>.episode_meta.json` (회차 메타)

**레코드 스키마**
```json
{"work_id": "<work>_<NN>", "scene_no": 12, "heading": "<원문 씬 헤딩>",
 "title": "<그 씬 핵심 압축 소제목, 씬마다 고유>",
 "intent_gist": "<그 씬이 극에서 하는 일 1~2문장, 씬마다 고유>",
 "core": "<CORE_ENUM 16종 중 1개>", "core2": "<CORE_ENUM 또는 null>",
 "skin": "<장소/시간 등 표면정보>", "by": "<작성 주체 식별자>"}
```

**CORE_ENUM (16) — `core`/`core2`/LocalEdge·CrossEdge `label` 전용 유일 유효값**
```
ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH,
REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK
```
이 16종 밖의 값("SETUP", "설정", "위기고조" 등)은 스키마 위반이다(실제 682건 발생 이력). **주의: CORE_ENUM은 "씬 기능" 어휘다. 인물/관계 arc 상태(§5.4/§5.5)에는 절대 쓰지 않는다** — arc에는 별도 enum(§5.4a)을 쓴다.

**episode_meta.json `core_dist`**: `core`와 `core2`를 **합산** 집계(core만 세지 않음).

**반게이밍(Stage01)**: title/intent_gist는 씬마다 실제로 달라야 함. `{char}`/`{topic}` 미치환 변수가 하나라도 남으면 fabrication 증거. 해설 필드에서 "고정 골격 + CORE_ENUM만 교체" 패턴(예: `"구조적으로 {X}에서 {Y}로 이동하는 전환점이다"`) 확인 — CORE_ENUM 단어를 마스킹한 뒤 골격 반복이 15%를 넘으면 FAIL.

---

## 4. Stage02 — SequenceBlueprint

Stage01 씬을 goal-obstacle-turn "시퀀스"로 묶는 층.

**경로**: `authored_seq/<work>_<NN>.seqblueprint.jsonl` (회차별)

**레코드 스키마 — 정확히 이 18키 (누락·추가 모두 FAIL)**
```
seq_id, work_id, episode_no, seq_index, member_scene_nos, scene_span,
scene_budget, sequence_intent, goal, obstacle, value_shift, turn_type,
turn_class, core_mix, pov_char, place_cluster, runtime_share, by
```
- `seq_id = "<work>_<NN>_S<II>"` (II = 회차 내 순번 2자리, 01부터)
- `value_shift`는 반드시 `{"from":"...","to":"..."}` dict. 문자열이면 FAIL.
- `turn_class`는 아래 4버킷 중 하나(파생값), `turn_type`과 별개 필드.
- `core_mix` 각 원소는 member 씬들의 실제 `core`/`core2`에 **실재**해야 함.
- 키 리네임 절대 금지(`episode_no`→`ep_no` 등은 EXTRA로 즉시 FAIL).

**turn_class 4버킷**: RISE←{RISE,BOND,PUNISH} / FALL←{FALL,LOSS} / REVEAL←{REVEAL,ORACLE,REVERSAL} / STALL←{STALL,HOOK,CONFLICT}

**불변식**: I-COVER(회차 모든 scene_no가 정확히 한 시퀀스 member로 덮임, 누락·중복 0) / I-PARTITION(member scene_no 전역 중복 없음) / I-COUNT(Σscene_budget == 회차 씬 총수) / `scene_span==[min,max]`, `scene_budget==len(member)` / member는 연속·오름차순.

**밀도 floor**: `ratio = 총시퀀스수/총씬수 ≥ 0.11` (실측 0.145~0.26). 시퀀스는 대개 3~7씬. 0.05~0.10(시퀀스당 15~20씬)이면 **과소분절 = FAIL**.

---

## 5. Stage03 — 해석층 + 렛저 4종 (v2 이중 슬롯 적용 지점)

Stage01/02를 근거로 회차·시리즈 해석과 인물/관계/인과 렛저를 만든다. **이 프로젝트에서 게이밍이 가장 잦았던 지점** — §7과 함께 읽어라.

### 5.1 EpisodeArc — 정확히 이 13키
경로: `authored_arc/<work>_<NN>.episodearc.json` (회차별)
```
work_id, episode_no, scene_count, sequence_count, dramatic_question,
act_structure, entry_state, exit_state, turning_point,
central_conflict_axis, episode_function, core_dist, by
```
- `act_structure`의 seq_span들이 `1..sequence_count`를 빈틈·중복 없이 타일링.
- entry_state/exit_state/dramatic_question/central_conflict_axis/episode_function/core_dist 전부 채움.

### 5.2 FullSeriesArc — 정확히 이 17키
경로: `authored/<work>_full_series_arc.json` (작품 1개)
```
series, episodes_total, scenes_total, sequences_total, logline,
central_dramatic_question, theme_statement, protagonist, antagonist,
season_structure, macro_turning_points, resolution, open_ending, tone,
conflict_persist, series_core_dist, by
```
- `season_structure=[{"movement":"...","episode_span":[a,b],"beat":"...","hinge":"..."}]` — episode_span이 `1..episodes_total` 타일링.
- `macro_turning_points=[{"episode":n,"event":"...","role":"..."}]`
- `protagonist={"name","want","need","arc","arc_curve":[...]}`
- `series_core_dist`는 전 회차 core_dist(core+core2 합산) 총합과 일치.
- 구스키마 리네임 금지(`total_episodes`→`episodes_total` 등).

### 5.3 LocalEdge (화내·인접화 인과) — 정확히 이 12키
경로: `authored_edges/<work>_<NN>.local_edges.jsonl` (회차별)
```
edge_id, work_id, edge_type, src_episode_no, src_scene_no, tgt_episode_no,
tgt_scene_no, gap_episodes, label, confidence, note, by
```
- 이 단계에서는 `edge_type="causal"`만, `gap_episodes`는 0(같은 화) 또는 1(다음 화 브릿지)만.
- **`label`은 서술문이 아니라 `tgt_scene_no` 씬의 실제 `core` 값과 동일한 CORE_ENUM 하나를 그대로 복사**한 것이어야 함(서술문 삽입은 위반 — 내이름은김삼순 저작 때 65건 실제 발생).
- `note`는 그 인과의 구체적 근거를 씬마다 다르게 서술. **깊이 floor: 최소 40자.**
- **커버리지 floor: 화당 최소 8개 이상**의 실질적 인과 엣지.

### 5.4 CharacterArc — 정확히 이 **9키** ★v2 이중 슬롯 + 가장 중요한 반게이밍 지점
경로: `authored_chararc/<work>_<NN>.chararc.jsonl` (**회차별 파일**)
```
work_id, character, episode_no, state_label, state_headline,
state_delta, trigger_scene_no, by, evidence
```
(v1 8키에서 **`state_headline` 1개 추가** = 이중 슬롯.)

- **`state_label`**: 아래 `ARC_STATE_ENUM`(닫힌 enum, 기계 쿼리용) 중 하나. **CORE_ENUM을 쓰지 말 것.**
- **`state_headline`**: 그 회차 끝 그 인물의 상태를 **그 인물 고유의 산문 한 줄**로(최소 8자). enum 값을 그대로 복사하면 FAIL(`state_headline == state_label` 금지). 이게 Claude 깊이 강점을 강제하는 슬롯이다.
- **`state_delta`**: 이전 회차 대비 변화 방향/정도(첫 등장 회차는 "series_start" 등).
- **`trigger_scene_no`**: 그 상태변화를 유발한, 그 회차·그 인물이 실제 등장하는 실재 scene_no.
- **`evidence`**: Stage01 intent_gist/title 근거의 구체 서술. **최소 40자(깊이 floor).** 다른 인물의 evidence와 동일 문장 재사용 금지 — 같은 사건도 "그 인물에게 어떤 의미였는지"는 인물마다 달라야 함.
- 인물명 표기는 작품 전체 통일(§2-4).

**★★★ "인물 × 회차" 조합마다 별도 레코드.** 6명이 16화 내내 나오면 최소 6×16(미등장 화 제외)에 가까운 수가 나와야 정상. "인물당 시리즈 요약 1건"으로 퉁치는 것이 사례2의 핵심 위반이었다.

**커버리지 floor(자동 강제, §8 게이트)**: CharArc 총량 ≥ max(4×회차수, ⌈0.12×총씬수⌉); **회차마다 ≥4행 AND 서로 다른 인물 ≥3명.**

#### 5.4a ARC_STATE_ENUM (14) — CharacterArc.state_label 전용 (코퍼스 실측 기반)
```
ESTABLISH, DESIRE, BOND, GROWTH, RESOLVE, CONFLICT, REVERSAL,
REVELATION, LOSS, FALL, PUNISH, RESCUE, RELIEF, SACRIFICE
```
(주의: CORE_ENUM과 겹치는 토큰도 있으나 **어휘 집합이 다르다**. arc에는 반드시 이 집합만 쓴다. `PERIL`·`ORACLE`·`HOOK`·`INTRO`·`ROMANCE`·`REUNION`은 arc-state에 없음 → 쓰면 FAIL. 대신 인물 성장/추락/희생 궤적 토큰 `GROWTH`/`RESOLVE`/`FALL`/`SACRIFICE`가 있음.)

### 5.5 RelationshipArc — 정확히 이 **10키** ★v2 이중 슬롯
경로: `authored_relarc/<work>_<NN>.relarc.jsonl` (회차별)
```
work_id, char_a, char_b, episode_no, relation_state, relation_headline,
relation_delta, trigger_scene_no, evidence, by
```
(v1 9키에서 **`relation_headline` 1개 추가**.)

- **`relation_state`**: 아래 `REL_STATE_ENUM` 중 하나.
- **`relation_headline`**: 그 관계쌍 고유의 산문 한 줄(최소 8자, enum 복사 금지).
- **`evidence`**: 최소 40자, 다른 관계쌍과 동일 문장 재사용 금지.
- CharacterArc와 동일 원칙 — **관계쌍 × 회차** 조합마다 그 회차 실제 상호작용 근거의 개별 레코드.

**커버리지 floor**: RelArc 총량 ≥ max(3×회차수, ⌈0.09×총씬수⌉); **회차마다 ≥3행.**

#### 5.5a REL_STATE_ENUM (14) — RelationshipArc.relation_state 전용
```
BOND, ALLIANCE, ROMANCE, DEPENDENCE, RECONCILE, SUSPICION, CONFLICT,
RIVALRY, BETRAYAL, DISTANCE, DOMINANCE, DESIRE, LOSS, REUNION
```

### 5.6 PayoffCandidate — 정확히 이 7키
경로: `authored_edges/<work>_<NN>.payoff_candidates.jsonl` (회차별)
```
candidate_id, work_id, episode_no, scene_no, edge_type_guess, description, by
```
- `edge_type_guess ∈ {plant_payoff, callback, subplot_counterpoint, resolved_here}` (`resolved_here`는 마지막 화에서 그 화 안에 회수 확인된 경우만).
- `description` **최소 40자(깊이 floor).**
- "장거리 연결 후보 메모"일 뿐 최종 확정 엣지가 아님. 화 하나만 읽고 단정 금지 — **화당 2~5개로 절제.**

### 5.7 ID 네임스페이스 규칙 (우회 불가)
```
LocalEdge:        edge_id      = f"{work}_e{episode_no:02d}{seq:03d}"
PayoffCandidate:  candidate_id = f"{work}_p{episode_no:02d}{seq:03d}"
CrossEpisodeEdge: edge_id      = f"{work}_x{seq:03d}"
```
- `episode_no`는 항상 `src_episode_no`. `seq`는 **그 src_episode_no 그룹 전체**의 순번(1부터). 인접화 브릿지(gap=1)를 tgt 화 파일에 저장하더라도 번호는 src_episode_no 그룹의 이어지는 순번(예: 1화 자체 엣지가 e01001~e01036이면 1→2 브릿지는 e01037).
- 병렬 저작 시 "전역 고유하게 하라"는 자연어 지시만으로는 반드시 충돌한다(2회 실제 발생). **위 고정 포맷 문자열을 그대로 지시에 박아 넣어라.**

---

## 6. Stage04 — CrossEpisodeEdge (장거리 fan-in) + 시즌 통합

**전 화를 다 읽은 뒤에만** 수행하는 마지막 단계. Stage03 PayoffCandidate를 재료로, 원문/씬카드를 대조해 확정된 장거리 연결만 CrossEpisodeEdge로 승격한다.

**경로**: `authored_edges/<work>_cross_episode_edges.jsonl` (작품 전체 1개)

**스키마**: LocalEdge와 동일한 12키. 단 `edge_type ∈ {callback, plant_payoff, subplot_counterpoint}`(causal 아님), `gap_episodes ≥ 1`(장거리일수록 큼, 실측 최대 15).

**확정 절차**
1. Stage03 모든 PayoffCandidate를 episode_no 순으로 훑는다.
2. 각 candidate의 `description`이 가리키는 회수가 실제 어느 화 몇 번 씬에서 일어나는지 Stage01 title/intent_gist를 직접 대조 확인(대조 없이 지어내지 말 것).
3. 확정된 것만 CrossEpisodeEdge로 기록, `label`은 tgt_scene_no의 실제 core 값 그대로.

**커버리지 floor(회차수 ≥ 4일 때 자동 강제)**: CrossEdge 총량 ≥ ⌈0.75×회차수⌉; **장거리(gap≥5) ≥ max(3, ⌈회차수/6⌉)**; plant→payoff 회수 ≥ ⌈0.3×plant_payoff 후보수⌉. (이것이 GPT의 커버리지 강점을 흡수하는 지점 — Sonnet이 흔히 빠뜨리던 장거리 브리지를 정량으로 강제한다.)

---

## 7. 반게이밍 규칙 전체 목록 (실제 적발 근거)

게이트(§8)가 자동 검사한다. 통과 자기보고 전에 아래를 직접 계산하라.

1. **텍스트 다양성 15% 룰**: note/evidence/description/headline 등 자유서술 필드에서 완전 동일 문자열이 전체의 15% 이상이면 FAIL. (사례1: 69%. 사례2: 67.7%.) v2는 `state_headline`/`relation_headline`에도 이 룰을 적용한다.
2. **골격 마스킹 재검사**: CORE_ENUM 등 가변 슬롯 마스킹 후 다시 15% 룰 적용. 표면이 달라도 골격 같으면 상투문구.
3. **미치환 템플릿 변수 금지**: `\{[a-zA-Z_]+\}` 매칭이 하나라도 있으면 즉시 FAIL.
4. **참조 무결성**: src/tgt/trigger_scene_no 등 모든 참조는 실재 값만. 없는 씬 참조 시 FAIL.
5. **ID 전역 고유성**: edge_id/candidate_id 100% 고유(§5.7 준수 시 자동).
6. **arc는 "인물(쌍)×회차" 개별 레코드**여야 하며 같은 회차 서로 다른 인물(쌍)이 완전 동일 문구 공유 시 FAIL. 인물별 phase/start/end가 전원 동일한 것도 같은 징후.
7. **회차 기계적 등분 금지**: "전체를 4등분해 setup/expansion/reversal/closure" 방식은 실제 전환점과 무관한 게이밍 신호. 각 인물 실제 전환점(trigger_scene_no 근거)으로 구간을 나눠라.
8. **provider_call_count 류 정직성**: 남긴다면 실제 값을 적어라. 0이면서 "close-reading 했다"는 모순. 이 프로젝트 관례는 그런 필드를 안 만들고 게이트 실행 로그(ERRORS 0)로 증명.
9. **자기보고 정합성**: report.md(사람용)와 validation.json(기계 판정)이 FAIL vs PASS로 모순되면 안 됨. 검증은 항상 최신 스크립트 재실행 기준.
10. **이중 슬롯 우회 금지(v2 신규)**: `state_headline`을 enum 복붙(`GROWTH`)으로 채우거나 8자 미만으로 때우면 FAIL. 헤드라인은 그 인물/관계 고유의 실제 의미여야 한다.

---

## 8. 검증 절차 (증거의 최종 기준)

모든 Stage 저작 후 아래를 실행하고 **실제 출력이 "ERRORS 0"이 될 때까지 수정 반복**한다. 자기보고는 증거가 아니다.

게이트는 **repo 루트(seqcard_ko의 부모 디렉토리)에서 실행**한다. 로컬 정본 기준 경로:
- Windows: `C:\claude\db` 에서 실행, BASE=`seqcard_ko`
- (샌드박스 bash 매핑: `/sessions/.../mnt/claude/db`)

```bash
# 1) Stage01~02(+03 EpisodeArc/FullSeriesArc) 엄격 3층 구조 게이트
python3 seqcard_ko/verify_work_strict.py <work_id>
#   기대: "ERRORS 0 — 엄격게이트 ALL PASS"
#   (키셋 정확·value_shift{from,to}·turn_class 4버킷·밀도 floor ratio≥0.11 검사)

# 2) v2 신규계층 게이트 (이중 슬롯 + 이중 floor) ★신규 작품은 이걸로 검증
python3 seqcard_ko/verify_new_layers_v2.py <work_id>
#   기대: "ERRORS 0 — [<work_id>] 신규계층 v2 강한게이트 ALL PASS"

# (기존 v1 정본은 계속 이걸로만 통과시킨다 — 건드리지 말 것)
python3 seqcard_ko/verify_new_layers.py <work_id>
```

**v2 게이트가 검사하는 것**: 정확한 키셋(state_headline/relation_headline 포함, 누락·초과 FAIL) · state_label∈ARC_STATE_ENUM · relation_state∈REL_STATE_ENUM · LocalEdge label∈CORE_ENUM · headline 길이≥8 및 enum≠headline · 깊이 floor(evidence/note/description ≥40자) · 참조 무결성 · ID 전역 고유성 · gap_episodes 산술 일치 · 다양성 15%(헤드라인 포함) · 미치환 변수 부재 · 커버리지 floor(회차별 arc 행/인물 최소, 장거리 cross-edge 쿼터, plant→payoff 페어링).

게이트가 없는 환경(GPT 단독)에서는 위 항목을 **직접 코드로 재현 실행**하고 로그를 산출물과 함께 첨부하라. "검증했다"는 문장은 증거가 아니다.

---

## 9. 산출 보고 형식

작품 완주 시 보고에 반드시 포함:
- 회차수, 총 씬수, 총 시퀀스수, ratio(시퀀스/씬)
- 렛저 4종 레코드 수(LocalEdge+CrossEdge / CharacterArc / RelationshipArc / PayoffCandidate). **CharacterArc/RelationshipArc 수가 "인물(쌍) 수"에 근접하면 즉시 의심** — 정상은 "인물수 × 등장회차수"에 가까운 큰 수.
- `verify_work_strict.py`, `verify_new_layers_v2.py` 각각의 실제 출력(ERRORS 0 여부)
- 저작 중 발견·수정한 실제 결함 목록(있다면). "0건"만 보고하기보다 어떤 자체 검증을 거쳤는지 함께 보고할 것.

---

## 10. 새 드라마 즉시 착수 체크리스트 (이 문서만으로 실행)

- [ ] 원문 hwp/txt를 확보하고 **전량 정독**(요약·역산 아님)
- [ ] 인물 대표 표기 목록 확정, 모든 병렬 에이전트에 동일 전달(§2-4)
- [ ] 회차 단위로 병렬 분할(권장 ~8 Sonnet)하되 각 에이전트에 §5.7 ID 포맷 문자열을 그대로 지시
- [ ] Stage01: `authored/<work>_<NN>.seqcard.jsonl` — title/intent_gist 씬마다 고유, core∈CORE_ENUM, `{var}` 잔여 0
- [ ] Stage02: 18키 정확, value_shift는 dict, I-COVER/PARTITION/COUNT 충족, ratio≥0.11
- [ ] Stage03 EpisodeArc 13키 / FullSeriesArc 17키 정확
- [ ] Stage03 LocalEdge: label=tgt core 값(서술문 아님), note≥40자, **화당≥8**
- [ ] **Stage03 CharacterArc 9키: state_label∈ARC_STATE_ENUM, state_headline 산문(≥8자, enum복사 아님), evidence≥40자, "인물×회차" 개별, 회차당≥4행·≥3인물**
- [ ] **Stage03 RelationshipArc 10키: relation_state∈REL_STATE_ENUM, relation_headline 산문, evidence≥40자, "관계쌍×회차" 개별, 회차당≥3행**
- [ ] Stage03 PayoffCandidate 7키, description≥40자, 화당 2~5개
- [ ] Stage04 CrossEpisodeEdge: 전 화 정독 후 원문 대조로 확정, gap≥5 장거리 쿼터 충족, plant→payoff 회수율 충족
- [ ] `verify_new_layers_v2.py <work>` 실제 출력이 **ERRORS 0**
- [ ] 보고서와 기계 판정이 서로 모순되지 않음

---

## 부록 A: 최소 워크드 예시 (형식 감 잡기용)

가상 작품 `example_01`(1화, 씬 1~40 존재)에서 각 층 레코드 한 줄씩:

**Stage01 SceneCard**
```json
{"work_id":"example_01","scene_no":12,"heading":"S#12 병원 복도 - 낮","title":"수술 동의서 앞에서 굳는 진호","intent_gist":"진호가 어머니 수술 동의서에 서명을 망설이며 가족과 갈등이 처음 표면화된다","core":"CONFLICT","core2":"DESIRE","skin":"병원 복도/낮","by":"sonnet-a"}
```
**Stage03 CharacterArc (이중 슬롯)**
```json
{"work_id":"example_01","character":"진호","episode_no":1,"state_label":"CONFLICT","state_headline":"책임을 떠안기 직전 도망치고 싶은 마음과 싸우는 장남","state_delta":"series_start","trigger_scene_no":12,"by":"sonnet-a","evidence":"12번 씬에서 수술 동의서 앞에 굳어 서명을 미루는 모습으로 가족 부양 책임에 대한 회피 심리가 처음 드러난다"}
```
(주목: `state_label`은 enum `CONFLICT`, `state_headline`은 진호 고유 산문, `evidence`는 40자↑ 씬 근거.)

**Stage03 RelationshipArc (이중 슬롯)**
```json
{"work_id":"example_01","char_a":"진호","char_b":"어머니","episode_no":1,"relation_state":"DEPENDENCE","relation_headline":"아픈 어머니가 장남에게 결정권을 떠넘기며 형성되는 무언의 압박","relation_delta":"series_start","trigger_scene_no":12,"evidence":"어머니가 직접 결정을 미루고 진호를 바라보는 12번 씬에서 의존과 부담이 뒤섞인 관계축이 성립한다","by":"sonnet-a"}
```

---

## 부록 B: v2 산출물 자산 위치 (자립 참조)

- **게이트 스크립트**: `seqcard_ko/verify_new_layers_v2.py` (이중 슬롯 키 + ARC_STATE_ENUM/REL_STATE_ENUM + 이중 floor). v1 게이트 `seqcard_ko/verify_new_layers.py`는 기존 정본 전용으로 유지.
- **저작 브리프**: `seqcard_ko/_GRAPH_LAYER_BRIEF_v2.md` (Sonnet 병렬 에이전트 지시용 — 이 문서의 §5를 실행 지시로 압축).
- **본 설명서**: `seqcard_ko/claude_drama_analysis_method_manual_stage01_04_v2.md` (=이 파일).
- **v1 설명서**: `seqcard_ko/claude_drama_analysis_method_manual_stage01_04_v1.md` (기존 정본 기준, 배경/사례 원본).

---

*본 문서는 v1 설명서(CLAUDE-DRAMA-METHOD-STAGE01-04-V1)를 상위집합으로 포함하며, 두 진영(GPT 커버리지 + Claude 깊이) 산출물의 상보적 강점만 흡수한 이중 슬롯·이중 floor 병합설계를 실제 저작에 강제하도록 재구성했다. 기존 ~35작품 정본(v1 스키마)은 v1 게이트로 유지되고, v2 규