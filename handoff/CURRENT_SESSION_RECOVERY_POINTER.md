# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-09

## READ FIRST
1. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
2. `handoff/20260909/P07_SYNC_R6_PHYSICAL_BYTES_HUB_STORAGE_AUDIT_R1_20260909.json`
3. `handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILD_SPEC_R1_20260909.md`
4. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json`
5. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_PREREG_AMENDMENT_R1_TARGETED_TEST_DEFINITION_20260909.json`
6. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_IMPLEMENTATION_CHECKPOINT_R1_20260909.json`
7. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_IMPLEMENTATION_PREFLIGHT_RESULT_R1_20260909.json`
8. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2/tests/test_p07_i4h_recovery_qualification_r2.py`
9. `handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILDER_R1.py`
10. `handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILDER_SELFTEST_RESULT_R1_20260909.json`
11. `handoff/20260909/P07_DEVELOPER_DELIVERY_BASELINE_CORRECTION_AND_CUMULATIVE_RECOVERY_R1_20260909.md`

## DEVELOPER-HELD PHYSICAL BASELINE
`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`

Physical active engine inside that baseline:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`.

The developer supplied all nine Sync R6 parent transport files in the current conversation earlier, but the GitHub Hub itself does **not** store those nine ZIP/BIN bytes. It stores authority/evidence records and recovery code.

Current local direct verification completed before execution-transport failure:
- CONTROL: expected SHA256 / CRC / duplicate=0 / unsafe=0 PASS;
- PART A: expected SHA256 / CRC / duplicate=0 / unsafe=0 PASS.

Current direct current-session verification remains `2/9`; the remaining seven require a functioning byte-addressable runtime.

This is not a corruption finding.

## FROZEN SYNC R6 IDENTITIES
- CONTROL `c291e9a3866de66fae625ab899139a13f1e98468a3bff0d58a11fd34553f0aa6`
- A `25eb489d07e78a3a3288e1e5029114ce791ada2ab43a8564ae9f9eed738306dd`
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 `40de0853fd8e1e8318658d64a4e8d26cb8e88711842639aa45b87c0e4d062c02`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `b775bf65cba23ad5611b3383678765f88c1a444d25c4b49f7ccfb5a9d2438ec9`
- C2-B `be4af1ac97467e1f090c8cd0854e14df1ffef6699ed23b0a80014f55e197e860`
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Combined C2 must be exact `C2-A || C2-B`:
- bytes `318351029`;
- SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`;
- entries `3765`;
- historical CRC PASS / duplicate 0 / unsafe 0.

DB59 frozen SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## HUB STORAGE BOUNDARY
Dedicated storage audit:
`handoff/20260909/P07_SYNC_R6_PHYSICAL_BYTES_HUB_STORAGE_AUDIT_R1_20260909.json`.

Across the inspected Git tree, historical I4D tree, I4H physical-closure Actions artifacts, Releases, recent File Library uploads and connected Google Drive, no trustworthy byte-addressable copy of the complete nine Sync R6 parent files is available from Hub-adjacent storage.

Correct rule:
`HUB_STORES_AUTHORITY_EVIDENCE_AND_RECOVERY_CODE__NOT_9_PARENT_PACKAGE_BYTES`.

## LOCAL EXECUTION FAILURE
Current local execution fails before filesystem work:
- container `/bin/true` -> `TransportTimeoutError`;
- private Python -> `TransportTimeoutError`;
- user-visible Python -> `TransportTimeoutError`.

Correct blocker:
`EXECUTION_TRANSPORT_TIMEOUT__NO_TRUSTWORTHY_BYTE_ADDRESSABLE_LOCAL_RUNTIME`.

## I4H RESEARCH / ENGINEERING STATE
- I4H R1: HOLD — pre-generation input contamination; no craft claim.
- I4H R2: HOLD — preselector durable-control multiplicity/transport defect; no craft claim.
- I4H R3: PASS — stronger-virtual prospective craft signal.
- I4H R4: PASS — fresh source-free masked physical replication.
- historical I4H Runtime Qualification: recorded PASS 42/42 new, 26/26 targeted, 255/255 full, parent I4D 5/5 byte-identical, critical accepts 0.

Historical test body `tests/test_p07_i4h_runtime_promotion.py` is not recoverable as source; only its recorded 15130-byte / SHA256 `9b7ef43744dfe094b2b1d1ec850c8712ba38a1f450a11c689ff43215f01fbf7a` identity remains. Do not invent it or claim exact historical rerun.

## RECOVERY QUALIFICATION R2 — NEW EVIDENCE
Preregistered before implementation:
- commit `cc7561d9ea16ff1c50e3d9971eb027423ddd9433`.

New recovery test body:
- 45 explicit tests;
- implementation commit `edee28bb75443ef3055bc40f5cc27c537b716abd`.

Stubbed-parent implementation preflight:
- 45/45 PASS / 0 fail;
- result commit `77329ceef66a4a293bc0aaf1e61e24019ff6f40b`.

This is implementation preflight only, not exact Sync R6 qualification.

### Deterministic targeted-regression amendment
The historical 26-test targeted list is not recoverable. Before any exact-parent R2 execution, a new deterministic definition was frozen:
`handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_PREREG_AMENDMENT_R1_TARGETED_TEST_DEFINITION_20260909.json`
Commit `ab36d5b818f1745204467fe5f85632937c2a0c10`.

Rule:
- on the exact parent materialization, scan nonhistory `tests/test_*.py`;
- select every test file containing at least one literal reference to the five frozen I4D modules/core symbols;
- sort paths lexicographically and seal selected-file SHA256 before execution;
- require every collected targeted test PASS;
- do not reuse the historical `26/26` label.

## FAIL-CLOSED PHYSICAL RECOVERY BUILDER — READY
Builder:
`handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILDER_R1.py`
Commit `b414af65b9bf0777c7d03800ebc265549ae7f2e7`.

The Builder automates the full physical recovery from exact Sync R6 parents:
1. verify all 9 parent outer byte lengths and SHA256;
2. run CRC / duplicate / unsafe-path checks on parent ZIPs;
3. reassemble and verify exact Sync R6 C2;
4. verify durable Hub I4H runtime source hashes;
5. materialize exact parent C2;
6. require the five frozen I4D runtime files byte-identical to recorded hashes;
7. overlay only the three authorized I4H runtime modules + new R2 test;
8. execute R2 45-test suite and require `45/45`;
9. discover and seal deterministic parent-targeted suite, then require 100% PASS;
10. run full nonhistorical regression and require `>=213 PASS / 0 failure`;
11. rebuild CONTROL / A / B2 and runtime C2;
12. copy B1 / C1 / D1 / D2 byte-identically;
13. split output C2 into C2-A / C2-B;
14. reassemble the output C2 and verify it again;
15. generate a fresh 9-package Final Physical Audit, package-set SHA256 and SHA256SUMS;
16. preserve Production `ENG:R47`, formal count `137`, R140 `0/0/0`, I4I `0/0/0/0`.

Builder implementation validation:
`handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILDER_SELFTEST_RESULT_R1_20260909.json`
Commit `fbb2afe65a03ce69ac12b2d54729499e2b660f2a`.

GitHub-hosted runner result:
- Python `py_compile`: PASS;
- Builder `--self-test`: `SELF_TEST_PASS`;
- workflow run `34308855331`, job `102331094936`.

This validates the Builder implementation only. It does not substitute for actual 9-parent execution.

## EXPECTED NEW PHYSICAL OUTPUT TOPOLOGY
When the Builder executes successfully it creates a new I4H Recovery R2 set:
- CONTROL — rebuilt;
- A — rebuilt;
- B1 — exact parent bytes;
- B2 — rebuilt;
- C1 — exact parent bytes;
- C2-A — rebuilt transport half;
- C2-B — rebuilt transport half;
- D1 — exact parent bytes;
- D2 — exact parent bytes.

Target active development authority after fresh audit:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R2`.

