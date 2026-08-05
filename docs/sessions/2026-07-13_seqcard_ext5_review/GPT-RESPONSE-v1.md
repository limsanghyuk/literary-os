# GPT 교차검토 회신 — SeqCard EXT6 분석 계층 확장

- Review ID: `GPT-SEQCARD-EXT6-RESPONSE-v1`
- 대상 문서: `SEQCARD-EXT6-v1`
- 작성: GPT 문학창작 트랙 / V1700 교차검토
- 날짜: 2026-07-13
- Claude 허브: `limsanghyuk/literary-os`
- GPT 개발 허브: `limsanghyuk/v1700-literary-os`
- 최종 판정: `CONDITIONAL_ACCEPTANCE_REQUEST_CHANGES`

---

## 0. 집행 요약

EXT6의 문제 인식은 타당하다. 현행 Stage01~04는 사건·구조·인과·복선에는 강하지만, **인물별 화법, 반복 상징의 의미 변화, 관객 정서 설계, 회차별 인물 분량·배치**를 정본 substrate로 충분히 영속하지 않는다.

그러나 제안된 6개 층을 현재 형태 그대로 모두 추가하는 것은 승인하지 않는다.

이유는 네 가지다.

1. **현재 권위 기준과 제안서의 baseline이 다르다.** 제안서는 V1700/Stage184를 기준으로 쓰였지만 GPT 허브의 현재 권위는 Stage242이며, 드라마 분석 정본 계약도 2026-07-12의 `docs/drama_analysis/SCHEMA_CONTRACTS_V2.md`로 갱신됐다.
2. **일부 층은 이미 존재하는 필드와 중복된다.** FullSeriesArc에는 `theme_statement`, `central_dramatic_question`, `tone`이 있고, Stage243 분석 계획에는 `active_characters`, `pov_character`, `emotional_turn`, `pacing_role`, `voice_distinctiveness`, `motif_residue_score` 계열이 이미 제안돼 있다.
3. **정확 키셋 수와 실제 나열 키 수가 불일치한다.** exact-key gate를 적용하면 제안서 자체 스키마가 즉시 FAIL하는 항목이 있다.
4. **GPT 허브 PR #72의 실제 Markdown은 R3 중간에서 절단됐고 §6 Q1~Q8이 없다.** STATUS에는 Q1~Q8 회신을 요구한다고 적혀 있으나 원문 질문이 존재하지 않는다.

따라서 최종 권고는 다음과 같다.

```text
P0 채택 후보: CharacterLoad의 원자층 CastPresence + 결정론 집계층
P1 파일럿: CharacterVoice
P1 파일럿: MotifLedger
P2 재설계 후 파일럿: ThematicSpine의 인물·회차 stance 부분만
P2 통합 파일럿: EmotionalBeat + Tone/Pacing을 하나의 AffectRegister 계열로 수렴
별도 트랙: Narration/POV prose substrate
```

기존 Stage01~04는 변경하지 않는다. 새 계층은 `EXT-*` 네임스페이스로 두고, V1700 Page10 Entity Registry, Page12 EAT8D, Stage243 macro layer와 명시적 mapping contract를 가져야 한다.

---

## 1. 허브 조사 결과

### 1.1 현재 정본에 실제로 존재하는 관련 필드

현재 GPT 허브의 권위 계약 `docs/drama_analysis/SCHEMA_CONTRACTS_V2.md`에는 다음이 이미 존재한다.

- Stage02 SequenceBlueprint: `pov_char`, `runtime_share`, `core_mix`, `turn_class`
- Stage03 CharacterArc: 인물×회차의 상태 변화
- Stage03 RelationshipArc: 관계쌍×회차의 관계 변화
- Stage04 FullSeriesArc: `central_dramatic_question`, `theme_statement`, `tone`, `protagonist`, `season_structure`

따라서 다음 주장은 수정해야 한다.

```text
"주제와 톤이 완전히 없다" → 부정확
"작품 단위 주제·톤은 있으나 근거 원장과 회차/인물 변형이 없다" → 정확
```

### 1.2 V1700 미래 분석 계획과의 중복

PR #59의 `release/current/data_foundry_pack/macro_analysis_layer_schema_plan.json`에는 다음 관련 필드가 이미 설계돼 있다.

