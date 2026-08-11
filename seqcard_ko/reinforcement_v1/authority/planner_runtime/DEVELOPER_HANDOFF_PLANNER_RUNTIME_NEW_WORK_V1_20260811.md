# 개발자 핸드오프 — PlannerInput(R5) / RuntimeSceneProjection(R8) 새 작품 보강 실행서 V1

상태: **ACTIVE_DEVELOPER_HANDOFF**  
대상: 새 대화창 / 새 작품 / 기존 THICK 정본 작품의 R5·R8 보강

## 1. 이 문서만으로 알아야 할 핵심

PlannerInput(R5)과 RuntimeSceneProjection(R8)은 Stage01~04나 THICK를 대체하는 새 정본이 아니다. 둘은 Literary OS가 정본 데이터를 **기획과 장면 창작 시점에 소비하기 위한 실행 파생 계층**이다.

- **R5 PlannerInput**: N화를 설계하기 직전, N-1화까지 확정된 상태·관계·열린 장기축·미해결 부담을 전달한다.
- **R8 RuntimeSceneProjection**: 현재 CANONICAL THICK를 Scene 하나가 바로 소비할 수 있도록 장면 단위로 펼친다.

권위 순서:
`원본/SourceLock → Stage01 → Stage02 → Stage03 → Stage04 → CANONICAL THICK → R5 → R8`

R5/R8은 **DERIVED EXECUTION CONTRACT**이며 상위 의미층을 수정할 권한이 없다.

## 2. 새 세션 필독 순서

1. `seqcard_ko/reinforcement_v1/CURRENT_THICK_AUTHORITY_POINTER.json`
2. `seqcard_ko/reinforcement_v1/CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json`
3. `seqcard_ko/reinforcement_v1/authority/planner_runtime/README_FIRST.md`
4. `.../PLANNER_RUNTIME_EXECUTION_AUTHORITY_V1_20260811.md`
5. `.../PLANNER_RUNTIME_SCHEMA_REGISTRY_V1.json`
6. `.../schemas/PLANNER_INPUT_CANONICAL_PROFILE_V1_1.schema.json`
7. `.../schemas/RUNTIME_SCENE_PROJECTION_V1.schema.json`
8. `.../PLANNER_RUNTIME_VALIDATION_CHECKLIST_V1.json`
9. 대상 작품의 CANONICAL THICK / EpisodeArc / CharacterArc / RelationshipArc / SourceLock
10. 중단 재개라면 대상 작품 `work_state.json`과 기존 R5/R8 hash

과거 대화의 기억이나 임시 보고서보다 현재 pointer/manifest를 우선한다.

## 3. R5 정의와 작성 규칙

### 목적
질문은 하나다.
**“N화를 설계하기 직전, 작가가 반드시 기억해야 하는 N-1까지의 현재 상태와 아직 해결되지 않은 부담은 무엇인가?”**

### 정확한 14키
`schema, work_id, episode_no, previous_exit_state, character_states, relationship_states, unresolved_payoffs, active_causal_threads, remaining_episode_count, subplot_debt, character_debt, world_constraints, target_refs, source_hashes`

### EP01
선행 회차가 없으므로 `previous_exit_state=null`, 상태/관계/thread/debt 배열은 빈다.

### EP02+
- `previous_exit_state`: 직전 EpisodeArc만 사용.
- `character_states`: 직전 CharacterArc의 인물별 최종 1개 상태.
- `relationship_states`: 직전 RelationshipArc의 관계쌍별 최종 1개 상태.
- `unresolved_payoffs`: **직전 회차까지 실제 THICK에 등장한 thread history만** 사용. 마지막 상태가 PAYOFF면 닫는다.
- `active_causal_threads`: planning boundary에서 살아 있는 thread.
- `subplot_debt`: 실제 열린 thread가 있으면 그중 중요한 것을 미해결 부담으로 기록한다. 관성적으로 빈 배열 금지.
- `character_debt`: 직전 인물 상태가 아직 어떤 선택으로 귀결될지 미결임을 기록한다. 미래 답을 쓰지 않는다.
- 미래 회차의 statement·사건·결말을 읽어 현재 PlannerInput에 넣지 않는다.

### 권장 bounded context
- unresolved thread ≤ 24
- subplot debt ≤ 8
- 인물/관계 동일 키 중복 0

## 4. R8 정의와 생성 규칙

R8은 독립 저작이 아니다. **CANONICAL THICK + 같은 회차 R5를 장면별로 deterministic projection**한다.

### 정확한 15키
`schema, work_id, episode_no, scene_no, seq_id, characters, primary_pov, secondary_pov, character_states, relationship_states, event_context, info_context, plant_payoff_context, functional_propositions, source_refs`

