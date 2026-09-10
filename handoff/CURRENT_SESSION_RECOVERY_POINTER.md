# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-10

## FIRST READ
1. `handoff/20260910/P07_I4K2R_RESEARCH_SYNC_R6_PHYSICAL_CLOSURE_R1_20260910.md`
2. `handoff/20260910/P07_I4K2R_STATE_ATTACHMENT_REPLICATION_FAIL_CLOSURE_R1_20260910.md`
3. `handoff/20260910/P07_I4K2_RESEARCH_SYNC_R5_PHYSICAL_CLOSURE_R1_20260910.md`
4. `handoff/20260910/P07_I4K2_EXTERNAL_SEARCH_ABLATION_FAIL_CLOSURE_R1_20260910.md`
5. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
6. `handoff/CURRENT_NEXT_RESEARCH_POINTER.md`

## CURRENT DURABLE STATE
Physical research-sync authority:
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R6__I4K2R_FAIL_H3_ENSEMBLE_FUTURE_MARGIN`

Nine-file material SHA256:
`9df7f7f6cc6e3c6790e98e168b6eb82a0c56bb8729280bcf9c2d95309675d216`

Active engine `P07-I4H Recovery R3`; combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Production `ENG:R47`; Formal `137`; latest `R138`; R140 `0/0/0`.

## I4K-2R RECOVERY FACTS
Experiment: `P07-I4K-2R-STATE-ATTACHED-EXTERNAL-MECHANISM-REPLICATION`.
Evidence class: masked same-agent Development/Preformal; blindness not independently provable.
Arms: Internal-only 16 / External-unattached 16 / External-state-attached 16.
Prescore: representation parity PASS; State Attachment Contract 16/16; hard gates 0.
Masked scoring: 48 x 7 = 336 values; score SHA `d050f5b6d673f69051af29ae0f722777837d15c49cc41923e9a7c030672f9708`; map unopened at score seal.

Means:
- Internal all-7 8.428571; causal 8.59375; ensemble+future 8.500000.
- Unattached all-7 8.294643; causal 7.59375; ensemble+future 8.250000.
- Attached all-7 8.745536; causal 9.125000; ensemble+future 8.609375.

Hypotheses:
- H1 PASS: causal fit recovered strongly.
- H2 PASS: institutional+specificity preserved/improved.
- H3 FAIL: all-7 margin +0.316964 passes, but ensemble+future margin +0.109375 < +0.15.
- H4 PASS.

Verdict: `FAIL__H3_ENSEMBLE_FUTURE_MARGIN_BELOW_PREREG_THRESHOLD__NO_I4K3_ENTRY`.
Post regression: 258/258 PASS.

## PHYSICAL SYNC R6
Changed CONTROL/A/B2 only; 13 evidence entries appended per changed ZIP; parent metadata mismatch 0; CRC/path safety PASS. B1/C1/C2-A/C2-B/D1/D2 byte-identical from R5. C2 and DB59 reassembly PASS.

## MANDATORY RESUME ORDER
1. minimal process → filesystem → cgroup/OOM → small archive preflight;
2. verify Sync R6 material SHA and read I4K-2R closure;
3. do not alter I4K-2 or I4K-2R thresholds/verdicts;
4. perform knowledge-only ensemble/future propagation diagnosis;
5. only if justified, freeze a new fresh propagation-focused preregistration before output;
6. run the replication;
7. only a full fresh PASS may authorize I4K-3 preregistration;
8. regression/package-impact/full physical sync after meaningful research.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R6_9DF7F7F6__ACTIVE_I4H_R3__I4K2R_FAIL_H3_ENSEMBLE_FUTURE__PROPAGATION_DIAGNOSTIC_NEXT__NO_I4K3__DB59__PRODUCTION_R47__FORMAL_137__R140_0_0_0`