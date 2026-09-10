# CURRENT HANDOFF POINTER
Last updated: 2026-09-10

## READ FIRST
1. `handoff/20260910/P07_I4K2R_RESEARCH_SYNC_R6_PHYSICAL_CLOSURE_R1_20260910.md`
2. `handoff/20260910/P07_I4K2R_STATE_ATTACHMENT_REPLICATION_FAIL_CLOSURE_R1_20260910.md`
3. `handoff/20260910/P07_I4K2_RESEARCH_SYNC_R5_PHYSICAL_CLOSURE_R1_20260910.md`
4. `handoff/20260910/P07_I4K2_EXTERNAL_SEARCH_ABLATION_FAIL_CLOSURE_R1_20260910.md`
5. `handoff/20260910/P07_I4K1_RESEARCH_SYNC_R4_PHYSICAL_CLOSURE_R1_20260910.md`
6. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
7. `handoff/CURRENT_NEXT_RESEARCH_POINTER.md`
8. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`

## CURRENT PHYSICAL / ENGINE / DB AUTHORITY
Physical research-sync authority:
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R6__I4K2R_FAIL_H3_ENSEMBLE_FUTURE_MARGIN`

Full 5-Part / 9-transport material SHA256:
`9df7f7f6cc6e3c6790e98e168b6eb82a0c56bb8729280bcf9c2d95309675d216`

Active Development Engine remains `P07-I4H Recovery R3`.
Combined active C2 remains `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.
DB59 remains frozen `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
Production `ENG:R47`; Formal scored count `137`; latest formal `R138`; Formal R140 `0/0/0`.

## CURRENT RESEARCH STATE
- I4J J1: immutable preselector Control-scale HOLD.
- I4K-0: Exit Gate PASS.
- I4K-1: PASS_TO_I4K2.
- I4K-2: FAIL H2 because External-only causal-fit degradation; immutable.
- I4K-2R State-Attachment fresh replication: `FAIL__H3_ENSEMBLE_FUTURE_MARGIN_BELOW_PREREG_THRESHOLD__NO_I4K3_ENTRY`.
  - Prescore integrity PASS; representation parity PASS; State Attachment Contract 16/16 PASS; hard gates 0.
  - INTERNAL_ONLY all-7 8.428571; EXTERNAL_UNATTACHED 8.294643; EXTERNAL_STATE_ATTACHED 8.745536.
  - H1 PASS: Attached causal fit +1.53125 vs Unattached and +0.53125 vs Internal.
  - H2 PASS: institutional+specificity +0.28125 vs Unattached and +0.59375 vs Internal.
  - H3 FAIL: all-7 margin +0.316964 passes, but ensemble+future margin +0.109375 < frozen +0.15.
  - H4 PASS.
- Post-I4K2R nonhistorical regression: 258/258 PASS.

## PHYSICAL SYNC R6
Changed transports: CONTROL / A / B2 only. Parent-entry mismatch 0; exactly 13 R6 evidence entries appended to each; CRC/path safety PASS. B1/C1/C2-A/C2-B/D1/D2 are byte-identical from R5. C2 and DB59 reassembly PASS.

## EXACT NEXT BOUNDARY
Do NOT advance to I4K-3. The causal-fit defect is repaired, but second-order ensemble activation / future propagation is still below the preregistered incremental threshold. Perform knowledge-only propagation diagnosis first, then freeze a separate fresh propagation-focused repair/replication preregistration if warranted. Do not rewrite I4K-2 or I4K-2R verdicts.

## STATUS TOKEN
`CURRENT_HANDOFF__SYNC_R6_9DF7F7F6__ACTIVE_I4H_RECOVERY_R3__DB59_FROZEN__I4K1_PASS__I4K2_FAIL_H2__I4K2R_FAIL_H3_ENSEMBLE_FUTURE__NO_I4K3__REGRESSION_258_258__PRODUCTION_R47__FORMAL_137__R140_0_0_0`