# START HERE — P07-I4H Recovery R3 Physical Authority R1

Date: 2026-09-09
Classification: DEVELOPMENT / PREFORMAL / PHYSICAL RECOVERY CLOSURE

## 1. Current developer-delivered physical authority

The exact developer-held Sync R6 5-Part / 9-Package set was mounted and directly reverified 9/9 in a healthy byte-addressable runtime. The current developer-delivered recovered authority is now:

`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R3`

Parent physical authority:
`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`

Parent active engine:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`

Production remains `ENG:R47`.
Formal scored count remains `137`.
Latest formal authority remains `R138`.
R140 remains `0/0/0`.
I4I remains `0/0/0/0` and unexecuted.
OpenAI Live qualification is not established.

## 2. Exact recovered 5-Part / 9-Package transport set

Package-set SHA256:
`9327630e8fc8c9b88a8233055b939e08ab5d3726a777b44122bb6682a8c436f8`

1. CONTROL
`LITERARY_OS_CURRENT_CONTROL_P07_I4H_RECOVERY_R3_20260909.zip`
- bytes `108642318`
- SHA256 `4ae0d3278a0f0b15f17195e982ac2c6bb654266fd063e31d1bea6f8352edf3a2`

2. PART A
`LITERARY_OS_CURRENT_PART_A_P07_I4H_RECOVERY_R3_20260909.zip`
- bytes `123072738`
- SHA256 `e6786ab21f23c29c32dd3d77d436023b618ba587cf2a66ddd8883e4d5852d005`

3. PART B1
`LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_20260909.zip`
- bytes `196427036`
- SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- byte-identical to Sync R6 parent

4. PART B2
`LITERARY_OS_CURRENT_PART_B2_P07_I4H_RECOVERY_R3_20260909.zip`
- bytes `255176463`
- SHA256 `3aa4e358b5e8097ad2e0ea401fe14657425e9b7b68e2df4e5ceaf97f882c9000`

5. PART C1
`LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_20260909.zip`
- bytes `140020974`
- SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- byte-identical to Sync R6 parent

6. PART C2-A
`LITERARY_OS_CURRENT_C2_BINARY_A_P07_I4H_RECOVERY_R3_20260909.bin`
- bytes `159184277`
- SHA256 `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`

7. PART C2-B
`LITERARY_OS_CURRENT_C2_BINARY_B_P07_I4H_RECOVERY_R3_20260909.bin`
- bytes `159184276`
- SHA256 `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`

8. PART D1
`LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_20260909.zip`
- bytes `138011573`
- SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- byte-identical to Sync R6 parent

9. PART D2
`LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_20260909.zip`
- bytes `173393886`
- SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`
- byte-identical to Sync R6 parent

## 3. Final C2 and logical 5-Part integrity

