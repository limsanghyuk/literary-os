# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-09

## DEVELOPER-HELD PHYSICAL PACKAGE AUTHORITY
`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`

This remains the last complete **5 Parts / 9 transport files** package set actually supplied to and held by the developer as a completed authority set.

The historical session-internal Sync R7 and Sync R8 builds were not handed back to the developer as all nine files and are not developer-held physical authorities. They may be used only as reconstruction references.

Mandatory correction / cumulative recovery document:
`handoff/20260909/P07_DEVELOPER_DELIVERY_BASELINE_CORRECTION_AND_CUMULATIVE_RECOVERY_R1_20260909.md`
Commit `76264d5a35f2dd52845203150df6db8ec45e6552`.

Current I4H physical recovery build specification:
`handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILD_SPEC_R1_20260909.md`
Commit `abe3801582441e07031261c52c0b39c9dbf2ab65`.

## DEVELOPER-HELD PHYSICAL ENGINE STATE
Physical active authority inside Sync R6:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`

Developer-held combined C2 baseline:
- SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`
- bytes `318351029`
- entries `3765`
- CRC PASS.

DB59 frozen SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

Production remains `ENG:R47`.
Formal scored count remains `137`.
Latest formal authority remains `R138`.
Formal R140 remains `0/0/0`.
OpenAI Live qualification is not established.

## CURRENT CONVERSATION PARENT-FILE SUPPLY / DIRECT VERIFICATION
The developer has supplied all nine exact Sync R6 parent transport files again in the current conversation:
CONTROL / PART A / PART B1 / PART B2 / PART C1 / PART C2-A / PART C2-B / PART D1 / PART D2.

Before the execution-transport failure, direct byte verification completed for CONTROL and PART A:
- exact expected Sync R6 SHA256 matched;
- CRC PASS;
- duplicate paths 0;
- unsafe paths 0.

The remaining seven supplied files have not yet received trustworthy current-session direct byte verification.

Current local execution diagnosis is stronger than the earlier large-file hypothesis:
- private Python -> `TransportTimeoutError`;
- user-visible Python -> `TransportTimeoutError`;
- container shell -> `TransportTimeoutError`;
- failures occur even for minimal `echo`, `stat`, `getsize`, `/bin/true` before package processing.

Therefore the current blocker is:
`EXECUTION_TRANSPORT_TIMEOUT__NO_TRUSTWORTHY_BYTE_ADDRESSABLE_LOCAL_RUNTIME`.

This is **not** evidence of package corruption.

Correct physical status:
`ALL_9_SYNC_R6_PARENTS_SUPPLIED__2_OF_9_DIRECT_BYTE_VERIFIED__7_OF_9_DIRECT_VERIFICATION_PENDING_EXECUTION_RECOVERY`.

## HUB-QUALIFIED POST-DELIVERY I4H RESEARCH STATE
### I4H prospective craft research
- R1: pre-generation contamination HOLD; no craft claim.
- R2: preselector control multiplicity/transport HOLD; no craft claim.
- R3: stronger-virtual prospective craft signal PASS; Method Audit Closure `17e33163a519edb68bcc80c4970ebb255d4b0c51`.
- R4: fresh source-free masked physical replication PASS; result `16773b5ad9a97ca709f0476d227c4a04fa60909d`.
  - sample 21 = ABSTAIN7 / LOW7 / STANDARD7;
  - interventions Treatment7 / Control0 / Tie7;
  - nonloss 100%, harmful 0%, mean delta +0.32699;
  - STANDARD 7/7 wins, mean +0.42699;
  - LOW relational-subtext positive nonloss signal, mean +0.227, voice loss 0.

Correct research classification:
`P07-I4H = HUB-QUALIFIED NEXT-PHYSICAL-AUTHORITY CANDIDATE`.

It is not yet developer-held physical authority.

## HISTORICAL I4H RUNTIME QUALIFICATION AND RECOVERY DEFECT
Historical runtime qualification preregistration:
`ac7202ac7743252ac1bb8b0ac50cb84287b7dfcd`.

Historical qualification result:
`8fa611b801118ecf2b703cf1f41288c6a7e84bcc`.

Recorded historical qualification:
- new tests 42/42 PASS;
- old targeted tests 26/26 PASS;
- full nonhistorical regression 255/255 PASS = parent 213 + new 42;
- frozen parent I4D files 5/5 byte-identical;
- critical failure accepts 0;
- Python literary prose generation false.

Durable runtime source modules remain on Hub:
- `handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_intervention_policy.py`
- `handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_runtime_renderer.py`
- `handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_episode_render_wiring.py`.