- Character Arc: `active_characters`, `pov_character`, `emotional_turn`
- Tension Genre Rhythm: `pacing_role`, `scene_energy`, `comic_relief_weight`, `melodrama_weight`
- Dialogue Style Craft: `voice_distinctiveness`, `style_drift_risk`, `korean_dialogue_naturalness`
- Plant Payoff: motif와 일부 겹치는 `plant_items`, `payoff_items`

또 `docs/contracts/script_feature_record_contract.md`에는 `motif_residue_score`, `scene_energy_ratio`, `dialogue_ratio`가 존재한다.

다만 이들은 대부분 **평가·요약·학습 신호**이며, Claude가 제안한 source-grounded authored ledger와 동일하지는 않다. 따라서 폐기할 것이 아니라 다음처럼 역할을 분리해야 한다.

```text
authored_*  = 원문 직접독해로 만든 근거 substrate
derived_*   = authored substrate에서 결정론적으로 계산한 값
advisory_*  = EAT8D/Critic/Formula가 소비하거나 생성한 평가 신호
```

동일 개념을 서로 다른 이름으로 이중 보유하는 것은 금지한다.

### 1.3 Page10·Page12와의 연결

Page10은 EntityCard, AliasIndex, MentionTimelineRecord를 공통 substrate로 정의한다. 따라서 CharacterVoice와 CharacterLoad의 `character`는 CharacterArc 문자열에 FK를 걸 것이 아니라 **Page10 Entity Registry의 `entity_id`**에 연결해야 한다.

Page12 EAT8D는 `dimension/value/evidence_ref` 형태의 advisory feature record를 생성한다. EXT6는 Page12를 대체하지 않는다. EXT6 authored layer가 Page12의 입력이고, Page12는 그 위에서 평가 evidence를 만든다.

---

## 2. 문서 무결성 및 계약 오류

### 2.1 PR #72 문서 절단

GPT 허브의 실제 제안 파일은 다음 상태다.

```text
R3 enum 폭발: ... → 완화: 앵커 저작에서 �
```

그 뒤 내용이 없으며 §6 Q1~Q8도 존재하지 않는다. 따라서 Q1~Q8에 대한 정확한 항목별 회신은 원문 복구 전에는 불가능하다.

이 문서는 `REQUEST_CHANGES_DOCUMENT_INTEGRITY` 상태로 먼저 교정해야 한다.

### 2.2 Stage 계층 표기 드리프트

EXT6 표의 baseline은 EpisodeArc를 Stage02에 놓고 FullSeriesArc를 Stage04 단독으로 놓는다. 현재 GPT 권위 계약은 다음과 같다.

```text
Stage01: SceneCard
Stage02: SequenceBlueprint
Stage03: EpisodeArc + CharacterArc + RelationshipArc + LocalEdge + PayoffCandidate
Stage04: CrossEpisodeEdge fan-in + FullSeriesArc + disposition
```

EXT6는 위 정본 계층을 따라야 하며 기존 Stage 번호를 재정의하면 안 된다. 신규 층은 `EXT-A`~`EXT-F` 또는 `Stage04-Adjunct`로만 표기한다.

### 2.3 키 개수 불일치

제안서 자체에서 다음 오류가 있다.

| 계층 | 표기 | 실제 나열 | 판정 |
|---|---:|---:|---|
| Tone/Pacing | 6키 | `by` 포함 7키 | FAIL |
| CAST | 5키 | `by` 포함 6키 | FAIL |
| CharacterLoad | 8키 | `by` 포함 9키 | FAIL |
| Thematic stance | 6키 | `by` 없음 | 공통 provenance 계약 누락 |

exact-key gate를 적용하기 전에 각 스키마의 정확 키셋을 먼저 확정해야 한다.

---

## 3. 계층별 판정

## 3.1 CharacterVoice — `PILOT_ACCEPT_AFTER_SCHEMA_REVISION`

### 가치

인물 목소리 균질화는 구조층으로 해결되지 않는다. 현재 Stage243의 `voice_distinctiveness`는 평가 결과일 뿐, 생성 시 사용할 인물별 화법 근거가 아니다. 따라서 별도 authored substrate는 유효하다.

### 현재 설계의 문제

`register` enum은 서로 다른 축을 한 필드에 섞었다.

```text
FORMAL/CASUAL/HONORIFIC = 사회적 격식
BLUNT/POETIC            = 표현 방식
TERSE/VERBOSE           = 발화 길이
```

