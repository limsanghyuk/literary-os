# Literary OS — P07 New Session Handoff R4 Recovery (2026-09-05)

## 0. Authority and recovery boundary(권위와 복구 경계)

이 문서는 R3 이후 새 세션에서 실제 제공 패키지를 다시 조사하고, R3가 인계한 누락 적용사항을 현재 CP0-era 물리 패키지에 복구한 결과를 기록하는 Session Transition Recovery Authority(세션 전환 복구 권위)이다.

R3의 과학적 상태·증거 경계·금지사항은 그대로 유지한다. 이번 복구는 제공되지 않은 과거 R30/R31 변경 패키지와 byte-identical(바이트 동일)하다고 주장하지 않는다. 대신 R3 계약 + 재조립 Research Master(연구 마스터) + 재조립 Engine Master(엔진 마스터) + 기존 실행체 원자료를 근거로 functional/authority recovery(기능·권위 복구)를 수행했다.

## 1. 전역 상태 — 변동 없음

- P06: COMPLETED / PHYSICALLY CLOSED(완료 / 물리 폐쇄).
- P07: ACTIVE PREFORMAL(예비시험 진행 중), NOT COMPLETE(미완료).
- Formal scored count(정식 채점 누계): 137.
- Latest formal scored experiment(최신 정식 채점 실험): R138.
- R140 formal attempt/output/score(정식 시도/산출/채점): 0/0/0.
- ENG:R47 Production(운영 엔진): immutable(불변).
- DB59 frozen reference SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- 기존 6개 개발작품은 DEVELOPMENT SET ONLY(개발 표본 전용), Formal R140 재사용 금지.

## 2. 이번 복구에서 실제 완료한 조사

### 2.1 Three-stage research lineage(3단계 연구계보)

Research Master를 다시 조립·검사하고 Stage 1/2/3 연결관계를 재감사했다.

- Stage 1 R001~R103 계보의 101-row Traceability(101행 추적성) 분류: ADOPTED 36 / CONDITIONAL 17 / NEGATIVE_GUARD 29 / METROLOGY_ONLY 10 / SUPERSEDED 9.
- 따라서 과거 실험을 1실험=1알고리즘으로 구현하지 않는다. 성공은 Runtime Module/Policy(실행 모듈·정책), 조건부는 Gate(관문), 실패는 Negative Guard(부정 관문), 계측 전용은 Metrology(계측), 후속 대체는 Historical Provenance(역사 계보)로 흡수한다.
- Stage 2 PRE-R104-AUX-001~068은 Formal count +0의 Non-formal Engineering/Metrology Layer(비정식 공학·계측층)로 유지한다.
- Stage 3 R104 이후는 Source-State -> Entity/Relationship/Thread -> Whole Story/Long Arc -> Episode Allocation -> Detailed Episode Synopsis -> Ensemble/Social Ecology -> Event/Plot-Axis Ownership -> THICK Sequence/Boundary -> Scene Contract -> Dialogue/Action/Subtext -> Surface Realization -> State Carry/Repair/Rollback의 종단간 계보다.

Historical Claim Boundary(역사 주장 경계)도 R3와 동일하게 유지한다: R129→R134 CONFLICTED_NOT_REPLICATED, R48 KNOWLEDGE_ONLY, R39 clean causal FAIL(방향성 신호만), R41 Ensemble effect reproduced/Tone add-on unsupported, R42 Blueprint Depth+Mismatch Harm reproduced/Thread Binding primary claim 미채택.

## 3. R-B Narrative Architecture Recovery(서사구조 복구)

R3 계약을 현재 실행체에 재구성했다.

