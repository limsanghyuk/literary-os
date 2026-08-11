# PlannerInput(R5) / RuntimeSceneProjection(R8) 실행 권위 V1

상태: **ACTIVE_EXECUTION_GUIDE**  
범위: `seqcard_ko/reinforcement_v1/planner_input/`, `runtime_scene_projection/`  
상위 권위: 기존 Stage01~04와 CANONICAL THICK를 수정하지 않는다.

## 0. 왜 이 문서가 필요한가

Thick Sequence는 시퀀스의 `cast / event / info_shift / plant_payoff / scene_notes`를 보존한다. 그러나 Literary OS가 실제로 다음 회차·시퀀스를 설계하고 장면을 렌더링하려면 두 개의 실행용 파생 계층이 필요하다.

- **R5 PlannerInputRecord**: 회차 N을 기획하기 직전의 planning-boundary packet.
- **R8 RuntimeSceneProjection**: CANONICAL THICK를 장면 단위 실행 packet으로 펼친 deterministic projection.

과거 새계층 실행 설명서는 Thick만 만들고 R5/R8을 연결하지 않는 `dead sidecar`를 금지했고, 작품 완료 조건에 `R5/R8 검사`를 포함했다. 가을동화 초기 감사에서도 R5의 `unresolved_payoffs / subplot_debt / character_debt`가 전 회차 빈 배열이었던 것이 실제 결함으로 판정되었다. 따라서 R5는 단순 포맷 파일이 아니라 **회차 간 이월(carry-over) 정보를 실제로 담아야 한다.**

R8은 반대로 **독립 의미 저작층이 아니다.** Thick와 PlannerInput을 장면별로 배선하는 파생물이며, R8 자체의 문장을 별도의 창작 성과로 계상하지 않는다.

---

## 1. 권위 경계

### CANONICAL / AUTHORITATIVE
1. 원본 대본 / SourceLock
2. Stage01 SceneCard
3. Stage02 SequenceBlueprint / EpisodeArc
4. Stage03 CharacterArc / RelationshipArc / PayoffCandidate
5. Stage04 CrossEpisodeEdge
6. CANONICAL THICK Sequence

### DERIVED EXECUTION CONTRACT
7. R5 PlannerInputRecord
8. R8 RuntimeSceneProjection

R5/R8은 상위 정본을 덮어쓰지 않는다. 상위 정본 revision이 바뀌면 R5/R8은 재검증 또는 재생성한다.

---

## 2. R5 PlannerInputRecord의 목적

PlannerInput은 **대상 회차 N에서 처음 생길 사실을 미리 알려주는 요약문이 아니다.** 오직 N-1회까지 확정된 상태와 열린 장기축만 전달한다.

질문은 하나다.

> "N화를 설계하기 직전, 작가가 반드시 기억해야 하는 현재 상태·미해결 장기축·남은 부담은 무엇인가?"

### 필수 14개 top-level key

`schema, work_id, episode_no, previous_exit_state, character_states, relationship_states, unresolved_payoffs, active_causal_threads, remaining_episode_count, subplot_debt, character_debt, world_constraints, target_refs, source_hashes`

### R5 작성 규칙

#### EP01
- `previous_exit_state = null`
- `character_states = []`
- `relationship_states = []`
- `unresolved_payoffs = []`
- `active_causal_threads = []`
- debt 배열도 비운다.

#### EP02 이후
1. `previous_exit_state`
   - **직전 회차 EpisodeArc**의 `exit_state / central_conflict_axis / episode_function`을 그대로 planning boundary로 가져온다.
2. `character_states`
   - **직전 회차 CharacterArc**에서 인물별 최종 상태 1개를 사용한다.
   - 같은 인물의 레코드가 여러 개면 마지막 trigger 이후의 레코드 1개만 planning state로 채택한다.
3. `relationship_states`
   - **직전 회차 RelationshipArc**에서 관계쌍별 최종 상태 1개를 사용한다.
4. `unresolved_payoffs`
   - 직전 회차까지 실제로 등장한 THICK `plant_payoff.thread_id`만 대상으로 한다.
   - 직전 boundary 이전의 **가장 마지막 상태가 PAYOFF면 닫힌 thread**로 보고 제외한다.
   - 마지막 상태가 `PLANT/LINK/ESCALATION/CALLBACK/REACTIVATION/...`이면 열린 thread 후보이다.
   - 미래 회차의 statement·payoff 내용을 읽어 현재 상태를 만들면 안 된다.
