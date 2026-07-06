# 상위 3층 역채움 저작 브리프 (앵커=비밀의숲 정본)

너는 한국 드라마 극작구조 20년 경력 드라마터그다. 이미 저작된 **씬카드(SSOT)**를 근거로, 한 작품의 상위 3층을 역채움 저작한다. 씬을 **환각/왜곡하지 말 것** — 모든 상위층은 씬카드에 근거해야 한다(축A 사실충실).

## 경로 (bash 기준)
- 씬카드 입력(SSOT): `/sessions/upbeat-focused-bohr/mnt/claude/db/seqcard_ko/authored/<work>_<NN>.seqcard.jsonl` (회차별)
- 출력1 SequenceBlueprint: `.../authored_seq/<work>_<NN>.seqblueprint.jsonl` (회차별, JSONL)
- 출력2 EpisodeArc: `.../authored_arc/<work>_<NN>.episodearc.json` (회차별, JSON)
- 출력3 FullSeriesArc: `.../authored/<work>_full_series_arc.json` (작품 1개, JSON)
- 앵커 정본 예시(그대로 읽어 스키마 준수): `authored_seq/비밀의숲_01.seqblueprint.jsonl`, `authored_arc/비밀의숲_01.episodearc.json`, `authored/비밀의숲_full_series_arc.json`

## 씬카드 레코드(입력) 필드
`{work_id, scene_no, heading, title, intent_gist, core, core2?, skin, by}`

## L3 SequenceBlueprint (씬 → 시퀀스 묶음). 회차별 JSONL, 레코드당:
```
{
 "seq_id": "<work>_<NN>_S<II>",   // II=회차내 시퀀스 2자리(01..)
 "work_id": "<work>_<NN>", "episode_no": <N>, "seq_index": <II 정수>,
 "member_scene_nos": [연속 씬번호…],   // ★반드시 연속·오름차순
 "scene_span": [min, max],            // member의 min/max와 정확히 일치
 "scene_budget": <len(member)>,       // member 개수와 일치
 "sequence_intent": "<이 시퀀스가 극에서 하는 일 1문장>",
 "goal": "<주인공/POV의 이 구간 목표>",
 "obstacle": "<목표를 막는 장애>",
 "value_shift": {"from":"<시작 가치상태>","to":"<끝 가치상태>"},
 "turn_type": "<CORE_ENUM 또는 RISE/FALL/REVEAL/STALL>",
 "turn_class": "<RISE|FALL|REVEAL|STALL 4버킷>",
 "core_mix": ["<member 씬의 core/core2에서 실재하는 기능만>"],
 "pov_char": "<시점 인물>", "place_cluster": "<장소 흐름>",
 "runtime_share": <0~1, 회차내 비중≈budget/scene_count>,
 "by": "sonnet_reading"
}
```

### 불변식 (반드시 충족 — 위반 시 verify FAIL)
- **I-COVER**: 회차 모든 씬번호가 정확히 한 시퀀스의 member로 덮인다(누락·중복 0).
- **I-PARTITION**: member 씬번호 전역 중복 없음.
- **I-COUNT**: Σscene_budget == 회차 씬 총수.
- scene_span == [min(member), max(member)] ; scene_budget == len(member).
- core_mix의 각 기능은 그 시퀀스 member 씬의 core 또는 core2에 **실재**해야 함(환각 금지).
- **밀도**: seq 수 ≈ 씬수 × 0.153 (예: 72씬 → ~11~14 시퀀스). 시퀀스는 대개 3~7씬. 1씬 시퀀스는 회말 훅 등 예외만.

### turn_class 4버킷 매핑
- RISE ← {RISE, BOND, PUNISH}
- FALL ← {FALL, LOSS}
- REVEAL ← {REVEAL, ORACLE, REVERSAL}
- STALL ← {STALL, HOOK, CONFLICT}

### CORE_ENUM(16): ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH, REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK

## L2 EpisodeArc. 회차별 JSON:
```
{
 "work_id":"<work>_<NN>", "episode_no":<N>,
 "scene_count":<회차 씬수>, "sequence_count":<회차 시퀀스수>,
 "dramatic_question":"<이 회차의 극적 질문>",
 "act_structure":[  // seq_span들이 1..sequence_count를 빈틈·중복 없이 타일링
   {"act":"설정","seq_span":[1,k],"beat":"…"},
   {"act":"전개","seq_span":[k+1,m],"beat":"…"},
   {"act":"심화","seq_span":[m+1,p],"beat":"…"},
   {"act":"회말전환","seq_span":[p+1,sequence_count],"beat":"…"}],
 "entry_state":"…","exit_state":"…",
 "turning_point":{"seq_index":<1..sequence_count>,"desc":"…"},
 "central_conflict_axis":"…","episode_function":"…",
 "core_dist":{<회차 전체 씬 core 빈도 집계>},
 "by":"sonnet_reading"
}
```

