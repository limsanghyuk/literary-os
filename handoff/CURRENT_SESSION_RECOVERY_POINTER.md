# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-09

## READ ORDER
1. Read this file first.
2. Read `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`.
3. Read `handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILD_SPEC_R1_20260909.md`.
4. Read `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json`.
5. Read `handoff/20260909/P07_NEW_SESSION_SYNC_R6_I4H_RECOVERY_VERIFICATION_R1_20260909.md`.
6. Read `handoff/20260909/P07_DEVELOPER_DELIVERY_BASELINE_CORRECTION_AND_CUMULATIVE_RECOVERY_R1_20260909.md`.
7. Read `handoff/20260909/P07_FILE_LIBRARY_ARCHIVE_MOUNT_RECOVERY_INDEX_R1.md`.
8. Read `handoff/20260909/START_HERE_P07_DEVELOPER_HELD_SYNC_R6_CUMULATIVE_RECOVERY_R1.md`.
9. Read `handoff/20260908/START_HERE_P07_SYNC_R6_PHYSICAL_AUTHORITY_NEW_SESSION_HANDOFF_R1.md`.

## DEVELOPER-HELD PHYSICAL BASELINE
`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`
This remains the last complete 5-Part / 9-Package set actually held by the developer as a completed authority set.

Physical active engine inside that baseline:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`

Combined parent C2:
- SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`
- bytes `318351029`
- entries `3765`
- CRC PASS.

DB59 frozen SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## CURRENT CONVERSATION — ALL NINE PARENTS RESUPPLIED
The developer has now supplied all nine exact Sync R6 parent transport files in the current conversation:
CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2.

Direct current-session byte verification completed before the execution layer failed:
- CONTROL exact parent SHA/CRC/path-safety PASS;
- PART A exact parent SHA/CRC/path-safety PASS.

Remaining seven direct byte checks are pending because container/private-Python/user-visible-Python now return `TransportTimeoutError` even for minimal `echo`, `stat` and `getsize` operations.

Correct classification:
`ALL_9_SYNC_R6_PARENTS_SUPPLIED__2_OF_9_DIRECT_BYTE_VERIFIED__EXECUTION_TRANSPORT_TIMEOUT_PREVENTS_REMAINING_7_VERIFICATION_AND_BINARY_BUILD`.

This is not a corruption finding.

## POST-DELIVERY HUB I4H STATE
Durable Hub research/engineering evidence:
- I4H R1 HOLD: pre-generation input contamination, no craft claim;
- I4H R2 HOLD: preselector durable-control multiplicity/transport defect, no craft claim;
- I4H R3 PASS: stronger-virtual prospective craft signal;
- I4H R4 PASS: fresh source-free masked physical replication;
- I4H Runtime Promotion Qualification PASS recorded: 42/42 new, 26/26 targeted, 255/255 full nonhistorical regression, parent I4D files 5/5 byte-identical, critical failure accepts 0;
- runtime source modules durable on Hub.

Correct classification:
`P07-I4H = HUB-QUALIFIED NEXT-PHYSICAL-AUTHORITY CANDIDATE`.

It is not yet developer-held physical authority.

## EXACT TEST-BODY RECOVERY LIMIT
The historical qualification result records:
`tests/test_p07_i4h_runtime_promotion.py`
- bytes `15130`;
- SHA256 `9b7ef43744dfe094b2b1d1ec850c8712ba38a1f450a11c689ff43215f01fbf7a`.

Current GitHub recursive-tree inspection, GitHub code search, File Library search and connected Google Drive search do not rediscover the exact test-body source.

Therefore exact historical Sync R8 C2 byte reproduction is limited by:
`MISSING_EXACT_I4H_QUALIFICATION_TEST_BODY`.

Do not fabricate byte identity or claim an exact historical 42/42 rerun without the source.

### Recovery solution now preregistered
A separate new recovery qualification suite has been preregistered before implementation/execution:
`handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json`
Commit `cc7561d9ea16ff1c50e3d9971eb027423ddd9433`.

This R2 suite:
- preserves the original I4H runtime architecture and promotion gates;
- is bound to exact developer-held Sync R6 / I4D parent materialization;
- requires at least 25 new recovery tests and reports the actual count;
- must not call itself the historical 42-test suite or byte-identical reproduction;
- requires 100% recovery-test PASS, 100% old targeted PASS, full nonhistorical regression >=213 with 0 failures, 5/5 frozen parent I4D byte identity, ABSTAIN exact invariance, fault-injection fail-closed behavior, zero critical accepts, and Python literary prose=false;
- currently has no implemented test body, no execution and no result.

