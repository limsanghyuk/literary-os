# NEW SESSION BOOTSTRAP — PlannerInput(R5) / RuntimeSceneProjection(R8)

새 대화창은 과거 대화 기억을 추측하지 말고 아래 순서로 시작한다.

## 필독 순서
1. `seqcard_ko/reinforcement_v1/CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json` (DB 현재 권위)
2. `seqcard_ko/reinforcement_v1/authority/planner_runtime/CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json` (가이드 포인터)
3. `PLANNER_RUNTIME_EXECUTION_AUTHORITY_V1_20260811.md`
4. `schemas/PLANNER_INPUT_CANONICAL_PROFILE_V1_1.schema.json`
5. `schemas/RUNTIME_SCENE_PROJECTION_V1.schema.json`
6. `PLANNER_RUNTIME_VALIDATION_CHECKLIST_V1.json`
7. 작품의 `reinforcement_v1/manifests/{work}/reinforcement_manifest.json`
7. 작품의 CANONICAL THICK / EpisodeArc / CharacterArc / RelationshipArc / SourceLock

## 작업 개시 조건
- 대상 작품 THICK가 CANONICAL 또는 명시된 승인 상태
- SourceLock 접근 가능
- Stage01~04 경계와 current THICK hash 확인
- 기존 R5/R8이 있으면 current authority hash와 일치하는지 먼저 확인

## 작업 명령
대상 작품에 대해 회차 순서대로 R5를 만들고, 같은 회차 CANONICAL THICK를 장면별 R8로 결정론적 투영하라. R5에는 직전 회차까지의 상태만 허용하고 대상/미래 회차 사실을 넣지 마라. `unresolved_payoffs`, `subplot_debt`, `character_debt`를 실제 열린 장기축에 근거해 채워라. R8에서는 새 의미를 저작하지 말고 THICK의 cast/event/info/payoff/scene_notes와 evidence를 그대로 scene-level로 투영하라.

## 완료 조건
- R5 회차 수 = 작품 회차 수
- R8 scene 수 = SceneCard scene 수
- R5 future-leak structural errors = 0
- R8 THICK parity mismatches = 0
- existing Stage01~04 / THICK 변경 = 0
- fresh extraction validator = PASS

## 재개
중단 시 `work_state.json`과 생성된 episode hash를 읽고 마지막 PASS 회차 다음부터 재개한다. 이미 검증된 회차를 의미 변경 없이 다시 생성하지 않는다.

## 실행 도구 확인
- 생성기: `tools/build_planner_runtime_reference.py`
- 검증기: `tools/validate_planner_runtime.py`
- 개발자 상세 핸드오프: `DEVELOPER_HANDOFF_PLANNER_RUNTIME_NEW_WORK_V1_20260811.md`
- 현재 상위 CANONICAL THICK baseline artifact SHA256: `45d049d659a5ebe9079642c1bc093078677b3857d0036c5c8a58d9b4e29500ac`