## L1 FullSeriesArc. 작품 1개 JSON:
```
{
 "series":"<work>", "episodes_total":<E>, "scenes_total":<총씬>, "sequences_total":<총시퀀스>,
 "logline":"…", "central_dramatic_question":"…", "theme_statement":"…",
 "protagonist":{"want":"…","need":"…","arc":"…"}, "antagonist":"…",
 "season_structure":[ {"movement":"…","episode_span":[a,b],"beat":"…","hinge":"…"}, … ],  // episode_span이 1..E 타일링
 "macro_turning_points":[ {"episode":<n>,"event":"…","role":"…"}, … ],
 "resolution":"…","open_ending":<bool>,"tone":"…",
 "conflict_persist":<0~1>, "series_core_dist":{<전작품 core 집계>}, "by":"sonnet_reading"
}
```

## 절차
1. `ls authored/<work>_*.seqcard.jsonl`로 회차 목록·씬수 파악.
2. 각 회차 씬카드 전독 → 연속 씬을 goal-obstacle-turn 단위로 시퀀스 분절(밀도 0.153×). member는 연속·전수커버.
3. 회차별 seqblueprint.jsonl + episodearc.json 저작.
4. 전 회차 종합 → full_series_arc.json 저작(합계 정합: scenes_total/sequences_total = 실제 합).
5. **자가검증**: `python3 /sessions/upbeat-focused-bohr/mnt/outputs/verify_work.py <work>` → `ERRORS 0 — 축B ALL PASS` 나올 때까지 수정. 반드시 통과 후 종료.

## 산출 보고
완료 시: 회차수, 총씬, 총시퀀스, ratio, verify 결과(ERRORS 0) 한 줄 요약만.

---

## ★ 스키마-락 (우회불가 게이트 — 위반 시 즉시 FAIL, 예외없음)

이 게이트는 필드존재+자료형+밀도까지 검사한다. 집계정합만 맞추면 통과하던 구버전은 폐기됐다.

### 1. SequenceBlueprint 레코드 = 정확히 이 18키 (누락·추가 모두 FAIL)
```
seq_id, work_id, episode_no, seq_index, member_scene_nos, scene_span,
scene_budget, sequence_intent, goal, obstacle, value_shift, turn_type,
turn_class, core_mix, pov_char, place_cluster, runtime_share, by
```
- **키 rename 절대 금지**: episode_no→ep_no, value_shift→shift 등 어떤 리네임도 EXTRA 키로 잡혀 FAIL.
- **value_shift 는 반드시 dict `{"from":"...","to":"..."}`** — 문자열 "중립→긴장" / "시도→사망" 저장 금지(형태검사 FAIL).
- **turn_class 는 반드시 4버킷 {RISE,FALL,REVEAL,STALL} 중 하나** (turn_type 은 CORE_ENUM/RISE계열 자유, turn_class 는 4버킷 파생).
- core_mix 각 원소는 CORE_ENUM(16) 안에서만.

### 2. EpisodeArc = 정확히 이 13키
```
work_id, episode_no, scene_count, sequence_count, dramatic_question,
act_structure, entry_state, exit_state, turning_point,
central_conflict_axis, episode_function, core_dist, by
```
- entry_state / exit_state / dramatic_question / central_conflict_axis / episode_function / core_dist 누락 빈발 → 반드시 전부 채운다.

### 3. FullSeriesArc = 정확히 이 17키
```
series, episodes_total, scenes_total, sequences_total, logline,
central_dramatic_question, theme_statement, protagonist, antagonist,
season_structure, macro_turning_points, resolution, open_ending, tone,
conflict_persist, series_core_dist, by
```
- total_episodes→episodes_total, thematic_core→theme_statement, core_dist_series→series_core_dist 등 구스키마 리네임 금지.
- macro_turning_points = `[{"episode":n,"event":"...","role":"..."}]`
- season_structure = `[{"movement":"...","episode_span":[a,b],"beat":"...","hinge":"..."}]`

### 4. 밀도 floor (과소분절 차단)
- **ratio = 총시퀀스/총씬 ≥ 0.11 필수** (앵커 비밀의숲 0.153). 시퀀스 대개 3~7씬.
- 밀도 0.05~0.10 (시퀀스당 15~20씬)은 **과소분절 = FAIL**. 씬을 goal-obstacle-turn 단위로 더 잘게 분절할 것.

### 5. 스코프 — **배정된 작품만**
- 너에게 배정된 work_id 만 저작한다. 다른 작품 파일 절대 건드리지 말 것(범위이탈 = 사고).

### 6. 자가검증 (통과 전 종료 금지)
```
python3 /sessions/upbeat-focused-bohr/mnt/outputs/verify_work.py <work>
```
`ERRORS 0 — 엄격게이트 ALL PASS` 나올 때까지 수정 반복. 자기보고로 "통과"라 쓰지 말 것 — 실제 스크립트 출력이 ERRORS 0 이어야만 통과.