This is a new recovery authority, not historical Sync R8 byte reproduction.

## EXACT NEXT EXECUTION
Once a trustworthy runtime exposes the nine exact Sync R6 parent files as ordinary bytes:

```bash
python handoff/20260909/P07_I4H_PHYSICAL_RECOVERY_BUILDER_R1.py \
  --parent-dir /path/to/SYNC_R6_9_PARENTS \
  --hub-root /path/to/literary-os \
  --out-dir /path/to/LITERARY_OS_I4H_RECOVERY_R2_OUTPUT
```

The Builder itself refuses promotion on any parent mismatch, CRC/path failure, C2 mismatch, frozen-I4D mismatch, R2 failure, targeted regression failure, full-regression failure, output C2 failure or final package-audit failure.

Only an output directory whose sidecar `LITERARY_OS_I4H_RECOVERY_R2_FINAL_PHYSICAL_AUDIT_R1_20260909.json` has `overall_pass=true` may be delivered as recovered I4H physical authority.

## I4I BOUNDARY
I4I remains later and unexecuted:
- Control 0;
- selector 0;
- Treatment 0;
- scores 0.

Do not execute I4I before the new I4H 9-package authority is physically built, audited and delivered.

## FIXED SCIENTIFIC STATE
- Production `ENG:R47`
- Developer-held physical active engine **still** `P07-I4D` until Builder output is audited and delivered
- Hub-qualified recovery target `P07-I4H`
- Formal scored count `137`
- Latest formal authority `R138`
- Formal R140 `0/0/0`
- OpenAI Live qualification not established.

## STATUS TOKEN
`SYNC_R6_I4D_DEVELOPER_HELD__HUB_AUTHORITY_EVIDENCE_RECOVERED__9_PARENT_BYTES_NOT_HUB_STORED__2_OF_9_CURRENT_SESSION_DIRECT_VERIFIED__LOCAL_EXECUTION_TRANSPORT_TIMEOUT__I4H_R3_R4_PASS_HISTORICAL_RUNTIME_QUAL_PASS__RECOVERY_R2_45_TESTS_IMPLEMENTED__TARGETED_RULE_PREREGISTERED__BUILDER_IMPLEMENTED_COMPILE_SELFTEST_PASS__ACTUAL_9_PARENT_BUILDER_EXECUTION_PENDING__PHYSICAL_I4H_9_PACKAGE_OUTPUT_PENDING__I4I_0_0_0_0__FORMAL_137__R140_0_0_0`