- Social Ecology Graph(사회생태 그래프): groups/memberships/group relations/obligations/pressures/resources/information.
- Event/Plot-Axis Ownership(사건·플롯축 소유권): first-class runtime contract(1급 실행계약).
- Detailed Episode Synopsis(상세 회차 시놉시스): generic EPISODE_PLAN alias가 아닌 독립 LLM plan layer.
- THICK Sequence+Boundary: goal/obstacle/value_shift/turn_type/POV/cast_function/event-info-relationship-thread movements/entry-exit state/runtime share를 하류 소비.
- Consumer Fidelity(소비 충실도): Parent -> Child -> Renderer 실제 소비경로와 behavior hash/receipt를 검증.
- CP0에서 누락됐던 `tools/` 실행파일은 C2 내부 이전 sealed `CANDIDATE_SOURCE/tools`에서 원본 바이트를 복원했다. 새 파일을 발명하지 않았다.

Fresh recovery test: **7/7 PASS**.

R-B inherited authority status는 CLOSED를 유지한다.

## 4. R-C Decision Architecture Recovery(의사결정 구조 복구)

R3 계약을 현재 실행체에 재구성했다.

`LLM Candidate Portfolio` -> `LLM Plan Critic` -> `R82 Non-compensatory Safety Gate` -> `Primary/Backup Selection` -> `THICK Sequence downstream request`.

- Python이 event_family/responsibility/global_value를 창작적으로 결정하지 않는다.
- owner_axis_id / primary_group은 R-B 실제 ID를 참조해야 한다.
- exact PASS safety만 통과하며 UNKNOWN은 HOLD, FAIL은 BLOCK.
- responsibility hard floor는 다른 점수로 보상 불가.
- LLM critic 순위와 안전판정으로 Primary/Backup을 선택한다.
- Primary 선택이 실제 THICK request hash를 바꾸는지 검증했다.
- Decision Receipt는 raw safety + allowed-context hash를 결합한다.

Fresh recovery test: **15/15 PASS**.

R-C inherited authority status는 CLOSED를 유지한다.

## 5. R-D Long-Horizon Recovery(장기전개 복구) — ACTIVE / NOT CLOSED

R3가 남긴 ACTIVE checkpoint를 재구성하고 남아 있던 Referential Integrity(참조 무결성) 결함주입까지 실행했다.

- Canonical Carry: Character/Relationship/Thread + Group/Membership/Group Relation/Plot Axis.
- dangling Relationship/Membership/Group/Thread-Axis 참조는 fail-closed HOLD.
- canonical hash domain에서 last_state_hash/commit_hash/parent_state_hash 같은 자기참조 메타데이터를 제외.
- EP06 commit hash == EP07 parent hash 연속성 검사.
- CLOSED/FINAL Thread 무단 재개 BLOCK.
- Authorized Novelty는 role gap + grounding/temporal/role-gap-match/identity-noncollision exact PASS에서만 허용하고 Character/Entity/Membership/Thread/Relationship에 atomic registration(원자 등록).
- Narrative-State Snapshot/Rollback은 Production Authority rollback과 분리하고 exact resume를 검증.
- Controlled Replan은 Series Anchor와 R-C Primary Plan을 변경할 수 없다.
- rollback 뒤 동일 요청의 request hash가 clean-run과 동일함을 검증.
- Python literary prose generation bytes = 0 유지.

Fresh recovery test: **17/17 PASS**.
Current non-historical regression(현행 비역사 회귀): **160/160 PASS**.

그러나 R-D는 아직 CLOSED가 아니다. 아래 D1 물리 문제 때문에 R3가 요구한 최종 5-part/8-package Fresh Handoff Audit을 완료할 수 없다.

## 6. 현재 물리 패키지 복구

새 변경 패키지:

1. CONTROL R32 — `LITERARY_OS_MANDATORY_CONTINUATION_SET_CONTROL_R32_P07_R3_RECOVERY_RD_ACTIVE_AUTHORITY_20260905_SEALED.zip`
   - SHA256 `256f51df283f4bf5363df783dc8413f763095b65dac40acbaba5168ac0e3e84b`
   - Fresh Extraction PASS.
2. PART-A R31 — `LITERARY_OS_MANDATORY_CONTINUATION_PART-A_CONTROL_AND_EXPERIMENT_R31_P07_R3_RECOVERY_RD_ACTIVE_20260905_SEALED.zip`
   - SHA256 `af6ed083c22cc0ec16f8db985672d98e46cff55ffb35a8d0fa4952cb749c8040`
   - Fresh Extraction PASS.
