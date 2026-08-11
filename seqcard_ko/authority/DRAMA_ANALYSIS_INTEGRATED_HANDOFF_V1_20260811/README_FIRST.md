# README FIRST — 한국 드라마 분석 새 세션 통합 실행 핸드오프 V1

문서 상태: **ACTIVE_NEW_SESSION_INTEGRATED_HANDOFF**  
작성일: **2026-08-11**  
목적: 과거 대화 기억 없이 새 세션이 **원본 대본 → Stage01~04 → CANONICAL THICK → PlannerInput(R5) → RuntimeSceneProjection(R8)** 순서로 바로 분석·저작·검증·통합할 수 있게 한다.

## 1. 이 묶음의 권위 경계

이 묶음은 기존 Stage01~04 정본을 대체하지 않는다.

- Stage01~04 의미 권위: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10`
- DB98 기존 강화 권위: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1` + active correction
- 2026-08-11 CANONICAL THICK 12작 overlay: `DB98_THICK_12WORK_CANONICAL_AUTHORITY_20260811`
- Planner/Runtime 파생 실행 권위: `DB98_PLANNER_RUNTIME_12WORK_CANONICAL_PROFILE_V1_1_AUTHORITY_20260811`

충돌 시 우선순위:

`원본/SourceLock → Stage01~04 V10 → 현재 작품의 CANONICAL THICK pointer/manifest → Planner/Runtime pointer → 이 통합 실행서`

이 문서는 **실행·인계 통합 문서**다. 기존 정본 스키마와 의미 권위를 임의 변경하지 않는다.

## 2. 새 세션 필독 순서

1. 허브 루트 `DRAMA_ANALYSIS_CURRENT_INTEGRATED_POINTER.json`
2. `seqcard_ko/authority/DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10/README.md`
3. `seqcard_ko/authority/DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10/DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10.md`
4. `seqcard_ko/authority/DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10/AUTHORITY_MANIFEST.json`
5. `seqcard_ko/authority/DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10/schemas/EXACT_SCHEMA_REGISTRY.json`
6. 허브 루트 `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
7. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/THICK_SEQUENCE_AUTHORING_AUTHORITY_V1.md`
8. `.../THICK_SEQUENCE_GRAIN_QUALITY_CORRECTION_V1_0_1.md`
9. `.../THICK_SEQUENCE_AUTHORING_EXECUTION_V1.md`
10. `seqcard_ko/reinforcement_v1/CURRENT_THICK_AUTHORITY_POINTER.json`
11. `seqcard_ko/reinforcement_v1/schemas/THICK_SEQUENCE_EXACT_SCHEMA_CONTRACT_V1_0_1_FINAL_20260811.json`
12. `seqcard_ko/reinforcement_v1/CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json`
13. `seqcard_ko/reinforcement_v1/authority/planner_runtime/README_FIRST.md`
14. 이 폴더의 `DRAMA_ANALYSIS_INTEGRATED_EXECUTION_V1_20260811.md`
15. 이 폴더의 `QUALITY_HOMOGENIZATION_PROVENANCE_AUDIT_V1_20260811.md`
16. 이 폴더의 `WORK_STATE_MANIFEST_SELFCHECK_CONTRACT_V1_20260811.md`
17. **대상 작품을 정한 뒤에만** 해당 SourceLock, source inventory, work_state, manifest, resume checkpoint를 읽는다.

## 3. 한 문장 실행 원칙

> **원본을 직접 읽어 의미를 저작하고, 기존 분석층은 구조·경계·검증·비교의 보조로 사용하며, 도구는 의미를 발명하지 않고 정확한 계약·출처·무결성을 검증한다.**

## 4. 완료를 선언할 수 있는 조건

`SOURCE_PASS + STAGE01_04_PASS + THICK_PASS + PROVENANCE_PASS + QUALITY_HOMOGENIZATION_PASS + R5_PASS + R8_PASS + MANIFEST_WORK_STATE_MATCH + NON_TARGET_IMMUTABILITY_PASS + FRESH_EXTRACTION_PASS`

하나라도 빠지면 `COMPLETE`가 아니다.

## 5. 현재 기준 앵커

- CANONICAL THICK baseline artifact SHA256: `45d049d659a5ebe9079642c1bc093078677b3857d0036c5c8a58d9b4e29500ac`
- Planner/Runtime repaired integrated DB SHA256: `26804e12178ca74ebb498ce478e3cd421ac4141be74bffd373d6ddf284d465f8`
- THICK 12작: 1,795 sequences / 12,979 SceneCards / exact schema errors 0 / provenance errors 0
- R5/R8 12작: 203 Planner episode files / 203 Runtime episode files / 12,979 Runtime scene records / errors 0 / warnings 0

## 6. 금지

- 원본을 읽기 전에 기존 대상 작품의 의미문을 복사해 새 의미를 만드는 것
- Python으로 SceneCard/Sequence/Arc/THICK 의미를 생성하는 것
- 구조 PASS를 의미 PASS로 간주하는 것
- 시퀀스·회차를 균등분할 공식으로 의미 설계하는 것
- THICK의 `event/cast/info/scene_notes`를 기존 필드 재기술로 채우는 것
- R5에 대상/미래 회차 사실을 넣는 것
- R8에서 THICK에 없는 새 의미를 저작하는 것
- THICK/Arc/Scene membership 변경 뒤 옛 R5/R8을 활성 유지하는 것
- user 승인 또는 active authority가 요구하는 승격 절차 없이 CANONICAL을 선언하는 것
