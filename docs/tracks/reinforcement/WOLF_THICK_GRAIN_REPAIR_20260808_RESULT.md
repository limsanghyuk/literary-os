# 개와늑대의시간 Thick Sequence 보강 결과 — 2026-08-08

Status: `GRAIN_REPAIR_FRESH_EXTRACT_PASS_MERGE_READY_NOT_COUNTED_COMPLETE`  
Lane: `가`  
Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1` + `DB98_THICK_SEQUENCE_GRAIN_QUALITY_CORRECTION_V1_0_1`

## 1. 실행 원칙

`EP01-level semantic authorship × every episode; up to 8 episodes only as management / strong-audit blocks.`

Blocks:
- EP01–08
- EP09–16

16회 모두 원문 전체 독해, 기존 인간 시퀀스 경계 확인, Thick 재저작, R5/R8 구성, 회차 light audit, 블록 strong audit 대상으로 처리했다. R8은 derived wiring이며 독립 의미저작으로 계상하지 않는다.

## 2. 정본 집계 교정

작업 초기 메모의 `145 sequences / 889 scenes`는 실제 정본 파일 합산과 불일치했다.

실제 정본은:
- episodes: 16
- human sequences: **143**
- canonical scenes: **880**

최종 Thick 결과도 정확히:
- Thick Sequence: `143 / 143`
- scene_notes: `880 / 880`
- R5 PlannerInput: `16 / 16`
- R8 RuntimeSceneProjection: `880 / 880`

## 3. 입도 / provenance / 연결 결과

- SOURCE `:Lx-Ly` provenance: **100%** (`2162 / 2162` source refs)
- complete six-key source hashes: **100%**
- exact schema/hash errors: **0**
- semantic exact duplicate classes: **0**
- normalized source verbatim 15-char hits: **0**
- grain distribution bad episodes: **0**
- multi-episode semantic threads: **10**

주요 장기 thread에는 `수현–지우 인연/재회`, `마오–지우 혈연`, `복수/잠입`, `수현–민기 형제 정체성 갈등`, `케이/수현 정체성`, `NIS 내부 균열` 등이 포함된다.

## 4. Core/SequenceBlueprint 문제 해결

### 4.1 Stage01 의미 불일치

EP16 S05에 strong mismatch가 확인됐다. 기존 Stage01 의미의 `수현이 폭발 장치를 심음`을 사용하지 않고 원문을 직접 재독해하여:

`마오가 준비한 미끼 USB가 NIS에서 폭발 → 마오가 케이의 배신을 확정 → 수현이 지우와 평범한 삶을 포기하고 마오에게 복귀`

로 source-grounded Thick을 재저작했다.

- raw-source override sequence: `개와늑대의시간_16_S05`
- core state: `CORE_SCENECARD_SEMANTIC_MISMATCH_DETECTED_NOT_MUTATED_UNDER_THICK_AUTHORITY`

Stage01 core는 Thick 권위로 수정하지 않았다.

### 4.2 SequenceBlueprint 의미 drift

여러 회차에서 SequenceBlueprint semantic fields가 원문과 크게 어긋나는 drift 신호가 확인되어, 해당 파일은 **boundary / member_scene_nos GT로만 사용**했다.

정책:
`BOUNDARY_ONLY_SEMANTIC_FIELDS_IGNORED_AFTER_SOURCE_DRIFT_DETECTION`

시퀀스 의미는 원문과 source-grounded evidence에서 다시 저작했다.

## 5. ZIP 인코딩 / 최종 검증 메타 문제 해결

1차 패키징 뒤 최종 checkpoint/manifest를 `zip -u`로 교체하는 과정에서 한글 경로 2개가 깨진 중복 엔트리로 생성되는 문제를 발견했다.

문제 패키지는 폐기하고 Python UTF-8 `zipfile`로 다음을 **처음부터 clean rebuild**했다.

- parent files: 32,878
- reinforcement files: 정확히 75
- final package files: **32,953**
- duplicate ZIP file entries: **0**
- garbled Unicode paths: **0**

또한 package 내부 `fresh_extract_validation.json`의 PASS1 참조를 최종 파일명으로 고쳤다. ZIP 자신의 SHA를 ZIP 내부 파일에 넣으면 자기참조가 되므로 실제 최종 SHA는 외부 seal 파일이 담당한다.

## 6. 최종 fresh extraction

Lane-local merge candidate:
`DB98_GA_LANE_GAEULDONGHWA_GANGNAMMOM_WOLF_THICK_MERGE_CANDIDATE_20260808.zip`

SHA-256:
`ad745699571ba01802ff4cd6caf4d5ca1c43fc5b7797d77599d5ab1e6e89c1f1`

Patch:
`WOLF_THICK_SEQUENCE_GRAIN_REINFORCED_20260808.zip`

SHA-256:
`5d6d28686e7d793ea6f23d76bd5d8a03566582fbb452fde2e161f654b3989882`

External final validation:
`WOLF_THICK_FINAL_FRESH_EXTRACTION_VALIDATION_20260808.json`

SHA-256:
`117ddc378d645c79b2bfcdf0cb181edb2e5ad58a8eea526dd26a7c29d9244e9f`

Final validation result:
- package files / fresh files: `32,953 / 32,953`
- missing: 0
- extra: 0
- changed after extraction: 0
- parent files verified: 32,878
- parent changed: 0
- parent missing: 0
- manifest artifact hashes: `74 / 74` match
- target structural/schema/hash errors: 0
- duplicate ZIP entries: 0
- garbled Unicode paths: 0

## 7. Accounting / parallel lane rule

물리적 상태는 `FRESH_EXTRACT_PASS`이고 `가` lane merge-ready다.

하지만 전역 `가을동화 5-field ablation` gate가 남아 있으므로:

`counted_complete = false`

또한 별도 `나` lane 세션이 병렬 작업 중이므로 전역 진행 포인터/글로벌 DB를 이 세션에서 덮어쓰지 않았다. 병합 시에는 **이 patch를 최신 reconciled global DB 위에 적용**해야 한다.
