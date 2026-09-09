# CURRENT HANDOFF POINTER
Last updated: 2026-09-10

## Current physical package authority
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R2__I4I_R2_CLOSED_PRIMARY_FAIL`

Current authority document:
`handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`

Current physical/research closure:
`handoff/20260910/P07_I4I_R2_FRESH_REPLICATION_CLOSURE_AND_PHYSICAL_SYNC_R2_20260910.md`

R2 closure commit:
`59ab0877c58ccaa367dac31f04371fee6dc03bae`.

Full logical 5-Part / 9-transport material SHA256:
`6e630bf4039953bd7b9969735c87fe7f273e760aa0811ee6c0322c2ea74b3b84`.

## Active engine / DB / fixed governance
- Active Development Engine: `P07-I4H Recovery R3`.
- Combined active C2: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.
- DB Authority: DB59 frozen `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- Production: `ENG:R47`.
- Formal scored count: `137`.
- Latest formal: `R138`.
- R140: `0/0/0`.
- Post-R2 active-engine regression: `258/258 PASS`.

## Closed whole-episode studies
### I4I R1
`CLOSED__PRIMARY_GATE_FAIL__POSITIVE_SCENE_LEVEL_SIGNAL__NO_PROMOTION`
- delta +0.2833333333333332 vs preregistered +0.30.

### I4I R2 Fresh Replication
`CLOSED__PRIMARY_GATE_FAIL__FRESH_REPLICATION_POSITIVE_NONHARMFUL_SIGNAL__NO_PROMOTION`
- delta +0.16666666666666607 vs preregistered +0.30;
- 12/12 axes nonloss;
- harmful intervention 0%;
- Control 35,738 chars / Treatment 37,939 chars;
- ABSTAIN 29 / LOW 12 / STANDARD 9.

R1/R2 remain separate FAIL results and must never be retroactively pooled or relabeled as PASS.

## Experiment recovery
Read:
- `P07_EXPERIMENT_RECOVERY_INDEX_R1_20260910.json`
- `P07_EXPERIMENT_RECOVERY_INDEX_R1_20260910.md`

Completed-experiment recovery chain:
Preregistration -> Frozen Inputs -> Control/Seal -> Selector/Profile Freeze -> Treatment/Integrity -> Provider/Runtime Receipts if claimed -> Blind Map Hash -> Blind Scores -> Unblind -> Final Result -> Post Regression -> Package Impact -> Changed Physical Packages.

## Active next research: P07-I4J
Knowledge-only endpoint/coverage audit:
- prereg: `handoff/20260910/P07_I4J_ENDPOINT_COVERAGE_AUDIT_PREREG_R1_20260910.json`
- prereg commit: `a5a861fbb0f7d66716cf1d84c8d07cb1ae6612cd`
- result: `handoff/20260910/P07_I4J_ENDPOINT_COVERAGE_AUDIT_RESULT_R1_20260910.json`
- result commit: `008b4e0681ff7068faf2cba63352d0512d658d99`
- verdict: `ENDPOINT_MISALIGNMENT_SIGNAL_CONFIRMED__COVERAGE_ALONE_INSUFFICIENT__FRESH_VALIDATION_REQUIRED`.

Prospective fresh validation:
- prereg: `handoff/20260910/P07_I4J_FRESH_COVERAGE_ENDPOINT_VALIDATION_PREREG_R1_20260910.json`
- prereg commit: `364e92c38772e6c78b1585b40eb6dc769eaebec9`
- status: `PREREGISTERED__FRESH_PLAN_0__CONTROL_0__SELECTOR_0__REVISION_POOL_0__ARM_SCORES_0`.

Current runtime execution is externally blocked by repeated `TransportTimeoutError`, including minimal `/bin/true`; do not manufacture fresh I4J outputs while runtime preflight fails.

## Other research states
- Semantic Alignment Virtual R1 remains Live-confirmation-pending and not active.
- DB64/9-Contract remains HOLD; DB59 stays authority.

## New-session read order
1. `handoff/CURRENT_HANDOFF_POINTER.md`
2. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
3. `handoff/20260910/P07_I4I_R2_FRESH_REPLICATION_CLOSURE_AND_PHYSICAL_SYNC_R2_20260910.md`
4. `handoff/20260910/P07_I4J_ENDPOINT_COVERAGE_AUDIT_RESULT_R1_20260910.json`
5. `handoff/20260910/P07_I4J_FRESH_COVERAGE_ENDPOINT_VALIDATION_PREREG_R1_20260910.json`
6. `handoff/CURRENT_NEXT_RESEARCH_POINTER.md`
7. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`
8. `handoff/CURRENT_NEXT_RESEARCH_CANDIDATE.md`
9. `handoff/CURRENT_DATABASE_RESEARCH_POINTER.md`
10. `handoff/20260909/START_HERE_P07_I4H_RECOVERY_R3_PHYSICAL_AUTHORITY_R1.md`

## STATUS TOKEN
`HANDOFF_R2_RESEARCH_SYNC__ACTIVE_I4H_RECOVERY_R3__DB59_FROZEN__I4I_R1_FAIL_0_2833__I4I_R2_FAIL_0_1667__I4J_AUDIT_ENDPOINT_MISALIGNMENT_SIGNAL__I4J_FRESH_PREREG_OUTPUTS_0__RUNTIME_TRANSPORT_TIMEOUT_BLOCK__FORMAL_137__R140_0_0_0`