Historical qualification records identify:
`tests/test_p07_i4h_runtime_promotion.py`
- bytes `15130`;
- SHA256 `9b7ef43744dfe094b2b1d1ec850c8712ba38a1f450a11c689ff43215f01fbf7a`.

The exact historical test-body source is not currently rediscoverable in GitHub tree/history searched, File Library index, or connected Google Drive search.

Correct defect classification:
`MISSING_EXACT_I4H_QUALIFICATION_TEST_BODY`.

The historical PASS remains durable historical evidence, but exact historical 42-test rerun / exact old Sync R8 C2 byte reproduction must not be claimed from an invented replacement.

## RECOVERY QUALIFICATION R2 — NEW EVIDENCE, NOT HISTORICAL REPRODUCTION
A new recovery qualification path was preregistered before implementation:
- path `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json`;
- commit `cc7561d9ea16ff1c50e3d9971eb027423ddd9433`.

New test body:
- path `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2/tests/test_p07_i4h_recovery_qualification_r2.py`;
- implementation commit `edee28bb75443ef3055bc40f5cc27c537b716abd`;
- 45 explicit test functions.

Implementation checkpoint:
- `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_IMPLEMENTATION_CHECKPOINT_R1_20260909.json`;
- commit `bef90190b20e0e15d25ea0e3e32ff1c2ee435962`.

Because local execution is unavailable, a GitHub-hosted implementation preflight was executed using the exact three durable I4H source modules with only parent dependencies stubbed for the harness.

Preflight result:
- workflow run `34307097376`;
- job `102325943807`;
- `45 passed / 0 failed / 1 warning`;
- duration `0.14s`;
- durable result path `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_IMPLEMENTATION_PREFLIGHT_RESULT_R1_20260909.json`;
- result commit `77329ceef66a4a293bc0aaf1e61e24019ff6f40b`.

Correct interpretation:
`R2 IMPLEMENTATION PREFLIGHT = PASS 45/45 UNDER STUBBED PARENT DEPENDENCIES`.

It is **not**:
- exact Sync R6 materialization qualification;
- historical 42/42 reproduction;
- old targeted regression;
- full nonhistorical regression;
- 5/5 parent-I4D byte-identity proof;
- nine-package integrity proof;
- physical promotion evidence.

Actual Recovery Qualification R2 remains pending exact Sync R6 materialization and the preregistered promotion gates.

## REPOSITORY CI MAINTENANCE FINDING
The repository CI had a pre-existing Phase-A Exit EA-6 failure caused by stale `tools/test_inventory.json`, not by the I4H R2 handoff test body.

Evidence:
- the same CI failure existed on commit `abe3801582441e07031261c52c0b39c9dbf2ab65`, before R2 test implementation;
- failing R2 implementation run still executed 4,937 unit tests successfully with only two EA-6/overall failures pointing to stale inventory;
- official generator `tools/generate_test_inventory.py` was executed on a GitHub-hosted runner.

Official refreshed inventory:
- test_count `11503`;
- generated_at `2026-09-09T03:25:54.602045+00:00`;
- pytest `9.1.1`;
- source_hash `34d9309c196cf604`.

Inventory refresh commit:
`13c6d617560100c1a552f99517082affcff56346`.

This is repository bookkeeping/CI repair and has no I4H scientific-authority effect.

## I4H-ONLY PHYSICAL RECOVERY TARGET
The developer's requested immediate recovery scope is through I4H.

Build directly from exact Sync R6 parents + durable Hub I4H deltas + successful actual Recovery Qualification R2 evidence.

Must rebuild/change:
- CONTROL;
- PART A;
- PART B2;
- PART C2-A / C2-B after exact parent C2 reassembly and authorized I4H runtime/qualification overlay.

Must remain byte-identical:
- PART B1;
- PART C1;
- PART D1;
- PART D2.

Historical session-internal Sync R8 is reconstruction reference only:
- target behavior `CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_R1`;
- reference combined C2 bytes `318364190`;
- entries `3771`;
- SHA256 `eb49afacc0ef0377fc619e33c01603fe69ffcdc7d242a041a5a1d2c26c0d3ef0`;
- reference physical closure commit `2af29e335789aee7b72461d3bac3323cb79d6805`.

A fresh recovered authority need not reproduce historical Sync R8 outer ZIP hashes. It must instead prove exact Sync R6 parent identity, authorized member-level I4H delta, successful new recovery qualification, unchanged-parent byte identity, C2/DB59 integrity and complete new nine-file physical audit.