Recovered combined C2 (`C2-A || C2-B`):
- bytes `318368553`
- entries `3774`
- SHA256 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`
- CRC PASS
- duplicate paths 0
- unsafe paths 0
- symlink 0
- encrypted members 0

Active materialization order:
1. `CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY`
2. `P07_I3_BROADCAST_SURFACE_R1/CODE`
3. `P07_I4A_PROVIDER_SHADOW_DELTA_R1`
4. `P07_I4B_SURFACE_INTERFACE_DELTA_R1`
5. `P07_I4D_SURFACE_REALIZATION_MODE_DELTA_R1`
6. `P07_I4H_RUNTIME_RECOVERY_R3_DELTA_R1`

Logical master reconstructions remain intact:
- B Research Master: bytes `77347512`, SHA256 `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0`, PASS.
- C Narrative Master: bytes `204167926`, SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`, PASS.
- D / DB59: bytes `259756521`, SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`, PASS.

## 4. Exact-parent recovery execution and scientific boundary

The historical missing `tests/test_p07_i4h_runtime_promotion.py` body was not fabricated and historical `42/42` / `26/26` labels were not reused as a fresh rerun claim.

Exact Sync R6 active I4D materialization was independently reconstructed first:
- baseline full nonhistorical regression `213/213 PASS`;
- five frozen I4D runtime files `5/5` byte-identical.

Recovery Qualification R2 on the exact parent produced:
- `44/45 PASS`, `1 FAIL` -> **HOLD**.

The failure was integration-order specific: episode-level I4H wiring attempted the first scene bridge before prevalidating that every scene in the frozen episode had an intervention profile. The R2 HOLD is preserved and was not rewritten as a PASS.

A corrective R3 was preregistered after the R2 failure and before the patch. Authorized code change was limited to:
`literary_os_runtime/i4h_episode_render_wiring.py`

Correction: perform deterministic whole-episode profile completeness preflight before any bridge/provider call. No selector rule, I4H renderer rule, frozen I4D file, R2 test body, Production, formal state, R140 or I4I state was changed.

Corrected file SHA256:
`f90a6cdc699f0c6dd5631af8283c6c97a75dd2ad9ed28d7e6ef83908815f9727`

Recovery R3 results:
- new Recovery tests: `45/45 PASS`;
- deterministic parent-targeted regression: `56/56 PASS` across the preregistered discovery rule;
- full nonhistorical regression: `258/258 PASS`;
- critical failure accepts: `0`;
- Python literary prose generated: `false`.

An independent second-pass verifier then rejoined final C2, rematerialized the final active runtime from the six-stage overlay chain, rechecked five frozen I4D hashes, rechecked all package ZIP safety/CRC, rechecked B/C/D logical master reconstruction and reran the final full regression: `258/258 PASS`.

## 5. Failure root cause and operational fix

Sync R6 package corruption was ruled out by direct 9/9 outer SHA/size/CRC/path-safety verification and B/C/D logical reconstructions.

Four distinct operational defects were identified:
1. Prior session execution transport instability (`TransportTimeoutError` / `ClientError`) was outside the Literary OS package bytes. In the recovered session a related generated-file durability boundary failure was reproduced as `GeneratedFileUploadError` after local filesystem work had actually completed. This supports a platform/tool transport layer failure class, while not proving every historical timeout had the identical internal cause.
2. The container has a hard cgroup memory limit of 4 GiB and zero swap. Large sequential archive reads filled cgroup page cache and hit `memory.events max`, although `oom=0` and `oom_kill=0`. Resolution: streaming I/O, `/tmp` intermediates, staged cache release with `POSIX_FADV_DONTNEED`, and final-only movement to `/mnt/data`.
3. The Hub Recovery Builder R1 assumed the exact Sync R6 C2 archive extracted directly to a root `literary_os_runtime/` project. Exact C2 is instead a multi-overlay archive. Resolution: materialize by the frozen six-stage overlay order above.
4. Exact-parent R2 exposed a fail-closed episode wiring ordering defect not visible in stubbed-parent preflight. Resolution: R3 whole-episode profile prevalidation before any bridge/provider call.

Final runtime state after delivery verification remained healthy: no OOM, no OOM-kill, and final SHA256SUMS verification passed for all nine packages plus audit/independent-verification sidecars.

## 6. Current claim boundary and next step

Supported current claim:
`P07-I4H Development/Preformal physical recovery is complete and developer-delivered as a freshly audited 5-Part / 9-Package authority.`

Not supported:
- Production promotion;
- formal-count increment;
- R140 execution/result;
- I4I execution/result;
- OpenAI Live qualification;
- independent-human validation;
- human-writer equivalence;
- exact historical Sync R8 byte reproduction;
- exact rerun of the missing historical 42-test body.

I4I remains later and unexecuted. Do not convert any previously session-only I4I planning into an execution result. Any subsequent I4I work must start from this recovered I4H physical authority plus the already frozen Hub I4I preregistration/plan evidence.

## STATUS TOKEN
`I4H_RECOVERY_R3_DEVELOPER_DELIVERED__SYNC_R6_9_OF_9_PARENT_VERIFIED__I4D_BASELINE_213_213__R2_EXACT_PARENT_HOLD_44_45__R3_45_45__TARGETED_56_56__FULL_258_258__FINAL_C2_58D28ECC__PACKAGE_SET_9327630E__B_C_D_LOGICAL_PASS__DB59_FROZEN__PRODUCTION_R47__FORMAL_137__R140_0_0_0__I4I_0_0_0_0`
