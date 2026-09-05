# Authority Document Map and Handoff Index R1

## 목적

새 세션이 서로 다른 시점의 Authority(권위), Research Delta(연구 후속변경), Engine Delta(엔진 후속변경)를 혼동하지 않도록 읽기 순서와 우선순위를 고정한다.

## Authority 계층

### 1. Production Authority(운영 권위)
- ENG:R47 Production.
- PART-C1 R10.
- 이 세션에서 변경 금지 / 불변.

### 2. Data Authority for revised R140 preparation(수정 R140 준비 데이터 권위)
- DB59 frozen reference snapshot.
- SHA256 a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9.
- PART-D1/D2 physical authority bytes unchanged.
- P06 malformed 3,329 delta는 격리.
- DB successor는 별도 검증 전 R140 authority 아님.

### 3. Last Reported Physical Continuation Authority(마지막 보고 물리 연속 권위)
- CONTROL R27
- A R26
- B1 R10
- B2 R27
- C1 R10
- C2 R26
- D1 R10
- D2 R10

주의: 세션 말미 backend incident로 이번 응답에서는 이 물리 파일을 다시 열어 SHA/CRC를 재검증하지 못했다. 06_LAST_REPORTED_PHYSICAL_8_PACKAGE_SET_R1.json의 값을 recovery locator로 사용하고, 새 세션에서 반드시 실제 재검증한다.

### 4. Current Session Authority Delta(현재 세션 권위 후속변경)
이 GitHub handoff branch의 문서들.

이 Delta는 기존 physical ZIP을 대체하지 않는다. Backend 복구 후 CONTROL/A/B2/C2 새 revision에 물리 편입해야 한다.

## 새 세션 필독 순서

1. 00_NEW_SESSION_START_HERE_R21.md
2. 06_LAST_REPORTED_PHYSICAL_8_PACKAGE_SET_R1.json
3. 01_CURRENT_AUTHORITY_AND_PACKAGE_DELTA_R1.json
4. 02_P07_PREFORMAL_RESEARCH_EXPERIMENT_SUMMARY_R1.md
5. 03_RB_NARRATIVE_ARCHITECTURE_CLOSURE_PREREG_DRAFT_R1.json
6. 04_BACKEND_INCIDENT_AND_RECOVERY_R1.md
7. 05_PHYSICAL_8_PACKAGE_RESEAL_PLAN_R1.json
8. 기존 물리 8패키지 실제 SHA/CRC 재검증
9. CONTROL/A/B2/C2 physical reseal
10. Fresh Handoff Audit PASS 후 R-B 실행

## 다음 연구/실험 상태

Formal scored count = 137.
R140 formal attempt/output/score = 0/0/0.

P07 current phase:
R-A historical component re-audit complete.
R-B Narrative Architecture Closure next.

R-B가 닫기 전 Live Craft Parity CP1 재개 금지.

## R-B에 반드시 포함할 서사구조

- Whole Story / Long Arc
- Episode Allocation
- Social Ecology Graph
- Group Membership + group-to-group relations/pressures
- Event Ownership / Plot-Axis Ownership
- Detailed Episode Synopsis
- THICK Sequence + Boundary
- Scene Plan / Scene Contract
- Consumer Fidelity at every lowering edge
- Bidirectional repair at minimum responsible ancestor

## 후속 단계

R-C Candidate Portfolio / Critic / R82 safety.
R-D long-horizon state carry / rollback / Authorized Novelty / EP06-08 probe.
R-E Character Voice / Subtext / Repetition-Template / Ordered Beats.
R-F live Reference-vs-Engine Craft Parity.
R-G freeze → fresh sample → revised R140 prereg/G0 → formal R140.

## 절대 경계

- Physical reseal이 완료되기 전 이 branch 자체를 8-package physical authority라고 부르지 않는다.
- ENG:R47와 DB59 frozen R140 bytes를 변경하지 않는다.
- Development-contaminated six works를 revised formal sample로 재사용하지 않는다.
- Python이 문학문장을 쓰거나 수정하지 않는다.
- Live provider 결과가 없는데 Scripted/Test Double을 craft parity로 승격하지 않는다.
- 실패/중단/수리 attempt를 삭제하지 않는다.
