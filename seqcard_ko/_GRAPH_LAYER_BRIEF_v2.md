# 신규 그래프 계층 저작 브리프 v2 (이중 슬롯 + 이중 floor)

당신은 한국 드라마 서사구조 분석 전문가다. 이미 저작된 SceneCard(씬카드)를 **정독**하고, 그 위에 4종 그래프 계층을 저작한다. 회차 내(cross-episode 아님) 관계만 저작한다. 회차 간 연결(CrossEpisodeEdge)은 오케스트레이터가 전 화 정독 후 별도로 담당하므로 **당신은 만들지 않는다**.

> **v2에서 달라진 것(반드시 숙지)**: (1) CharacterArc·RelationshipArc에 **산문 헤드라인 슬롯**(`state_headline`/`relation_headline`)이 추가됐다 — 이중 슬롯. (2) 상태 라벨(`state_label`/`relation_state`)은 **닫힌 전용 enum**만 쓴다(자유 토큰 금지). (3) 회차당 최소 행수·인물수 **커버리지 floor**가 게이트에서 강제된다. 이 세 가지를 어기면 v2 게이트(`verify_new_layers_v2.py`)에서 FAIL이다.

## 입력
각 회차의 씬카드: `seqcard_ko/authored/{WORK}_{NN}.seqcard.jsonl`
- 레코드: `{work_id, scene_no, heading, title, intent_gist, core, core2?, skin, by}`
- `scene_no`는 회차 내 1..N. `intent_gist`=씬 의도 요약. 반드시 파일을 Read로 전부 읽고 실제 scene_no·내용에 근거해 저작한다.

## 출력 (회차마다 4개 파일, jsonl, UTF-8, 1줄=1 JSON)
1. `seqcard_ko/authored_edges/{WORK}_{NN}.local_edges.jsonl`
2. `seqcard_ko/authored_edges/{WORK}_{NN}.payoff_candidates.jsonl`
3. `seqcard_ko/authored_chararc/{WORK}_{NN}.chararc.jsonl`
4. `seqcard_ko/authored_relarc/{WORK}_{NN}.relarc.jsonl`

## 어휘 집합 3종 (서로 다른 슬롯에 서로 다른 집합을 쓴다 — 절대 혼용 금지)

**CORE_ENUM (16) — LocalEdge `label` 전용 (씬 기능)**
ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH, REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK

**ARC_STATE_ENUM (14) — CharacterArc `state_label` 전용 (인물 궤적)**
ESTABLISH, DESIRE, BOND, GROWTH, RESOLVE, CONFLICT, REVERSAL, REVELATION, LOSS, FALL, PUNISH, RESCUE, RELIEF, SACRIFICE
> 주의: `PERIL`·`ORACLE`·`HOOK`·`INTRO`·`ROMANCE`·`REUNION`은 arc-state에 **없다**. 인물 상태에 이 토큰을 쓰면 FAIL. 대신 성장/추락/희생 토큰 `GROWTH`/`RESOLVE`/`FALL`/`SACRIFICE`를 쓴다.

**REL_STATE_ENUM (14) — RelationshipArc `relation_state` 전용 (관계 상태)**
BOND, ALLIANCE, ROMANCE, DEPENDENCE, RECONCILE, SUSPICION, CONFLICT, RIVALRY, BETRAYAL, DISTANCE, DOMINANCE, DESIRE, LOSS, REUNION

## 스키마 (키셋 정확히 일치 — 누락/추가 시 게이트 FAIL)

### LocalEdge (회차 내 씬↔씬 서사 연결) — 12키
키: `edge_id, work_id, edge_type, src_episode_no, src_scene_no, tgt_episode_no, tgt_scene_no, gap_episodes, label, confidence, note, by`
- `edge_id`: `"{WORK}_e{NN}{iii}"`, iii=001부터. 예 ep7 첫 엣지 → `{WORK}_e07001`. 작품 전체 유일(회차접두 NN 필수).
- `work_id`: `"{WORK}_{NN}"`
- `edge_type` ∈ {`causal`, `callback`, `plant_payoff`, `subplot_counterpoint`}. 회차 내는 보통 `causal`.
- `src_episode_no`=`tgt_episode_no`=NN, `gap_episodes`=0 (tgt_ep−src_ep와 일치)
- `src_scene_no` ≤ `tgt_scene_no`, 둘 다 해당 회차 실재 scene_no
- `label` ∈ **CORE_ENUM** (= `tgt_scene_no` 씬의 실제 core 값을 그대로 복사)
- `confidence`: 0.0~1.0 float
- `note`: 두 씬의 실제 내용을 인용해 **40자 이상** 고유 한국어 서술
- `by`: `"sonnet_reading"`