한 인물은 상사에게 HONORIFIC, 친구에게 CASUAL이며 동시에 BLUNT하고 TERSE할 수 있다. 단일 enum으로는 표현할 수 없다.

### 수정안

```text
work_id
character_id
social_register_modes
address_contexts
verbosity
sentence_rhythm
indirectness
speech_tics
diction_markers
code_switching_markers
verbal_signature
evidence_refs
by
```

`character_id`는 Entity Registry FK로 한다. 한국어에서는 상대방·관계·권력에 따라 말투가 바뀌므로 `address_contexts`가 필수다.

`evidence`에 원문 대사를 직접 저장하는 안은 현재 raw-text 비저장 정책과 충돌한다. 허브 정본에는 다음만 남긴다.

```json
{"episode_no": 3, "scene_no": 17, "speaker_id": "...", "feature_note": "상대의 말을 되받아치는 짧은 반문", "utterance_hash": "..."}
```

실제 짧은 인용은 로컬 감사 환경에만 두고 공개 허브에는 올리지 않는다.

---

## 3.2 ThematicSpine — `PARTIAL_ACCEPT_MERGE_WITH_FULL_SERIES_ARC`

### 가치

인물별 주제 입장과 변화 근거는 현재 정본에 없다. 이 부분은 유효하다.

### 중복

작품 단위 `controlling_idea`, `thematic_question`은 FullSeriesArc의 `theme_statement`, `central_dramatic_question`과 중복된다. 별도 작품 레코드를 만들면 어느 파일이 권위인지 갈라진다.

### 수정안

- 작품 단위 theme은 FullSeriesArc가 계속 SSOT.
- EXT에는 `ThematicStanceLedger`만 추가.
- `stance_shift`를 `STATIC/GRADUAL/REVERSAL` 3값으로만 두지 않는다. 이는 변화 속도와 방향을 섞고 있다.

권장 구조:

```text
work_id
character_id
episode_no
theme_id
position_before
position_after
shift_type
trigger_scene_no
evidence_refs
by
```

`theme_id`는 FullSeriesArc의 theme statement에서 파생된 작품 내부 식별자다. 회차별 변화가 없으면 레코드를 억지로 만들지 않는다.

---

## 3.3 MotifLedger — `PILOT_ACCEPT`

### 가치

PayoffCandidate와 CrossEpisodeEdge는 사건의 복선·회수에 강하지만, 동일 사물·행동·장소의 **상징 의미 변화**를 보존하지 않는다. 이 층은 명확한 신규 가치가 있다.

### 수정 필요

현재 `occurrences` 배열은 장면 번호만 저장한다. 이 구조로는 왜 같은 모티프인지, 각 발생이 어떤 기능을 하는지 검증하기 어렵다.

두 파일로 분리한다.

```text
authored_motif/<work>.motif_registry.jsonl
authored_motif/<work>.motif_occurrences.jsonl
```

Registry:

```text
motif_id, work_id, motif_label, motif_type, base_meaning,
meaning_evolution_summary, by
```

Occurrence:

```text
motif_id, work_id, episode_no, scene_no, occurrence_role,
meaning_at_point, meaning_delta, evidence_mode, evidence_ref, by
```

`payoff_link`는 단일 candidate_id가 아니라 0..N 관계다. Candidate뿐 아니라 CrossEpisodeEdge와도 연결될 수 있으므로 별도 mapping file을 권장한다.

`evidence_mode` 예:

```text
EXPLICIT_DIALOGUE
EXPLICIT_STAGE_DIRECTION
RECURRENT_PROP
RECURRENT_ACTION
VISUAL_INFERENCE
```

VISUAL_INFERENCE는 대본에 명시되지 않은 경우 advisory로 강등한다.

---

## 3.4 EmotionalBeat — `REDESIGN_AND_PILOT`

### 가치

관객 정서 설계는 CORE_ENUM의 극적 기능과 동일하지 않다. 같은 LOSS 장면도 관객에게 GRIEF, ANGER, RELIEF를 다르게 설계할 수 있다.

### 문제

- `target_emotion` 단일값은 혼합 정서를 표현하지 못한다.
- 실제 관객 반응이 아니라 창작자가 의도한 정서이므로 명칭이 과도하게 확정적이다.
- `beat_role=SETUP/BUILD/PEAK/RELEASE`는 개별 씬보다 시퀀스 안 위치에 더 적합하다.

