# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-10

## FIRST READ
1. `handoff/20260910/P07_I4K2P_R2_RESEARCH_SYNC_R8_PHYSICAL_CLOSURE_R1_20260910.md`
2. `handoff/20260910/P07_I4K2P_R2_FIELD_BUDGET_HOLD_CLOSURE_R1_20260910.md`
3. `handoff/20260910/P07_I4K2P_RESEARCH_SYNC_R7_PHYSICAL_CLOSURE_R1_20260910.md`
4. `handoff/20260910/P07_I4K2R_RESEARCH_SYNC_R6_PHYSICAL_CLOSURE_R1_20260910.md`
5. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
6. `handoff/CURRENT_NEXT_RESEARCH_POINTER.md`

## CURRENT DURABLE STATE
Physical research-sync authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R8__I4K2P_R2_HOLD_FIELD_BUDGET`.
Nine-file material SHA256: `cb866ec47c94c4fcc508250ca89e8b3b6a047ee79ae9815bd1a100981707f864`.
Active engine `P07-I4H Recovery R3`; combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Production `ENG:R47`; Formal `137`; latest `R138`; R140 `0/0/0`.

## I4K-2P R2 RECOVERY FACTS
Experiment: `P07-I4K-2P-R2-FIELD-BUDGETED-PROPAGATION-REPLICATION`.
Preregistration commit: `34ef87d75ea7974c67c8487b8c34a9a7d33d283b`; GitHub prereg is Primary Evidence; outputs-before-execution 0.
Arms: Baseline 12 / Propagation 12.
Prescore result: Baseline field-budget violation 12/12; future_carry below minimum 12/12; second_order below minimum 10/12; coincidence_guard above max 1/12. Treatment field budgets 12/12 PASS. Total mean representation gap 0.056506 <=0.08.
Candidates were not edited. Mask 0 / scores 0 / unblind 0 / H1-H4 verdict 0.
Final classification: `HOLD__BASELINE_FIELD_LEVEL_BUDGET_MISS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`.

Root cause: field-budget instructions existed but there was no fail-closed pre-emission admission stage.

## PHYSICAL SYNC R8
CONTROL/A/B2 changed only; parent-entry mismatch 0; 16 new evidence entries each; CRC/path safety PASS; other six transports byte-identical from R7; C2/DB59 reassembly PASS.

## MANDATORY RESUME ORDER
1. minimal process / filesystem / cgroup-OOM / small archive preflight;
2. verify Sync R8 material SHA;
3. do not edit or score R1/R2 HOLD candidates;
4. preregister fresh `P07-I4K-2P-R3-PREEMISSION-BUDGET-GATED-PROPAGATION-REPLICATION` before any final candidate output;
5. freeze provisional-draft semantics, deterministic admission gate, field and pair budgets, max attempts, attempt receipts, and unchanged effect gates;
6. execute only after prereg seal;
7. if valid, mask → score seal → unblind → H1-H4;
8. only a full PASS may authorize I4K-3 preregistration;
9. regression/package impact/full physical sync after meaningful research.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R8_CB866EC4__ACTIVE_I4H_R3__I4K2P_R2_HOLD_FIELD_BUDGET__R3_PREEMISSION_ADMISSION_NEXT__NO_I4K3__DB59__PRODUCTION_R47__FORMAL_137__R140_0_0_0`