## I4I RESEARCH UNIT — LATER / UNEXECUTED
I4I preregistration `e4bb3a9571db87c7553b183c8a39c3bdb498a143` and the frozen 11-sequence / 56-scene plan remain durable.

I4I exact execution state:
- Control outputs 0;
- selector decisions 0;
- Treatment outputs 0;
- blind scores 0;
- no I4I result claim.

Do not execute I4I until the I4H physical recovery package is built, audited and delivered.

After the recovered I4H physical package is delivered, a pre-output administrative parent-authority amendment is required before I4I Control output 1 while preserving the frozen plan/hypotheses/gates unchanged.

## RECOVERY SUFFICIENCY / CURRENT BLOCKERS
Research-state recovery from Hub: **YES**.

All exact Sync R6 parent files supplied in current conversation: **YES**.

R2 new test body durable: **YES**.

R2 implementation preflight on remote runner: **45/45 PASS**, but only under stubbed parent dependencies.

Current trustworthy local byte-level rebuild/audit ability: **NO — execution transport times out before filesystem operations**.

Current direct physical verification: **2/9**.

Actual R2 qualification against exact Sync R6: **NOT YET EXECUTED**.

Therefore physical I4H recovery remains blocked by:
1. local/otherwise byte-addressable access to the nine supplied Sync R6 parent files;
2. completion of 9/9 SHA/CRC/path-safety and parent-C2 verification;
3. actual R2 qualification/regression against exact parent materialization;
4. final 5-Part/9-Package build and audit.

## HARD RESEARCH FREEZE
Do not execute I4I Control, Treatment, scoring or later research before I4H physical recovery is completed, audited and delivered.

## NEXT EXACT OPERATION
1. Restore or obtain a trustworthy byte-addressable execution path to the nine supplied Sync R6 files.
2. Verify 9/9 outer SHA256 / CRC / duplicate=0 / unsafe=0.
3. Reassemble and verify Sync R6 combined C2.
4. Materialize exact durable I4H runtime sources + new R2 suite over exact Sync R6/I4D parent.
5. Execute all 45 R2 tests and require 100% PASS.
6. Execute old targeted regression and require 100% PASS.
7. Execute full nonhistorical regression and require >=213 PASS / 0 fail.
8. Verify frozen parent I4D files 5/5 byte-identical and critical failure accepts 0.
9. Build CONTROL/A/B2/C2-A/C2-B; copy B1/C1/D1/D2 byte-identically.
10. Audit all nine output packages, combined C2 and DB59.
11. Deliver all nine output files to the developer.
12. Only then mark P07-I4H as developer-held physical authority.
13. Only afterward address I4I parent binding and resume I4I.

## CLAIM BOUNDARY
Supported now:
- all nine exact Sync R6 parents supplied;
- Sync R6 topology and frozen audit identities recovered;
- CONTROL/A directly verified in current session;
- I4H R1/R2/R3/R4 and historical runtime qualification lineage cross-validated;
- historical qualification test-body reproducibility defect identified;
- new R2 recovery qualification preregistered before implementation;
- new R2 test body implemented with 45 tests;
- R2 implementation preflight 45/45 PASS under stubbed parent dependencies;
- stale repository test inventory independently repaired from official remote generation;
- I4H remains Hub-qualified next physical candidate;
- I4I remains frozen/unexecuted.

Not supported now:
- current-session 9/9 direct physical verification;
- actual R2 qualification against exact Sync R6;
- newly built/audited/delivered I4H 9-file package set;
- developer-held physical I4H authority;
- exact historical Sync R8 byte reproduction;
- I4I result;
- Production change;
- formal-count change;
- R140 start;
- OpenAI Live qualification.

## STATUS TOKEN
`DEVELOPER_HUB__SYNC_R6_I4D_DEVELOPER_HELD__ALL_9_PARENTS_RESUPPLIED__2_OF_9_DIRECT_BYTE_VERIFIED__LOCAL_EXECUTION_TRANSPORT_TIMEOUT__I4H_R1_HOLD_R2_HOLD_R3_PASS_R4_PASS_HISTORICAL_RUNTIME_QUAL_PASS__HISTORICAL_TEST_BODY_MISSING__RECOVERY_QUAL_R2_PREREGISTERED_IMPLEMENTED_45_TESTS__REMOTE_STUBBED_PARENT_PREFLIGHT_45_OF_45_PASS__ACTUAL_SYNC_R6_QUAL_PENDING__I4H_PHYSICAL_RECOVERY_BUILD_PENDING__I4I_PLAN_FROZEN_OUTPUT_0__FORMAL_137__R140_0_0_0`