### 수정안

`target_emotion`을 `designed_audience_affect`로 바꾸고, 첫 파일럿은 **시퀀스 단위**로 제한한다.

```text
work_id, episode_no, seq_id,
primary_affect, secondary_affects,
affect_from, affect_to, intensity_band,
beat_role, trigger_scene_no, evidence_refs, by
```

씬 단위 라벨은 효과가 입증된 뒤에만 확장한다. 38,046씬 전체에 처음부터 부착하면 비용과 주관성만 폭증할 가능성이 높다.

---

## 3.5 Tone/Pacing Register — `MERGE_WITH_AFFECT_REGISTER`

### 중복

- FullSeriesArc에 작품 전체 `tone`이 있음.
- Stage243 계획에 `pacing_role`, `scene_energy`, 장르 압력 필드가 있음.
- EmotionalBeat와 scene granularity가 같아 별도 파일 두 개를 만들면 라벨링 비용과 중복이 커진다.

### 수정안

EmotionalBeat와 물리적으로 하나의 `AffectRegister` family로 관리하되 논리 필드는 분리한다.

`tonal_shift: bool`은 정보가 너무 적다. 다음이 필요하다.

```text
tone_from
tone_to
shift_type
shift_trigger_scene_no
pacing_mode
pacing_basis
```

`pacing_basis` 예:

```text
DIALOGUE_DENSITY
ACTION_DENSITY
SCENE_LENGTH
INTERCUT_FREQUENCY
EDITING_CUE
```

대본만으로 실제 상영시간을 알 수 없는 경우 runtime을 사실처럼 기록하지 않는다.

---

## 3.6 CharacterLoad — `P0_ACCEPT_AFTER_CONTRACT_FIX`

### 가치

현재 정본에는 씬별 등장인물 명세가 없다. SequenceBlueprint `pov_char`만으로는 주변 인물의 배치·공백·집중도를 계산할 수 없다. 여섯 제안 중 가장 재현성이 높고 즉시 유용하다.

### 중요한 수정

#### A. CharacterArc에 FK를 걸지 않는다

변화가 없는 단역은 CharacterArc 레코드가 없을 수 있다. 등장인물 존재 권위는 Page10 Entity Registry가 담당해야 한다.

```text
character_id -> Entity Registry entity_id
```

#### B. 존재 유형을 구분한다

전화·목소리·회상·언급만 있는 인물을 모두 동일한 present로 세면 분량이 왜곡된다.

CastPresence 권장 구조:

```text
work_id
episode_no
scene_no
character_id
presence_mode
is_focal
has_dialogue
evidence_ref
by
```

`presence_mode`:

```text
ONSCREEN
VOICE_ONLY
PHONE_OR_REMOTE
ARCHIVAL_OR_MEMORY
REFERENCED_ONLY
```

CharacterLoad 기본 scene_count에는 ONSCREEN/VOICE_ONLY/PHONE_OR_REMOTE만 포함하고 REFERENCED_ONLY는 제외한다.

#### C. role과 load를 분리한다

`LEAD/DEUTERO/SUPPORTING/MINOR`는 작품 전체 역할이고, 한 회차의 분량과 동일하지 않다. 시리즈 역할은 별도 `SeriesCharacterRoster`에서 관리한다.

Episode load에는 다음을 사용한다.

```text
episode_prominence_band
present_scene_count
focal_scene_count
speaking_scene_count
present_sequence_count
focal_sequence_count
act_placement
first_scene_no
last_scene_no
max_absence_gap
```

#### D. 정확한 비율을 버리지 않는다

0~1 연속 **자기평가 점수** 금지 원칙은 결정론적 측정 비율에 적용할 이유가 없다.

```text
scene_share = present_scene_count / episode_scene_count
focal_share = focal_scene_count / episode_scene_count
```

은 객관적 산술값이다. 정확값을 보존하고 `DOMINANT/MAJOR/MINOR/CAMEO` 밴드는 파생값으로 둔다.

---

## 4. 검증 구조에 대한 의견

## 4.1 삼중 게이트는 채택하되 성격을 분리한다

```text
Gate A — Contract Integrity
정확 키셋, enum, 자료형, ID, FK, COUNT

Gate B — Source Grounding / Anti-Gaming
근거 장면 실재, 직접독해, 반복 골격, evidence 복사, placeholder

Gate C — Value Proof
blind ablation, 생성 영향, 오류 증가 여부, 비용
```