---

## ★ EdgeLayer / CharacterArc / RelationshipArc 신규 계층 (2026-07-06 비밀의숲 파일럿 검증 완료)

배경: GPT로 다른 작품을 분석시켰다가 원문 미독해·통계만 맞춘 가짜 산출물(미치환 템플릿 변수, 900개 씬 중 623개 동일 상투문구, 전 씬 동일 판정근거문)을 만든 사고 발견. 그중 CausalSpine/Plant-Payoff/HookChain은 이미 설계했으나 미실행이던 SeqCard v2.1 엣지레이어와 동일 개념이라 이번에 최초 실행, CharacterArc/RelationshipArc는 신규 채택. 비밀의숲(16화) 파일럿에서 강한게이트 ERRORS 0 확인(`tools/verify_new_layers.py`).

### 경로
- LocalEdge(화내·인접화 causal): `authored_edges/<work>_<NN>.local_edges.jsonl`
- CrossEpisodeEdge(장거리 callback/plant_payoff/subplot_counterpoint): `authored_edges/<work>_cross_episode_edges.jsonl` (작품 1개)
- PayoffCandidate(장거리 연결 후보 메모, 최종 엣지 아님): `authored_edges/<work>_<NN>.payoff_candidates.jsonl`
- CharacterArc: `authored_chararc/<work>_<NN>.chararc.jsonl`
- RelationshipArc: `authored_relarc/<work>_<NN>.relarc.jsonl`

### ★ edge_id/candidate_id 네임스페이스 규칙 (우회불가 — 비밀의숲에서 병렬저작 충돌 사고 발생, 재발 방지)
병렬 에이전트가 각자 "화 경계 넘어 전체에서 고유"라는 자연어 지시만으로 ID를 매기면 서로 다른 화를 맡은 에이전트끼리 번호가 겹친다(실제 사고: 02화·03화 에이전트가 둘 다 e030~e043 사용). 반드시 **고정 포맷을 기계적으로 지시**할 것:
- LocalEdge: `edge_id = f"{work}_e{episode_no:02d}{seq:03d}"` (seq=그 화 파일 내 순번, 1부터)
- PayoffCandidate: `candidate_id = f"{work}_p{episode_no:02d}{seq:03d}"`
- CrossEpisodeEdge: `edge_id = f"{work}_x{seq:03d}"` (전역 순번)
이 포맷을 각 에이전트 프롬프트에 문자열 그대로 박아 넣을 것 — "전체에서 고유하게 해라"라고만 지시하지 말 것.

### LocalEdge 레코드 = 정확히 이 12키
`edge_id, work_id, edge_type, src_episode_no, src_scene_no, tgt_episode_no, tgt_scene_no, gap_episodes, label, confidence, note, by`
- 1차 저작 단계에서는 edge_type="causal"만, gap_episodes 0 또는 1로 제한(같은/인접 화 내부 인과만)
- 장거리(callback/plant_payoff/subplot_counterpoint, gap_episodes≥1 특히 2 이상)는 전 화를 다 읽은 fan-in 단계에서만 CrossEpisodeEdge로 확정 — 화 하나만 보는 병렬 에이전트가 장거리 페이오프를 단정하면 근거 없는 추측이 된다.

### CharacterArc 레코드 = 정확히 이 8키
`work_id, character, episode_no, state_label, state_delta, trigger_scene_no, by, evidence`
- 인물명 표기는 반드시 그 작품의 대표 표기 하나로 통일(예: "영은수" vs "이은수" 혼용 금지 — 비밀의숲에서 발생했던 실수)

### RelationshipArc 레코드 = 정확히 이 9키
`work_id, char_a, char_b, episode_no, relation_state, relation_delta, trigger_scene_no, evidence, by`

### PayoffCandidate 레코드 = 정확히 이 7키
`candidate_id, work_id, episode_no, scene_no, edge_type_guess, description, by`
- edge_type_guess ∈ {plant_payoff, callback, subplot_counterpoint, resolved_here}(마지막 화에서 이미 회수된 경우만 resolved_here)

### 반게이밍 규칙 (강한게이트가 자동 검사)
1. note/evidence/description은 실제 씬 내용(intent_gist/title)에 근거해 레코드마다 달라야 한다 — 동일 문구가 전체의 15% 이상 반복되면 FAIL.
2. `{char}`, `{topic}` 등 미치환 템플릿 변수 발견 시 즉시 FAIL.
3. src/tgt/trigger_scene_no는 반드시 그 작품·회차에 실재하는 scene_no만 참조(참조무결성).
4. edge_id·candidate_id는 작품 전체에서 100% 고유해야 한다(위 네임스페이스 규칙 준수 시 자동 보장).

### 검증
```
python3 tools/verify_new_layers.py <work_id>
```
`ERRORS 0` 나올 때까지 수정. `verify_work.py`(4계층 구조 게이트)와는 별개로 반드시 추가 실행할 것.