5. `active_causal_threads`
   - 현재 planning boundary에서 실제로 살아 있는 open thread를 전달한다.
6. `subplot_debt`
   - 빈 배열을 관성적으로 만들지 않는다.
   - 열린 thread 중 중요·최근 thread의 **이미 확인된 최신 statement**를 근거로 아직 미결인 부담을 적는다.
7. `character_debt`
   - 직전 CharacterArc 상태가 다음 선택으로 어떻게 이어질지 아직 미결임을 기록한다.
   - 미래 회차의 해답을 쓰지 않는다.
8. `remaining_episode_count`
   - `총 회차 수 - 대상 episode_no`.
9. `world_constraints`
   - Stage01~04·SourceLock·인간 시퀀스 경계 보호.
   - target episode 미래정보 누수 금지.
10. `target_refs`
   - 대상 회차 EpisodeArc와 CANONICAL THICK를 가리킨다.
   - Character Pressure가 없으면 `null`을 허용한다.
11. `source_hashes`
   - 최소 `baseline_artifact_sha256`.
   - EP02 이후 `previous_episode_arc_sha256`을 추가한다.

### Planning packet 크기 제약

PlannerInput은 전 DB 덤프가 아니다.
- `unresolved_payoffs`: 최대 24개 권장.
- `subplot_debt`: 최대 8개 권장.
- 같은 인물/관계의 중복 상태를 금지한다.

---

## 3. R8 RuntimeSceneProjection의 목적

R8은 새 의미를 쓰는 계층이 아니다.

> "현재 CANONICAL THICK의 시퀀스 정보를 Scene 하나를 쓰는 Writer가 즉시 소비할 수 있도록 펼친다."

### 필수 15개 top-level key

`schema, work_id, episode_no, scene_no, seq_id, characters, primary_pov, secondary_pov, character_states, relationship_states, event_context, info_context, plant_payoff_context, functional_propositions, source_refs`

### R8 생성 규칙

각 CANONICAL THICK sequence의 `member_scene_nos`마다 정확히 1개의 R8 record를 만든다.

- `characters` = 해당 sequence `cast[].character`
- `primary_pov`
  - `participation == PRIMARY` 중 첫 인물
  - 없으면 cast 첫 인물
- `secondary_pov` = 추가 PRIMARY 인물
- `character_states[].sequence_function` = THICK `cast[].desire_or_function` **그대로**
- `planning_boundary_state` = 같은 회차 R5의 동일 인물 state. 없으면 `null`.
- `relationship_states` = 같은 회차 R5의 planning boundary 관계 상태
- `event_context` = THICK `event` **그대로**
- `info_context` = 해당 `scene_no`가 `info_shift.scene_nos`에 포함된 항목만
- `plant_payoff_context` = 해당 `scene_no`가 `plant_payoff.scene_nos`에 포함된 항목만
- `functional_propositions` = 해당 scene의 THICK `scene_notes.functional_propositions` **그대로**
- `source_refs` = scene note evidence + sequence evidence를 deduplicate한 투영

R8에서 별도 사건·감정·정보를 새로 발명하지 않는다.

---

## 4. Provenance 규칙

### R5
R5는 선행 상태 packet이므로 의미 출처는:
- 직전 EpisodeArc
- 직전 CharacterArc
- 직전 RelationshipArc
- 직전 회차까지의 CANONICAL THICK thread history

### R8
R8은 현재 THICK 파생물이므로:
- `event_context == THICK.event`
- `sequence_function == THICK.cast.desire_or_function`
- `info_context`와 `plant_payoff_context`는 scene membership filter 결과
- `functional_propositions == THICK.scene_notes.functional_propositions`
- `source_refs`는 CANONICAL THICK evidence를 보존

따라서 R8의 provenance 핵심은 **THICK revision hash와 정확한 scene coverage**이다.

---

## 5. Invalidation / 재생성 규칙

다음 중 하나가 바뀌면 해당 작품 R5/R8을 현재값으로 간주하지 않는다.

- EpisodeArc revision
- CharacterArc / RelationshipArc revision
- THICK `plant_payoff` thread history
- CANONICAL THICK file hash
- sequence membership
- SceneCard membership

특히 THICK가 바뀌었는데 옛 R8이 남아 있으면 **STALE_RUNTIME**이다. 활성 경로에서 사용해서는 안 된다.