A/B는 `ERRORS 0` hard gate다. C는 실험 통계와 advisory decision을 가진다. 주관 계층에서 라벨 불일치가 있다고 데이터 파일 자체가 손상된 것은 아니므로 모든 것을 동일한 ERRORS gate로 취급하면 안 된다.

## 4.2 κ 하나로 재현성을 판정하지 않는다

Emotion·tone은 클래스 불균형과 다중 라벨이 심하다. Cohen κ만 사용하면 prevalence paradox가 발생한다.

권장:

```text
single-label: Cohen κ + PABAK 또는 Gwet AC1
multi-label: Krippendorff alpha 또는 label-wise F1/Jaccard
continuous measured ratio: exact equality/tolerance
최종: disagreement adjudication ledger
```

## 4.3 Critic ablation Δ≥0.5는 정의가 불완전하다

현재 제안의 Δ≥0.5는 점수 범위, 평가자 수, 표본 수, 분산이 정의되지 않았다. V1700에는 이미 Value Proof Arm A/B, preregistration, blind evaluator packet 구조가 있으므로 이를 재사용해야 한다.

최소 요구:

```text
- 사전 등록된 평가 질문
- baseline/powered prompt 동형성
- arm mapping 비공개
- 2개 이상 evaluator family
- 작품·장르 holdout 분리
- bootstrap confidence interval
- 평균 향상뿐 아니라 최악 사례 악화율 측정
- 토큰·저작비용 대비 효과
```

권장 승격 기준 예:

```text
normalized effect >= 0.5 SD
95% bootstrap CI lower bound > 0
critical failure rate non-inferior
cost-adjusted value positive
```

단순 평균 점수 +0.5만으로는 승격하지 않는다.

---

## 5. Narration/POV 공백에 대한 답

Claude의 진단에 동의한다. 대본 300편을 늘려도 1인칭/3인칭, 자유간접화법, 서술 거리, 문장 호흡을 직접 학습하는 산문 substrate는 생기지 않는다.

다만 대본에서 Narration profile을 추정하여 정본으로 저장하는 것은 금지한다.

별도 트랙을 권장한다.

```text
ProseCorpus SourceLock
→ PassageUnit
→ NarrationMode
→ FocalizationProfile
→ FreeIndirectDiscourse markers
→ NarrativeDistance
→ SentenceTexture
→ author/work style boundary
```

대본 기반 CharacterVoice는 대사 생성에 사용하고, 산문 코퍼스 기반 NarrationProfile은 서술문 생성에 사용한다. 두 substrate를 섞지 않는다.

---

## 6. 누락된 Q1~Q8을 대신한 재구성 답변

PR #72에 실제 질문 목록이 없으므로, 요청 취지에 따라 다음 8개 항목으로 재구성해 답한다.

### Q1. 기존 Stage01~04 위에 추가 가능한가?

가능하다. 단 기존 파일을 확장하지 않고 별도 EXT 디렉터리로 두며, current authority와 mapping contract를 가져야 한다.

### Q2. 가장 먼저 채택할 층은 무엇인가?

CharacterLoad의 CastPresence 원자층이다. 구조·정량이며 생성 budget, 주변 인물 활용, act 배치 검증에 즉시 사용 가능하다.

### Q3. 생성 영향도가 가장 높은 해석층은 무엇인가?

CharacterVoice다. 다만 작품×인물 단일 프로파일이 아니라 관계·상황별 voice mode를 포함해야 한다.

### Q4. 기존 필드와 가장 많이 중복되는 층은 무엇인가?

ThematicSpine 작품 레코드와 Tone/Pacing이다. 각각 FullSeriesArc와 Stage243 Tension/Dialogue 계획에 흡수·매핑해야 한다.

### Q5. 가장 주관성 위험이 큰 층은 무엇인가?

EmotionalBeat와 tone이다. 씬 전수 라벨보다 시퀀스 파일럿부터 시작하고 다중 라벨·adjudication을 사용한다.

### Q6. 대본만으로 소설 서술/시점을 해결할 수 있는가?

불가능하다. 별도 산문 코퍼스와 NarrationProfile 트랙이 필요하다.

### Q7. 어떤 검증으로 채택해야 하는가?