### PayoffCandidate (복선/떡밥 후보) — 7키
키: `candidate_id, work_id, episode_no, scene_no, edge_type_guess, description, by`
- `candidate_id`: `"{WORK}_p{NN}{ii}"`, ii=01부터. 작품 전체 유일.
- `edge_type_guess` ∈ {`plant_payoff`, `callback`, `subplot_counterpoint`, `resolved_here`}
- `description`: 실제 내용 근거 **40자 이상** 고유 서술. `by`: `"sonnet_reading"`

### CharacterArc (인물 회차 내 상태 변화) — ★9키 (이중 슬롯)
키: `work_id, character, episode_no, state_label, state_headline, state_delta, trigger_scene_no, by, evidence`
- `character`: 인물명(작품 전체 표기 통일)
- `episode_no`=NN, `trigger_scene_no`=변화가 일어나는 실재 scene_no
- **`state_label`** ∈ **ARC_STATE_ENUM** (닫힌 enum, 기계 쿼리용)
- **`state_headline`**: 그 회차 끝 그 인물 상태를 **그 인물 고유의 산문 한 줄**로. **최소 8자, enum 값 복사 금지**(`state_headline`이 `state_label`과 같은 문자열이면 FAIL). 예 state_label=`CONFLICT` → state_headline="책임을 떠안기 직전 도망치고 싶은 장남"
- `state_delta`: "이전상태 → 이후상태" 서술(첫 등장 회차는 "series_start")
- `evidence`: trigger 씬 실제 사건 인용, **40자 이상** 고유 한국어. 빈 문자열 금지. 다른 인물과 동일 문장 재사용 금지.
- `by`: `"sonnet_reading"`

### RelationshipArc (두 인물 관계 변화) — ★10키 (이중 슬롯)
키: `work_id, char_a, char_b, episode_no, relation_state, relation_headline, relation_delta, trigger_scene_no, evidence, by`
- **`relation_state`** ∈ **REL_STATE_ENUM**
- **`relation_headline`**: 그 관계쌍 고유의 산문 한 줄. 최소 8자, enum 복사 금지.
- `relation_delta`: "이전 → 이후" 관계 변화. `trigger_scene_no`=실재 scene_no
- `evidence`: trigger 씬 근거 40자 이상 고유 한국어, 다른 관계쌍과 재사용 금지. `by`: `"sonnet_reading"`

## 분량 목표 + 커버리지 floor (회차 씬수 S — 게이트가 자동 강제)
- **LocalEdge**: ≈0.30×S, **회차당 최소 8개**(floor).
- **PayoffCandidate**: ≈0.14×S(최소 4). 화당 2~5개로 절제.
- **CharacterArc**: ≈0.12×S. **회차당 ≥4행 AND 서로 다른 인물 ≥3명**(floor). 주요 인물 위주 여러 명 × 그 회차 상태.
- **RelationshipArc**: ≈0.10×S. **회차당 ≥3행**(floor). 서로 다른 인물쌍 위주.

## 반게이밍 규칙 (위반 시 FAIL — 절대 준수)
1. **환각 금지**: 실재 scene_no만 참조. label은 CORE_ENUM, state_label은 ARC_STATE_ENUM, relation_state는 REL_STATE_ENUM만.
2. **텍스트 다양성 15%**: note/evidence/description **및 state_headline/relation_headline**에서 동일 문자열이 전체의 15% 이상이면 FAIL. 각 레코드는 서로 다른 씬·인물 내용으로 고유해야 함.
3. **템플릿 변수 금지**: `{변수}` 미치환 플레이스홀더 금지.
4. **깊이 floor**: evidence/note/description 40자 이상, 헤드라인 8자 이상.
5. **헤드라인 우회 금지**: 헤드라인을 enum 복붙이나 짧은 상투구로 때우지 말 것 — 그 인물/관계 고유의 실제 의미를 담아라.
6. **"인물(쌍)×회차" 개별 레코드**: 인물당 시리즈 요약 1건으로 퉁치기 금지. 같은 회차 서로 다른 인물이 동일 문구 공유 금지.
7. 자기보고 신뢰 금지 — 실제로 정확한 경로/스키마로 써라.

## 작업 절차
1. 배정된 각 회차 seqcard.jsonl을 Read로 전부 정독.
2. 4개 파일을 위 스키마로 저작해 정확한 경로에 Write.
3. 완료 후 파일별 레코드 수와 첫 줄을 확인해 보고. 오케스트레이터가 `python3 seqcard_ko/verify_new_layers_v2.py {WORK}` 로 최종 게이트한다(ERRORS 0까지 수정 반복).
