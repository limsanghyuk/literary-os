# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-09

## READ FIRST
1. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
2. `handoff/20260909/P07_SYNC_R6_PHYSICAL_BYTES_HUB_STORAGE_AUDIT_R1_20260909.json`
3. `handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILD_SPEC_R1_20260909.md`
4. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json`
5. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_IMPLEMENTATION_CHECKPOINT_R1_20260909.json`
6. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_IMPLEMENTATION_PREFLIGHT_RESULT_R1_20260909.json`
7. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2/tests/test_p07_i4h_recovery_qualification_r2.py`
8. `handoff/20260909/P07_DEVELOPER_DELIVERY_BASELINE_CORRECTION_AND_CUMULATIVE_RECOVERY_R1_20260909.md`

## CRITICAL CORRECTION — PHYSICAL BYTES ARE NOT STORED ON HUB
Developer-held physical baseline remains:
`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`
with active engine `CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`.

The GitHub hub does **not** contain the nine Sync R6 ZIP/BIN transport files themselves.
It contains their authority/evidence records: filenames, sizes, SHA256s, historical CRC/path-safety results, combined-C2 identity, DB59 identity, research lineage, I4H runtime delta and recovery tests.

Default-branch recursive tree audit at commit `4cf8a0397934e83b0bb5fdb06fb9beee563dfcb4` found:
- exact CONTROL physical binary path matches: 0;
- Sync R6 I4H virtual-pretest physical binary path matches: 0.

Dedicated storage audit:
`handoff/20260909/P07_SYNC_R6_PHYSICAL_BYTES_HUB_STORAGE_AUDIT_R1_20260909.json`
Commit `4a36230bcb34979e07a31bda1de2cbd914ee6f69`.

Do not state that the 9 physical packages were uploaded/loaded into GitHub.
Correct wording: the 9 package **authority identities and audit evidence** are durable on Hub; the 9 package **bytes are not**.