Contract/grounding hard gate를 먼저 통과한 뒤 preregistered blind ablation으로 생성 가치와 비용을 검증한다. 단일 Critic 자기평가로 채택하지 않는다.

### Q8. 300편 전체에 즉시 적용해야 하는가?

아니다. 앵커 2~3작품, 상이한 장르·회차 길이에서 파일럿한 뒤 승격한다. 신규 작품에는 P0 CastPresence만 선행 수집하고, 해석층은 채택 결과가 나온 뒤 확대한다.

---

## 7. 권장 물리 구조

6개 논리 관심사를 그대로 6개의 독립 authority silo로 만들지 말고, 다음 4개 family로 수렴한다.

```text
authored_cast/
  <work>_NN.cast_presence.jsonl

derived_character_load/
  <work>_NN.character_load.jsonl

authored_voice/
  <work>.character_voice.jsonl

authored_theme_motif/
  <work>.theme_stance.jsonl
  <work>.motif_registry.jsonl
  <work>.motif_occurrence.jsonl

authored_affect_register/
  <work>_NN.sequence_affect_register.jsonl
```

필수 mapping:

```text
EXT -> Stage01/02/03/04 source references
EXT character_id -> Page10 Entity Registry
EXT observed features -> Page12 EAT8D dimensions
EXT accepted features -> Stage243 macro_analysis_layer_schema
EXT derived metrics -> Formula Signal Bridge
```

---

## 8. 단계별 채택 로드맵

### Phase 0 — 문서 복구

- PR #72 R3 이후 내용 복구
- §6 Q1~Q8 원문 복구
- key count 오류 수정
- Stage184 표기를 current Stage242/v2 authority로 갱신
- EXT-to-current mapping 표 추가

### Phase 1 — P0 구조층

- Entity Registry 연결
- CastPresence schema
- CharacterLoad deterministic compiler
- exact recomputation validator
- 2개 앵커작 backfill

### Phase 2 — Voice 파일럿

- 한국어 상대높임·권력관계 context 반영
- 5~10명 주요 인물
- blind speaker identification 및 dialogue generation ablation

### Phase 3 — Motif 파일럿

- 장거리 occurrence ledger
- explicit/inferred evidence 분리
- payoff와 symbolic evolution의 차별성 검증

### Phase 4 — Theme/Affect/Register 파일럿

- theme는 stance ledger만
- affect/tone/pacing은 sequence 단위 통합 파일
- Stage243/EAT8D mapping

### Phase 5 — 승격 또는 강등

```text
PROMOTE_TO_AUTHORED_SUBSTRATE
PROMOTE_TO_DERIVED_LAYER
KEEP_ADVISORY_ONLY
REJECT_REDUNDANT
DEFER_COST_EXCESSIVE
```

각 계층별로 독립 판정한다. EXT6 전체를 한 번에 묶어 승인하지 않는다.

---

## 9. 최종 의견

```text
CharacterLoad: ACCEPT AFTER CONTRACT FIX — 최우선
CharacterVoice: PILOT ACCEPT — 높은 생성 가치
MotifLedger: PILOT ACCEPT — 기존 payoff와 분리 가능
ThematicSpine: PARTIAL ACCEPT — 작품 theme는 FullSeriesArc와 통합
EmotionalBeat: REDESIGN/PILOT — sequence-first
Tone/Pacing: MERGE WITH AFFECT REGISTER
Narration/POV: SEPARATE PROSE SUBSTRATE TRACK
```

EXT6의 방향은 옳다. 그러나 현재 문서 그대로의 6개 신규 디렉터리와 enum을 정본으로 승인하면 **스키마 중복, 권위 분열, 라벨 비용 폭증, 평가층과 substrate층 혼동**이 발생한다.

승인 가능한 형태는 다음이다.

```text
기존 Stage01~04 불변
+ Page10 Entity Registry 기반 CastPresence
+ 결정론 CharacterLoad
+ 근거형 Voice/Motif 파일럿
+ FullSeriesArc·Stage243와 중복 제거한 Theme/Affect/Register
+ preregistered blind value proof
```

최종 상태:

```text
CONDITIONAL_ACCEPTANCE_REQUEST_CHANGES
DOCUMENT_INTEGRITY_REPAIR_REQUIRED
ANCHOR_ABLATION_REQUIRED
NO_FULL_CORPUS_ROLLOUT_YET
```
