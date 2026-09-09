# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-09

## READ FIRST
1. `handoff/20260909/START_HERE_P07_I4H_RECOVERY_R3_PHYSICAL_AUTHORITY_R1.md`
2. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
3. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json`
4. `handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_PREREG_AMENDMENT_R1_TARGETED_TEST_DEFINITION_20260909.json`
5. `handoff/20260908/START_HERE_P07_SYNC_R6_PHYSICAL_AUTHORITY_NEW_SESSION_HANDOFF_R1.md`

## RECOVERY STATUS
The previous `EXECUTION_TRANSPORT_TIMEOUT__NO_TRUSTWORTHY_BYTE_ADDRESSABLE_LOCAL_RUNTIME` blocker is no longer the current state.

In the recovered runtime:
- exact Sync R6 parent transport files were directly verified `9/9`;
- all parent ZIP CRC / duplicate / unsafe / symlink / encryption checks passed;
- parent combined C2 reassembled exactly to SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`;
- B Research Master, C Narrative Master and D/DB59 logical reconstructions all passed;
- exact active I4D materialization reproduced `213/213 PASS` and five frozen I4D files were `5/5` byte-identical.

## EXACT-PARENT I4H QUALIFICATION
Recovery R2 exact-parent result:
`HOLD 44/45`.

Cause: episode I4H wiring discovered a missing later-scene profile only after beginning the first scene bridge. This violated the intended fail-closed whole-episode preflight ordering.

The R2 HOLD remains durable and must not be rewritten as PASS.

Corrective Recovery R3 was preregistered after observing the R2 failure and before changing code. Only `literary_os_runtime/i4h_episode_render_wiring.py` was authorized to change, adding whole-episode profile completeness validation before any bridge/provider call.

Corrected file SHA256:
`f90a6cdc699f0c6dd5631af8283c6c97a75dd2ad9ed28d7e6ef83908815f9727`.

R3 qualification:
- Recovery tests `45/45 PASS`;
- deterministic parent-targeted regression `56/56 PASS`;
- full nonhistorical regression `258/258 PASS`;
- critical failure accepts `0`;
- Python literary prose generated `false`.

## CURRENT PHYSICAL AUTHORITY
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R3`

Package-set SHA256:
`9327630e8fc8c9b88a8233055b939e08ab5d3726a777b44122bb6682a8c436f8`.

Combined recovered C2:
- bytes `318368553`;
- entries `3774`;
- SHA256 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`;
- CRC/path-safety PASS.

Final active materialization order:
1. `CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY`
2. `P07_I3_BROADCAST_SURFACE_R1/CODE`
3. `P07_I4A_PROVIDER_SHADOW_DELTA_R1`
4. `P07_I4B_SURFACE_INTERFACE_DELTA_R1`
5. `P07_I4D_SURFACE_REALIZATION_MODE_DELTA_R1`
6. `P07_I4H_RUNTIME_RECOVERY_R3_DELTA_R1`

An independent second-pass verifier rejoined final C2, rematerialized this exact chain, rechecked package/logical integrity and reran the full regression: `258/258 PASS`.

## OPERATIONAL FAILURE FINDINGS
Sync R6 corruption was ruled out.

Recovered-session findings:
- a generated-file durability boundary error (`GeneratedFileUploadError`) was reproduced after local filesystem work had completed, supporting a tool/platform transport-layer failure class for at least part of the historical instability;
- the container has a hard cgroup 4 GiB memory limit and zero swap; large sequential archive reads filled page cache and hit `memory.events max`, but `oom=0` and `oom_kill=0` throughout recovery;
- safe operating rule is streaming I/O, `/tmp` intermediates, `POSIX_FADV_DONTNEED` cache release after large reads, and final-only movement to `/mnt/data`;
- Hub Recovery Builder R1 had a real integration defect: it treated multi-overlay C2 as a root project tree. Correct materialization must use the six-stage order above.

## FIXED SCIENTIFIC STATE
- Active development physical authority: `P07-I4H Recovery R3`.
- Production: `ENG:R47`.
- DB59: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- Formal scored count: `137`.
- Latest formal authority: `R138`.
- R140: `0/0/0`.
- I4I: `0/0/0/0`, unexecuted.
- OpenAI Live qualification: not established.

## NEXT BOUNDARY
I4H physical recovery is complete. Do not rerun or relabel historical 42/42 or 26/26 evidence. Do not treat session-only historical Sync R8 bytes as the parent of this recovery.

The next research phase may resume only from this R3 physical authority and the already durable I4I preregistration/plan material. I4I still has no Control, selector, Treatment or score output.

## STATUS TOKEN
`I4H_RECOVERY_R3_PHYSICAL_CLOSURE_COMPLETE__SYNC_R6_PARENT_9_9__I4D_213_213__R2_HOLD_44_45__R3_45_45__TARGETED_56_56__FULL_258_258__PACKAGE_SET_9327630E__FINAL_C2_58D28ECC__DB59_FROZEN__PRODUCTION_R47__FORMAL_137__R140_0_0_0__I4I_0_0_0_0`
