# README FIRST — PlannerInput / Runtime 보강 개발자 패키지

이 폴더는 새 세션에서 과거 대화 기억 없이 PlannerInput(R5)과 RuntimeSceneProjection(R8)을 생성·검증하기 위한 실행 권위 묶음이다.

## 읽는 순서
1. **DB 기준 현재 권위:** `../../CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json`
2. **이 폴더 안내 포인터:** `CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json`
3. `PLANNER_RUNTIME_EXECUTION_AUTHORITY_V1_20260811.md`
4. `PLANNER_RUNTIME_SCHEMA_REGISTRY_V1.json`
5. `schemas/PLANNER_INPUT_CANONICAL_PROFILE_V1_1.schema.json`
6. `schemas/RUNTIME_SCENE_PROJECTION_V1.schema.json`
7. `PLANNER_RUNTIME_VALIDATION_CHECKLIST_V1.json`
8. `NEW_SESSION_PLANNER_RUNTIME_BOOTSTRAP_V1.md`
9. `DEVELOPER_HANDOFF_PLANNER_RUNTIME_NEW_WORK_V1_20260811.md`
10. 대상 작품의 CANONICAL THICK / Stage02~04 / SourceLock

## 한 문장 정의
- R5는 **N화를 만들기 직전 N-1까지 확정된 상태와 미해결 장기축을 전달하는 planning-boundary packet**이다.
- R8은 **현재 CANONICAL THICK를 Scene 하나가 소비할 수 있도록 펼친 deterministic projection**이다.

## 절대 규칙
- R5에 대상 회차나 미래 회차 사실을 선행 상태로 넣지 않는다.
- `unresolved_payoffs`, `subplot_debt`, `character_debt`를 관성적으로 빈 배열로 만들지 않는다. 실제 열린 축이 있으면 채운다.
- R8에서 새 의미를 저작하지 않는다. THICK와 exact parity를 유지한다.
- THICK/Arc/Scene membership이 바뀌면 기존 R5/R8을 현재값으로 사용하지 않는다.
- 완료 선언은 fresh extraction 후 portable validator PASS 뒤에만 한다.

## 참조 생성기
```bash
python tools/build_planner_runtime_reference.py --root <EXTRACTED_DB_ROOT> --work <작품명> --baseline-sha256 <CANONICAL_THICK_BASELINE_ARTIFACT_SHA256> --out <STAGING_DIR>
```
생성 후 바로 정본에 덮어쓰지 말고 staging에서 validator를 통과시킨다.

현재 12작 권위에서 `CANONICAL_THICK_BASELINE_ARTIFACT_SHA256`은:
`45d049d659a5ebe9079642c1bc093078677b3857d0036c5c8a58d9b4e29500ac`

이 값은 **R5/R8이 의존하는 12작 CANONICAL THICK 기준 artifact SHA256**이다. 새로 만들어진 Planner/Runtime 파생 DB ZIP의 SHA256을 넣지 않는다. 파생 ZIP SHA를 넣으면 동일 의미 데이터라도 source_hashes가 달라져 재현성 검증이 깨진다.

## 실행 검증
```bash
python tools/validate_planner_runtime.py --root <EXTRACTED_DB_ROOT> --work <작품명> --out validation.json
```
여러 작품은 `--work 작품1,작품2`, 전체 보유 작품은 `--work all`을 사용한다.

## 과거 결함에서 고정된 교훈
가을동화 초기 감사에서 R5의 세 debt 계층이 전 시즌 비어 있어 회차 간 carry-over가 실질적으로 작동하지 않는 문제가 확인되었다. 또한 R8은 R2/THICK를 장면으로 전개한 파생물이므로 독립 의미 저작층으로 계상하지 않는 것이 원칙이다. 이 패키지는 두 문제를 검증 규칙으로 고정한다.