Correct status:
`RECOVERY_QUAL_R2_PREREGISTERED__NO_IMPLEMENTATION__NO_EXECUTION__NO_RESULT__NO_AUTHORITY_CHANGE`.

## I4H-ONLY PHYSICAL RECOVERY TARGET
The developer's immediate requested scope is recovery through I4H.

Build directly from exact Sync R6 parents + durable Hub I4H deltas.

Must rebuild/change:
- CONTROL;
- PART A;
- PART B2;
- PART C2-A / PART C2-B after parent C2 reassembly and authorized I4H runtime/qualification overlay.

Must remain byte-identical:
- PART B1;
- PART C1;
- PART D1;
- PART D2.

Historical session-internal Sync R8 may be used only as reconstruction reference:
- target active behavior `CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_R1`;
- combined C2 bytes `318364190`;
- entries `3771`;
- SHA256 `eb49afacc0ef0377fc619e33c01603fe69ffcdc7d242a041a5a1d2c26c0d3ef0`;
- physical closure commit `2af29e335789aee7b72461d3bac3323cb79d6805`.

A new recovery build is not required to reproduce the old Sync R8 outer ZIP hashes. Fresh member-level identity, new recovery qualification evidence and a complete new physical audit control the recovered authority.

## I4I BOUNDARY
I4I preregistration and 11-sequence / 56-scene plan freeze remain durable on Hub, but are a later research unit.

Execution state:
- Control 0;
- selector 0;
- Treatment 0;
- scores 0;
- no I4I result.

Do not execute I4I until the I4H physical recovery package is built, audited and delivered.

## CURRENT EXECUTION / PACKAGING STATUS
An earlier probe in this session showed writable ZIP/SHA capability temporarily available and CONTROL/A were directly verified.

After additional large-package uploads, the execution transport began returning `TransportTimeoutError` before any filesystem operation, including minimal pings.

Private Python, user-visible Python and container shell all reproduce the same transport-level failure.

Current blocker is therefore not missing parent files and not established package corruption. It is:
`EXECUTION_TRANSPORT_TIMEOUT__NO_TRUSTWORTHY_BYTE_ADDRESSABLE_RUNTIME`.

## NEXT EXACT ACTION
1. Restore a functioning byte-addressable execution runtime.
2. Verify all 9 supplied Sync R6 parent outer hashes / CRC / duplicate=0 / unsafe=0.
3. Verify combined Sync R6 C2.
4. Materialize the three exact durable I4H runtime source files and the preregistered Recovery Qualification R2 test suite.
5. Execute Recovery Qualification R2 and record the actual new-test count/results; do not reuse historical 42/42 labeling.
6. Require old targeted 100% PASS and full nonhistorical regression >=213 PASS / 0 fail.
7. Build I4H physical recovery package directly from Sync R6 + authorized Hub I4H deltas + new recovery qualification evidence.
8. Preserve B1/C1/D1/D2 byte-identically.
9. Audit all nine output files, combined C2 and DB59.
10. Deliver all nine output files to the developer.
11. Only then mark P07-I4H as developer-held physical authority.
12. Only afterward repair the I4I parent-authority binding and resume I4I.

## FIXED SCIENTIFIC STATE
- Production `ENG:R47`
- Developer-held physical active engine `P07-I4D`
- Hub-qualified target `P07-I4H`
- Formal scored count `137`
- Latest formal authority `R138`
- Formal R140 `0/0/0`
- OpenAI Live qualification not established

## STATUS TOKEN
`DEVELOPER_HELD_SYNC_R6_I4D__ALL_9_PARENTS_RESUPPLIED__2_OF_9_DIRECT_BYTE_VERIFIED__EXECUTION_TRANSPORT_TIMEOUT__I4H_R1_HOLD_R2_HOLD_R3_PASS_R4_PASS_RUNTIME_QUAL_PASS__HISTORICAL_QUAL_TEST_BODY_MISSING__RECOVERY_QUAL_R2_PREREGISTERED_NO_RESULT__I4H_PHYSICAL_RECOVERY_BUILD_REQUIRED__I4I_PLAN_FROZEN_OUTPUT_0__RESEARCH_FROZEN__FORMAL_137__R140_0_0_0`
