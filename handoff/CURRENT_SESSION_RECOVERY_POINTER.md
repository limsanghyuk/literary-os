# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-11

## READ FIRST
1. `handoff/20260911/P07_I4K5R3_INTERNAL_MASKED_FINAL_RESULT_R1_20260911.json`
2. `handoff/20260911/P07_I4K5R3_MASK_R1_INTERNAL_SCORE_SEAL_R1_20260911.json`
3. `handoff/20260911/P07_I4K5R3_RECOVERY_DUPLICATE_RESCORE_QUARANTINE_R1_20260911.json`
4. `handoff/20260911/P07_I4K5R2_CLOSED_I4K5R3_PREREG_SYNC_R21_PHYSICAL_CLOSURE_R1_20260911.md`
5. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R21__I4K5R2_VALID_FAIL_CLOSED__I4K5R3_PSSB_PREREG_OUTPUTS_0`
R21 root `65093f163ac38ab23e67153421494f0edf06a28bedac5debaa7d3a3be7de57eb`; closure commit `67e6d51ac73324a9f257501443dd9bed61e61b31`.

## EXACT RESEARCH STATE
I4K-5R3 is already CLOSED as valid internal masked PASS. Prescore admission `c481e6e1b3efa619525d3eef0fc5648734b9d9b7`; canonical masked score seal `90a0d7985025fa0ebf221ae32aaa942b82271b50`; canonical result `c241d0d7d030d143f2cd2e145308f9858953d566`.
Treatment = 9W/2T/1L; H1/H2/H3/H4 all PASS. Dialogue +0.375; Stage Direction +0.875; Broadcast Readiness +0.7916666667.
Recovery duplicate score `f760cebfda473696654f535ffefc6c0373100212` occurred only because the visible checkpoint was stale after the canonical result had already committed. It is non-authority and quarantined by `61d3d180e804777594c5197a994c67fea1beeadf`.

## MANDATORY RESUME ORDER
1. Do not score, remask, rerender, or unblind R3 again.
2. Verify R21 transport set and current container memory/OOM state.
3. Create R22 append-only physical propagation with canonical R3 evidence in CONTROL/A/B2 only.
4. Reuse B1/C1/C2-A/C2-B/D1/D2 byte-identically.
5. Audit R22: 9 outer SHA, changed ZIP CRC, parent-entry metadata, B2 filename metadata, Combined C2, DB59, B/C master reassemblies.
6. Seal R22 physical closure and START_HERE; update all CURRENT pointers.
7. After R22 only, preregister a fresh independent/external PSSB confirmation experiment.

## RUNTIME / TOOL NOTE
Prior interruptions sometimes came from page cache near the 4GiB cgroup ceiling, not OOM or file corruption. Use streaming verification and POSIX_FADV_DONTNEED for large files if memory.current rises. Most recent recovery check was healthy (~294MB, OOM/kill 0).

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; Formal 137; latest R138; R140 `0/0/0`.

## STATUS TOKEN
`SESSION_RECOVERY__PHYSICAL_R21__CANONICAL_R3_INTERNAL_PASS_CLOSED__DUPLICATE_RESCORE_QUARANTINED__NEXT_BUILD_R22`