### parity 규칙
- SceneCard 1장면당 R8 정확히 1레코드.
- `event_context == THICK.event`
- `sequence_function == THICK.cast.desire_or_function`
- info/payoff는 해당 `scene_no`가 item의 `scene_nos`에 포함될 때만 투영.
- functional propositions는 해당 scene의 THICK scene_notes와 exact match.
- source refs는 THICK evidence를 보존.
- R8에서 사건·감정·정보를 새로 쓰지 않는다.

## 5. 새 작품 작업 절차

1. 현재 THICK authority와 대상 작품 상태 확인.
2. 대상 작품 THICK가 CANONICAL이 아니면 먼저 THICK를 정본화.
3. SourceLock/Stage01~04/THICK hash를 동결.
4. 회차 순서대로 R5 생성.
5. R5 future-leak 검사.
6. 실제 open thread/debt carry-over 검사.
7. 같은 회차 R5 + CANONICAL THICK로 R8 생성.
8. SceneCard 1:1 coverage 검사.
9. R8↔THICK exact parity 검사.
10. 작품 manifest/work_state 갱신.
11. DB에 append/replace.
12. 비대상 Stage01~04/THICK/기존 실행층 불변 검사.
13. ZIP 생성.
14. 별도 디렉터리 fresh extraction.
15. portable validator 재실행.
16. `FRESH_EXTRACTION_PASS` 뒤에만 완료 선언.

## 6. 자동화가 해도 되는 것 / 안 되는 것

### 허용
- 직전 Arc 상태 추출
- 현재 boundary까지 thread history 계산
- 해시/참조/정렬/직렬화
- R8 deterministic projection
- schema/parity/future-leak 검사

### 금지
- Python이 새로운 극적 사건, 감정, 관계 의미를 발명
- 미래 회차 사실을 현재 R5에 역류
- debt를 전 시즌 빈 배열로 두고 PASS 선언
- R8을 독립 의미 저작 성과로 계상
- THICK 변경 후 구형 R8을 활성 유지
- R5/R8 때문에 Stage01~04나 인간 Sequence 경계를 변경

## 7. 무효화 규칙

다음이 변경되면 R5/R8은 현재값이 아니다.
- EpisodeArc
- CharacterArc / RelationshipArc
- CANONICAL THICK / plant_payoff thread history
- SceneCard 또는 sequence membership

상태는 `REGEN_REQUIRED`로 내리고 재생성한다. 구형 파일은 history/quarantine으로 보존한다.

## 8. 검증 명령

```bash
python seqcard_ko/reinforcement_v1/authority/planner_runtime/tools/validate_planner_runtime.py \
  --root <EXTRACTED_DB_ROOT> \
  --work <작품명> \
  --require-v1-1 \
  --out planner_runtime_validation.json
```

새 작품과 재보강 작품은 반드시 `--require-v1-1`을 사용한다.

## 9. 완료 기준

- R5 episode file 수 = 작품 회차 수
- R8 episode file 수 = 작품 회차 수
- R8 scene records = SceneCard scenes
- future-leak errors = 0
- duplicate character/relation boundary state = 0
- 실제 열린 장기축이 있는데 debt가 비어 있는 회차 = 0
- R8 THICK parity mismatch = 0
- source refs empty = 0
- Stage01~04 변경 = 0
- THICK 변경 = 0
- non-target 변경 = 0
- fresh extraction validator = PASS

## 10. 2026-08-11 정리 결과

처음 R5/R8이 없던 6작: 경성스캔들, 결혼못하는남자, 공주가돌아왔다, 강남엄마따라잡기, 개와늑대의시간, 궁.

전수 검사 중 기존 보유작 가운데 가을동화·101번째프로포즈·난폭한로맨스·내여자친구는구미호의 legacy R5가 단일 V1.1 계약과 맞지 않거나 과거 debt 결함을 포함한 것을 확인해 현재 CANONICAL THICK에서 재생성했다. 내이름은김삼순·너의목소리가들려는 이미 V1.1 엄격 검사를 통과하여 기존 바이트를 보존했다.

최종적으로 12작 모두 PlannerInput Canonical Profile V1.1 + RuntimeSceneProjection V1 엄격 검사를 통과한다.

## 11. 새 대화창에 줄 최소 지시문

> 현재 DB의 `CURRENT_THICK_AUTHORITY_POINTER.json`과 `CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json`을 먼저 읽고, `authority/planner_runtime/README_FIRST.md` 및 실행 권위·스키마·검증 체크리스트를 필독하라. 대상 작품의 CANONICAL THICK와 Stage02~04/SourceLock을 확인한 뒤 PlannerInput V1.1을 회차 경계 기준으로 만들고 미래정보 누수를 금지하라. 이후 RuntimeSceneProjection V1을 THICK에서 결정론적으로 생성하고 exact parity를 검사하라. Stage01~04와 THICK는 수정하지 마라. fresh extraction validator가 PASS하기 전에는 완료 또는 정본 편입을 선언하지 마라.