3. PART-B2 R32 — `LITERARY_OS_MANDATORY_CONTINUATION_PART-B2_RESEARCH_CURRENT_RECOVERY_VOL2_R32_P07_R3_RECOVERY_RD_ACTIVE_20260905_SEALED.zip`
   - SHA256 `216452ed230551453b25de6e82b3d1a86733d21cbaa3f6bd298309c63a28b644`
   - Fresh Extraction PASS.
4. PART-C2 R31 — `LITERARY_OS_MANDATORY_CONTINUATION_PART-C2_ENGINE_MASTER_VOL2_CANDIDATE_R31_P07_R3_RECOVERY_RD_ACTIVE_20260905_SEALED.zip`
   - SHA256 `b594d90a398b43760595dd3ae523723c1469af565a8ba283792b0a89bb0ea240`
   - Fresh Extraction PASS.

Byte-unchanged(바이트 불변) 확인:

- B1 R10 SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98` — Fresh Extraction PASS.
- C1 R10 SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518` — Fresh Extraction PASS.
- D2 R10 SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4` — Fresh Extraction PASS.

## 7. D1 upload truncation incident(업로드 절단 사건)

R3가 요구하는 D1 R10 정본은:

- expected bytes: 138,011,573
- expected SHA256: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`

이번 새 세션에 실제 마운트된 업로드는:

- actual bytes: 132,644,864
- actual SHA256: `31a28645a2fca5004f475b1a74b4e5f2a366f0762374c60ac0910e905dd0059f`
- ZIP central directory 없음 / BadZipFile
- `20_SPLIT_VOLUMES/DB59_AUTHORITY_METADATA_REPAIRED_FULL.zip.part001` 내부에서 중단.

따라서 이 사건은 `PHYSICAL_UPLOAD_TRUNCATION__NOT_RESEARCH_OR_ENGINE_FAILURE`로 분류한다. 잘린 D1을 정본으로 사용하거나 새 해시를 권위로 승격하지 않는다.

## 8. Evidence boundary(증거 경계)

`Concept Application` ≠ `Virtual/Local Engine Rehearsal` ≠ `Live Provider Engine Execution` ≠ `Formal Controlled Evaluation`.

이번 7/7, 15/15, 17/17, 160/160은 Local/Engineering Evidence(로컬·공학 증거)이다. Provider Receipt가 없으므로 Live API Evidence 또는 Formal R140 evidence가 아니다.

## 9. Container failure boundary(컨테이너 오류 경계)

이번 복구 시작 직후 최소 Container/Python 호출에서 ClientError가 다시 나타났다가, 이후 최소 health check에서 `backend_alive` / `python_ok`로 회복했다. 이후 작업은 작은 독립 실행 단위로 수행했다.

분류: `INTERMITTENT_INFRASTRUCTURE_FAILURE__ENGINE_FAILURE_NOT_ESTABLISHED`.

ClientError가 재발하면 새 experiment/closure/seal을 실패로 기록하지 말고 마지막 검증 checkpoint에서 재개한다.

## 10. 정확한 다음 행동

현재 7/8 패키지는 fresh-validated 상태다. 정확한 D1 R10 바이트를 복구한 뒤:

1. D1 outer SHA/CRC/Fresh Extraction.
2. D1+D2 DB59 full reassembly 및 DB59 frozen SHA 재확인.
3. 전체 8-package Currentness/CRC/JSON/Python/nested archive/Fresh Handoff Audit.
4. 그 전체 감사가 PASS한 뒤에만 R-D Physical Closure 여부를 판정.
5. R-D가 완전 폐쇄된 뒤 R-E -> R-F Live Provider Parity -> R-G Freeze -> Fresh Formal Sample -> Revised R140 Preregistration -> New G0 -> Formal R140.

R-D 완료 전 R-E/R-F/Formal R140으로 건너뛰지 않는다.