권장 상태:
- `CANONICAL_DERIVED_RUNTIME`: 현재 authority와 hash가 일치
- `REGEN_REQUIRED`: 상위 revision 변경
- `HISTORY_SUPERSEDED`: 보존용 구형 파생물

---

## 6. 검증 게이트

작품 완료는 파일 생성만으로 선언하지 않는다.

### R5 gate
- 회차 파일 수 == 작품 회차 수
- EP01 선행 상태 비어 있음
- EP02+ `source_episode == episode_no - 1`
- `through_episode / available_through_episode <= episode_no - 1`
- 미래 회차 사실 역류 없음(생성 input trace로 증명)
- 인물 중복 0 / 관계쌍 중복 0
- 장기 작품에서 debt 배열이 시즌 내내 빈 상태이면 FAIL/REVIEW

### R8 gate
- Runtime record 수 == SceneCard record 수
- SceneCard scene_no가 정확히 1회씩 존재
- `seq_id`가 해당 scene을 포함한 CANONICAL THICK와 일치
- event/cast/info/payoff/proposition parity mismatch 0
- source ref 누락 0

### Integration gate
- 기존 Stage01~04 byte 변경 0
- 기존 CANONICAL THICK byte 변경 0
- 비대상 Planner/Runtime byte 변경 0
- ZIP test PASS
- fresh extraction 후 validator 재실행 PASS

---

## 7. 새 작품 추가 시 실행 순서

1. 현재 authority pointer와 DB SHA 확인
2. 작품 SourceLock / Stage01~04 / CANONICAL THICK 확인
3. THICK가 아직 후보면 먼저 THICK 정본화
4. R5 생성
   - 회차별 직전 boundary state
   - open thread
   - debt 실채움
5. R5 미래정보 누수 검사
6. R8 deterministic projection 생성
7. SceneCard 1:1 coverage 검사
8. THICK↔R8 field parity 검사
9. 작품 manifest / work_state 갱신
10. DB append/replace
11. non-target immutability 검사
12. fresh extraction 재검증
13. `FRESH_EXTRACT_PASS` 후 완료 선언

---

## 8. 새 세션에서 절대로 하면 안 되는 것

- R5를 대상 회차 요약으로 만들지 않는다.
- 미래 회차에서 알게 된 사실을 N화 PlannerInput에 넣지 않는다.
- debt를 빈 배열로 두고 형식 PASS만 선언하지 않는다.
- R8을 독립 저작층으로 평가하지 않는다.
- R8에서 THICK에 없는 의미를 새로 생성하지 않는다.
- THICK 수정 뒤 기존 R8을 그대로 활성 유지하지 않는다.
- Stage01~04나 인간 sequence boundary를 R5/R8 때문에 수정하지 않는다.

---

## 9. 2026-08-11 현재 적용 대상

기존 12작 CANONICAL 중 R5/R8이 없던 6작:
- 경성스캔들
- 결혼못하는남자
- 공주가돌아왔다
- 강남엄마따라잡기
- 개와늑대의시간
- 궁

이번 보강 뒤 12작 모두 R5/R8 활성 coverage를 갖도록 한다.

## 10. 휴대형 참조 도구
- `tools/build_planner_runtime_reference.py`: CANONICAL 입력에서 R5/R8 staging 파일을 만드는 결정론적 참조 생성기. 의미 권위를 수정하지 않는다.
- `tools/validate_planner_runtime.py`: V1.1 schema, future leak, debt, R8↔THICK parity, scene coverage를 검사한다.

새 작품은 builder → validator → integration → fresh extraction 순서를 지킨다.

## 11. Baseline artifact SHA 규칙

- 현재 12작 `CANONICAL_THICK_BASELINE_ARTIFACT_SHA256`: `45d049d659a5ebe9079642c1bc093078677b3857d0036c5c8a58d9b4e29500ac`
- reference builder의 `--baseline-sha256`에는 위 **상위 CANONICAL THICK 기준 artifact SHA**를 넣는다.
- Planner/Runtime을 포함해 새로 만든 파생 DB ZIP의 SHA를 넣지 않는다.
- 이유: R5 `source_hashes.baseline_artifact_sha256`은 상위 의미 권위를 식별하는 provenance이며, 파생 패키지 자체를 식별하는 값이 아니다.
