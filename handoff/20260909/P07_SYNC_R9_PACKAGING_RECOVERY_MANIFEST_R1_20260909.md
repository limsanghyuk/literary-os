# P07 Sync R9 Packaging Recovery Manifest R1

Date: 2026-09-09
Classification: RECOVERY / PACKAGING / NO NEW RESEARCH EXECUTION

## 0. Purpose
This manifest makes the post-Sync-R8 research state reproducible in a fresh session and defines exactly how to rebuild the next developer-deliverable 5-Part / 9-transport-file package set once a healthy writable runtime is available.

This document does **not** claim that Sync R9 already exists.

## 1. Recovery verdict
Two different recovery claims must be separated:

1. **Research-state recovery from GitHub Hub alone: YES.**
   The full post-Sync-R8 I4I preregistration and common plan freeze are durable in this repository and can be read/reconstructed without the prior chat session.
2. **Exact physical 5-Part / 9-Package regeneration from Hub alone: NO.**
   The repository does not contain the nine large Sync R8 transport binaries themselves. It contains their names, hashes, authority manifests, physical audit, runtime source deltas and post-Sync-R8 research evidence. A healthy packaging session must also mount an exact copy of the Sync R8 nine-file physical set (or an equivalent byte-identical developer-held copy).

Therefore the sufficient recovery input is:
`HEALTHY WRITABLE RUNTIME + EXACT SYNC R8 9 TRANSPORT FILES + THIS GITHUB HUB`.

With those three inputs, Sync R9 can be built without relying on chat-only memory.

## 2. Exact parent physical authority — Sync R8
Authority:
`LITERARY_OS_SYNC_R8_I4H_RUNTIME_PROMOTION_20260909`

Package-set material SHA256:
`4e93e545c670d9672b4c4a8e943df9d4a02702a1de707916cb6274d0a145712d`

Final physical audit SHA256:
`2be6d7cc124cf194adee8a5733b06d578c2a4df4339cc3153547aa4601f2b345`

Combined C2:
- bytes `318364190`
- entries `3771`
- SHA256 `eb49afacc0ef0377fc619e33c01603fe69ffcdc7d242a041a5a1d2c26c0d3ef0`
- CRC PASS
- duplicate paths 0
- unsafe paths 0

Frozen DB59 SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

### Required parent transport files and hashes
1. CONTROL
   `LITERARY_OS_CURRENT_CONTROL_P07_I4H_RUNTIME_PROMOTION_SYNC_R8_20260909.zip`
   SHA256 `ddee74d5c5ebd5fcc83e3138a3f649d98114ef9d6c9ed45e17e09818b26b856c`
2. PART A
   `LITERARY_OS_CURRENT_PART_A_P07_I4H_RUNTIME_PROMOTION_SYNC_R8_20260909.zip`
   SHA256 `f8d50abe9fec7580b1f2c37d41ccbe35ec71cba28eecf40b3c894148f396d76b`
3. PART B1
   `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_20260908.zip`
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. PART B2
   `LITERARY_OS_CURRENT_PART_B2_P07_I4H_RUNTIME_PROMOTION_SYNC_R8_20260909.zip`
   SHA256 `c80b2f389846e56250f9fd856dd3e7c4e25183da8cee9228d686046bd2e74248`
5. PART C1
   `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_20260908.zip`
   SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. PART C2-A
   `LITERARY_OS_CURRENT_C2_BINARY_A_P07_I4H_RUNTIME_PROMOTION_SYNC_R8_20260909.bin`
   SHA256 `d06d40bbf5aacebfffb94969b8640674809d818eee727bd82987e7e1d70919a4`
7. PART C2-B
   `LITERARY_OS_CURRENT_C2_BINARY_B_P07_I4H_RUNTIME_PROMOTION_SYNC_R8_20260909.bin`
   SHA256 `493c5b9368f7310b17d8e66a6f883c13caa8ff93ec40c9ae79c9ace24cb9f2bf`
8. PART D1
   `LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_20260908.zip`
   SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. PART D2
   `LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_20260908.zip`
   SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

If any parent file hash does not match, STOP. Do not rebuild R9 from a non-authority parent.