## FROZEN SYNC R6 IDENTITIES
- CONTROL SHA256 `c291e9a3866de66fae625ab899139a13f1e98468a3bff0d58a11fd34553f0aa6`
- A `25eb489d07e78a3a3288e1e5029114ce791ada2ab43a8564ae9f9eed738306dd`
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 `40de0853fd8e1e8318658d64a4e8d26cb8e88711842639aa45b87c0e4d062c02`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `b775bf65cba23ad5611b3383678765f88c1a444d25c4b49f7ccfb5a9d2438ec9`
- C2-B `be4af1ac97467e1f090c8cd0854e14df1ffef6699ed23b0a80014f55e197e860`
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Combined C2 must be exact `C2-A || C2-B`:
- bytes `318351029`
- SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`
- entries `3765`
- historical CRC PASS.

DB59 frozen SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## CURRENT CONVERSATION PHYSICAL INPUT STATE
The developer supplied all nine Sync R6 parents in this conversation earlier.
Before local execution transport failure, direct current-session byte verification completed for:
- CONTROL: SHA/CRC/path-safety PASS;
- PART A: SHA/CRC/path-safety PASS.

Remaining current-session direct physical verification: 7/9 pending.

File Search currently exposes the Sync R6 Final Physical Audit JSON and authority records, not a byte-addressable copy of all nine binary inputs.

## LOCAL EXECUTION FAILURE
Current local execution still fails before filesystem work:
- container `/bin/true` -> `TransportTimeoutError`;
- private Python -> `TransportTimeoutError`;
- user-visible Python -> `TransportTimeoutError`.

Correct blocker:
`EXECUTION_TRANSPORT_TIMEOUT__NO_TRUSTWORTHY_BYTE_ADDRESSABLE_LOCAL_RUNTIME`.

This is not a corruption finding.

## I4H RESEARCH / ENGINEERING STATE
- I4H R1: HOLD — pre-generation input contamination; no craft claim.
- I4H R2: HOLD — preselector durable-control multiplicity/transport defect; no craft claim.
- I4H R3: PASS — stronger-virtual prospective craft signal.
- I4H R4: PASS — fresh source-free masked physical replication.
- historical I4H Runtime Qualification: recorded PASS 42/42 new, 26/26 targeted, 255/255 full, parent I4D 5/5 byte-identical, critical accepts 0.

Exact historical test body is missing:
`tests/test_p07_i4h_runtime_promotion.py`, 15130 bytes, SHA256 `9b7ef43744dfe094b2b1d1ec850c8712ba38a1f450a11c689ff43215f01fbf7a`.
Do not invent it or claim exact 42/42 rerun.

## RECOVERY QUALIFICATION R2
Preregistered before implementation:
- commit `cc7561d9ea16ff1c50e3d9971eb027423ddd9433`.

New recovery test body:
- 45 explicit tests;
- commit `edee28bb75443ef3055bc40f5cc27c537b716abd`.

Stubbed-parent implementation preflight on GitHub-hosted runner:
- workflow run `34307097376`;
- 45/45 PASS, 0 fail;
- result commit `77329ceef66a4a293bc0aaf1e61e24019ff6f40b`.

This proves only the new R2 implementation harness under stubbed parent dependencies.
It is not exact-Sync-R6 qualification or physical-promotion evidence.

Inspection of the historical I4D result commit `d1fef19e8f4c07a0266f17f2307e734fd50ea587` and tree `57c0caaf4d2277aad5cac3f20010140eba57e996` did not recover the frozen parent runtime source files as ordinary GitHub paths. The actual non-stubbed parent materialization therefore still depends on the physical package bytes.

## CI REPAIR COMPLETED
A pre-existing repository CI failure was caused by stale `tools/test_inventory.json`, not I4H R2.
Official generator was run remotely and inventory refreshed to:
- test_count `11503`
- source_hash `34d9309c196cf604`
- pytest `9.1.1`
Commit `13c6d617560100c1a552f99517082affcff56346`.

CI 4-Tier run `34307265615` after refresh completed `success`.

## EXACT NEXT PHYSICAL RECOVERY ORDER
1. Obtain a trustworthy byte-addressable copy of all nine exact Sync R6 parents.
2. Verify 9/9 outer SHA256, CRC where applicable, duplicate=0, unsafe=0.
3. Reassemble C2 as exact `C2-A || C2-B` and verify SHA256 `9878aac8...3be7` / 318351029 bytes / 3765 entries / CRC PASS.
4. Materialize exact Sync R6/I4D parent runtime.
5. Overlay only the authorized durable I4H runtime delta and new R2 suite.
6. Execute all 45 R2 tests: require 100% PASS.
7. Execute old targeted regression: require 100% PASS.
8. Execute full nonhistorical regression: require >=213 PASS / 0 failures.
9. Verify five frozen parent I4D files 5/5 byte-identical and critical failure accepts 0.
10. Rebuild CONTROL / A / B2 / C2; preserve B1 / C1 / D1 / D2 byte-identically.
11. Split new C2 into transport C2-A / C2-B per frozen transport rule.
12. Generate a fresh 9-file Final Physical Audit, combined-C2 audit and DB59 audit.
13. Deliver all nine new physical files to the developer.
14. Only then mark P07-I4H developer-held physical authority.
15. Only afterward amend I4I parent binding and resume I4I.

## FIXED SCIENTIFIC STATE
- Production `ENG:R47`
- Developer-held physical active engine `P07-I4D`
- Hub-qualified next physical candidate `P07-I4H`
- Formal scored count `137`
- Latest formal authority `R138`
- Formal R140 `0/0/0`
- I4I Control/Selector/Treatment/Scores `0/0/0/0`
- OpenAI Live qualification not established.

## STATUS TOKEN
`SYNC_R6_I4D_DEVELOPER_HELD__HUB_HAS_AUTHORITY_EVIDENCE_NOT_9_BINARY_BYTES__ALL_9_WERE_SUPPLIED_IN_CONVERSATION__2_OF_9_DIRECTLY_VERIFIED_BEFORE_TRANSPORT_FAILURE__LOCAL_EXECUTION_TRANSPORT_TIMEOUT__I4H_R3_R4_PASS_HISTORICAL_RUNTIME_QUAL_PASS__HISTORICAL_TEST_BODY_MISSING__RECOVERY_R2_45_TESTS_IMPLEMENTED__STUBBED_PARENT_PREFLIGHT_45_OF_45_PASS__ACTUAL_SYNC_R6_QUAL_PENDING__PHYSICAL_I4H_9_PACKAGE_BUILD_PENDING__I4I_0_0_0_0__FORMAL_137__R140_0_0_0`