## 3. Active engine state that must be preserved
Active Development Engine:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_R1`

Physical closure commit:
`2af29e335789aee7b72461d3bac3323cb79d6805`

Runtime qualification result commit:
`8fa611b801118ecf2b703cf1f41288c6a7e84bcc`

Runtime contract:
- exact I4D baseline is Pass 1;
- ABSTAIN = baseline unchanged;
- LOW/STANDARD = at most one revision candidate;
- every candidate requires deterministic + external reliability + craft PASS;
- every failure/non-PASS falls back to exact baseline;
- Python authors no literary prose.

Qualification remains:
- I4H new tests 42/42 PASS;
- old targeted 26/26 PASS;
- full nonhistorical 255/255 PASS;
- parent I4D files 5/5 byte-identical;
- critical failure accepts 0.

No post-Sync-R8 runtime code change exists. Therefore C1/C2 runtime payload must remain byte-identical to Sync R8 in Sync R9.

## 4. Complete post-Sync-R8 research delta durable on Hub
No Control/Treatment episode or score was produced after Sync R8. The only valid post-Sync-R8 research delta is I4I preregistration + common-plan freeze + interruption/packaging-recovery metadata.

### I4I preregistration
Path:
`handoff/20260909/P07_I4I_WHOLE_EPISODE_PAIRED_RERENDER_PREREG_R1_20260909.json`
Commit:
`e4bb3a9571db87c7553b183c8a39c3bdb498a143`

### Fresh Series State + Episode Synopsis freeze
Path:
`handoff/20260909/P07_I4I_SERIES_STATE_AND_EPISODE_SYNOPSIS_FREEZE_R1_20260909.json`
Commit:
`623a57f04684c3729b2a12e117db9fc8982c0bd2`

### 11-Sequence Plan freeze
Path:
`handoff/20260909/P07_I4I_SEQUENCE_PLAN_FREEZE_R1_20260909.json`
Commit:
`234cda5bca761002a6b4d01a988cb0ce345e2426`

### SC01-SC56 Scene Plan freeze
Path:
`handoff/20260909/P07_I4I_SCENE_PLAN_SC01_SC56_FREEZE_R1_20260909.json`
Commit:
`72109d52d69ba5aacafde3e5a6e660bd587c45a1`

### Complete Plan Freeze Manifest
Path:
`handoff/20260909/P07_I4I_COMPLETE_PLAN_FREEZE_MANIFEST_R1_20260909.json`
Commit:
`ba658c7ede8de40bac6e4aaabdc325115ce8a82e`

### Plan-freeze interruption checkpoint
Path:
`handoff/20260909/P07_I4I_PLAN_FREEZE_CHECKPOINT_R1_20260909.md`
Commit:
`b4ec59a91a894f05131a19167db49c41776cf3a3`

### I4I current recovery START_HERE
Path:
`handoff/20260909/START_HERE_P07_I4I_PLAN_FROZEN_RUNTIME_INTERRUPTION_R1.md`
Commit:
`eddd3f823a31ca6fc87c8622b324abdf491ba9d2`

### Post-Sync-R8 packaging blocker checkpoint
Path:
`handoff/20260909/P07_POST_SYNC_R8_PACKAGING_BLOCKER_CHECKPOINT_R1_20260909.md`
Commit:
`3e9ae77479b163d00dff2aa2084d45d59fdb2b56`

### Packaging-blocked START_HERE
Path:
`handoff/20260909/START_HERE_P07_SYNC_R8_LAST_PHYSICAL_AUTHORITY_PACKAGING_BLOCKED_R1.md`
Commit:
`a3e508493315c0fe0fdb63f813bac6f98882a033`

Current scientific state of I4I:
- preregistration SEALED;
- fresh source-free series/episode state SEALED;
- 11 sequences SEALED;
- 56 scenes SEALED;
- Control outputs 0;
- I4H selector decisions 0;
- Treatment outputs 0;
- blind scores 0;
- no I4I PASS/HOLD/FAIL result;
- formal delta 0.

## 5. Exact Sync R9 logical change map
Sync R9 is a **research synchronization package**, not a runtime promotion package.

### Files that MUST change
1. CONTROL
   - add Sync R9 authority/delivery manifest;
   - add current research-status pointer;
   - include exact nine-file peer hashes after build;
   - state Active I4H unchanged and I4I plan-frozen/no outputs.
2. PART A
   - append the valid post-Sync-R8 I4I preregistration and plan-freeze evidence listed in Section 4;
   - append Sync R9 authority/recovery metadata.
3. PART B2
   - append the same post-Sync-R8 research/recovery evidence into the cumulative Research Master / recovery side of the package;
   - append Sync R9 research-status metadata.

### Files that MUST remain byte-identical to Sync R8
4. PART B1
5. PART C1
6. PART C2-A
7. PART C2-B
8. PART D1
9. PART D2

Reason:
- no post-Sync-R8 runtime implementation change;
- no DB59 change;
- no new C2 engine delta;
- no change to Production ENG:R47.

Therefore in Sync R9:
- combined C2 MUST still reconstruct to SHA256 `eb49afacc0ef0377fc619e33c01603fe69ffcdc7d242a041a5a1d2c26c0d3ef0`;
- DB59 MUST still reconstruct to SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## 6. Safe rebuild method
Do not fully extract the large parent packages.

Recommended procedure:
1. Verify all nine Sync R8 outer SHA256 values first.
2. Verify parent ZIP CRC / duplicate path 0 / unsafe path 0.
3. Copy unchanged B1/C1/C2-A/C2-B/D1/D2 byte-for-byte into a fresh Sync R9 output directory.
4. Copy CONTROL/A/B2 to fresh names and append only new, unique Sync R9 evidence paths. Never overwrite an existing path inside a ZIP and never create duplicate entries.
5. Use a fixed ZIP timestamp for newly appended small evidence entries so the new package is reproducible within the build run.
6. Recompute new outer SHA256 for CONTROL/A/B2.
7. Recompute all nine outer SHA256 values and create the new Delivery Manifest.
8. Reopen modified ZIPs and run full CRC / duplicate / unsafe-path audit.
9. Reconstruct C2-A+B logically and verify the unchanged combined C2 SHA/bytes/entries/CRC.
10. Reconstruct DB59 from D1+D2 and verify frozen DB59 SHA/member count.
11. Compute Sync R9 package-set material SHA256.
12. Write `LITERARY_OS_SYNC_R9_I4I_PLAN_FREEZE_FINAL_PHYSICAL_AUDIT_R1_20260909.json`.
13. Only after every audit passes may Hub authority move from Sync R8 to Sync R9.
14. Deliver all nine physical files to the developer.

## 7. Required Sync R9 claim boundary
Sync R9 may claim only:
- post-Sync-R8 I4I preregistration and complete 11-sequence/56-scene common plan are physically synchronized;
- Active Development Engine remains P07-I4H;
- Production remains ENG:R47;
- DB59 unchanged;
- Formal scored count remains 137;
- R140 remains 0/0/0;
- I4I Control/Treatment/scores remain 0.

Sync R9 must NOT claim:
- I4I execution;
- I4I whole-episode craft PASS/HOLD/FAIL;
- OpenAI Live validation;
- independent-human validation;
- Production promotion;
- formal-count change.

## 8. Exact post-R9 continuation
Only after developer-deliverable Sync R9 5-Part / 9-Package audit PASS:
1. fetch the physically synchronized I4I plan from R9;
2. generate exact I4D Control once;
3. require >=35,000 Unicode characters and exact SC01-SC56 order/membership;
4. seal Control scene hashes + whole-episode hash;
5. only then profile/freeze I4H ABSTAIN/LOW/STANDARD;
6. generate/seal Treatment;
7. blind-evaluate according to preregistration.

## 9. Recovery sufficiency test
A fresh session is ready to rebuild Sync R9 only if all are true:
- GitHub Hub readable;
- this manifest readable;
- exact Sync R8 nine-file set mounted;
- all nine Sync R8 outer SHA256 values PASS;
- writable container `/tmp` probe PASS;
- writable output-directory probe PASS;
- tiny ZIP create/read/CRC probe PASS.

If any item fails: do not execute new research and do not claim physical synchronization.

## STATUS TOKEN
`SYNC_R9_RECOVERY_MANIFEST_COMPLETE__HUB_RESEARCH_STATE_RECOVERABLE__SYNC_R8_BINARIES_REQUIRED__CONTROL_A_B2_CHANGE__B1_C1_C2A_C2B_D1_D2_BYTE_IDENTICAL__NO_NEW_RESEARCH_UNTIL_R9_PHYSICAL_AUDIT_PASS`
