# P07 FILE LIBRARY ARCHIVE / MOUNT RECOVERY INDEX R1

Date: 2026-09-09
Purpose: make new-session recovery independent of chat-memory limits while preserving the distinction between stored package metadata and byte-level runtime access.

## 0. CORE FINDING
The developer previously supplied a complete 5-Part / 9-Package physical package set. The authoritative developer-held baseline remains:

`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`

File Library search can recover durable physical metadata/evidence for the package family (filenames, sizes, SHA256, C2 reconstruction rules, audit/trust-root records, research authority records), but in the current session the large ZIP/BIN package objects are not exposed as mounted byte files inside the active runtime `/mnt/data`.

This must NOT be interpreted as proof that the package objects were deleted from File Library. The correct classification is:

`ARCHIVE_METADATA_DISCOVERABLE__LARGE_BINARY_RUNTIME_MOUNT_NOT_EXPOSED_IN_CURRENT_SESSION`

## 1. DEVELOPER-HELD PHYSICAL BASELINE — SYNC R6
Logical structure: 5 Parts / 9 transport files.

1. CONTROL — `LITERARY_OS_CURRENT_CONTROL_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
   SHA256 `c291e9a3866de66fae625ab899139a13f1e98468a3bff0d58a11fd34553f0aa6`
2. PART A — `LITERARY_OS_CURRENT_PART_A_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
   SHA256 `25eb489d07e78a3a3288e1e5029114ce791ada2ab43a8564ae9f9eed738306dd`
3. PART B1 — `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_20260908.zip`
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. PART B2 — `LITERARY_OS_CURRENT_PART_B2_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
   SHA256 `40de0853fd8e1e8318658d64a4e8d26cb8e88711842639aa45b87c0e4d062c02`
5. PART C1 — `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_20260908.zip`
   SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. PART C2-A — `LITERARY_OS_CURRENT_C2_BINARY_A_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin`
   SHA256 `b775bf65cba23ad5611b3383678765f88c1a444d25c4b49f7ccfb5a9d2438ec9`
7. PART C2-B — `LITERARY_OS_CURRENT_C2_BINARY_B_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin`
   SHA256 `be4af1ac97467e1f090c8cd0854e14df1ffef6699ed23b0a80014f55e197e860`
8. PART D1 — `LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_20260908.zip`
   SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. PART D2 — `LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_20260908.zip`
   SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Combined Sync R6 C2:
- bytes `318351029`
- SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`
- entries `3765`
- CRC PASS

Sync R6 delivered physical audit:
`LITERARY_OS_SYNC_R6_I4H_FINAL_PHYSICAL_AUDIT_R1_20260908.json`
SHA256 `94e808f6fa7c760662d0d02d1625046d23a9198afcc28bd3ab18c15453b37360`

DB59 frozen SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## 2. FILE LIBRARY EVIDENCE RECOVERABLE IN NEW SESSIONS
File Library currently returns indexed physical-authority evidence for P07-I4D / research synchronization including:
- `READ_FIRST_CURRENT_PHYSICAL_RESEARCH_AUTHORITY_P07_I4D_SYNC_R2.md`
- `CURRENT_PHYSICAL_RESEARCH_AUTHORITY_MANIFEST_P07_I4D_SYNC_R2.json`
- `CURRENT_PHYSICAL_RESEARCH_AUTHORITY_TRUST_ROOT_P07_I4D_SYNC_R2.json`
- `P07_I4D_CUMULATIVE_RESEARCH_SYNC_PHYSICAL_AUDIT_R2.json`
- `P07_I4D_CUMULATIVE_RESEARCH_SYNC_POST_SIDECAR_AUDIT_R2.json`
- `CURRENT_PHYSICAL_AUTHORITY_MANIFEST_P07_I4D_R1.json`
- `P07_I4D_PHYSICAL_AUDIT_R1.json`
- CT independent inspection / Live diagnostic reports from 2026-09-08.

These records demonstrate that the archive/search layer preserves detailed physical metadata and audit evidence even when the binary bodies are not mounted into the active runtime.

## 3. STORAGE VS SEARCH VS RUNTIME
Operationally distinguish three layers:

1. **Archive/File Library storage** — long-lived uploaded-file storage / archive reference.
2. **File Search index** — searchable extraction and metadata used to rediscover prior files/evidence across sessions.
3. **Active Runtime/Container** — byte-addressable filesystem required for ZIP mutation, C2 concatenation/splitting, CRC, SHA256 and new package construction.

A file may be discoverable through layer 2 without its complete binary body being materialized in layer 3.

No future session may infer `deleted` merely because a large ZIP/BIN body is absent from `/mnt/data`.

## 4. WHAT HUB CAN RECOVER WITHOUT RE-UPLOAD
GitHub Hub is sufficient to recover:
- current scientific/research state;
- exact developer-held physical authority identity;
- exact 9 filenames and frozen outer SHA256 values;
- C2 reconstruction target and SHA256;
- DB59 frozen identity;
- which packages are expected byte-identical;
- cumulative post-Sync-R6 research deltas;
- I4H R3/R4 results;
- I4H runtime source and qualification result;
- I4I preregistration and 11-sequence / 56-scene frozen plan;
- Sync R9 rebuild recipe and claim boundaries.

Therefore a new session does NOT need the developer to re-explain the research history or re-upload packages merely so the assistant can understand authority/state.

## 5. WHAT HUB CANNOT RECREATE FROM METADATA ALONE
Metadata/hashes do not reconstruct the original 1GB+ package byte streams.

For byte-level mutation into Sync R9, the active runtime must obtain exact Sync R6 package bytes from one of:
- a File Library binary mount/export path;
- a developer-controlled persistent artifact store;
- another byte-preserving archive reachable by the execution environment;
- as a last resort, re-upload by the developer.

The last option is a fallback, not the intended normal workflow.

## 6. CURRENT SESSION RUNTIME STATUS
The prior session recorded `ClientError` for filesystem/ZIP operations.
In the current session, a real writable-runtime probe successfully created a ZIP, reopened it, validated CRC/readability and computed SHA256.

Therefore:
`RUNTIME_WRITE_ZIP_SHA_CAPABILITY = RECOVERED`

Remaining physical blocker:
`SYNC_R6_LARGE_BINARY_BYTES_NOT_MOUNTED_TO_ACTIVE_RUNTIME`

## 7. SYNC R9 CUMULATIVE REBUILD RULE
Next physical package set remains Sync R9, built directly from exact developer-held Sync R6 + cumulative Hub deltas.

Rebuild/change:
- CONTROL
- PART A
- PART B2
- PART C2-A / C2-B after recombining exact Sync R6 C2 and applying qualified I4H runtime overlay/evidence

Expected byte-identical unless packaging audit proves otherwise:
- PART B1
- PART C1
- PART D1
- PART D2

Do not use session-internal Sync R7/R8 as required physical parents.

## 8. HARD INTEGRITY RULE
Before any physical promotion:
1. Obtain exact 9 Sync R6 byte files.
2. Verify all 9 frozen outer SHA256 values.
3. ZIP CRC PASS where applicable; duplicate paths = 0; unsafe paths = 0.
4. Rejoin C2-A + C2-B; verify bytes/SHA256/entry count above.
5. Apply only Hub-qualified cumulative deltas.
6. Re-run I4H qualification/regression against rebuilt materialization.
7. Audit all 9 Sync R9 files and DB59 reconstruction.
8. Deliver all 9 files to developer.
9. Only then change developer-held physical authority.

## 9. NEW-SESSION RECOVERY RULE
A new session should first read:
1. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`
2. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
3. this file
4. `handoff/20260909/P07_DEVELOPER_DELIVERY_BASELINE_CORRECTION_AND_CUMULATIVE_RECOVERY_R1_20260909.md`

Then query File Library for the physical authority manifest/audit records. Do not ask the developer to re-explain already-durable history.

Only request re-upload of binary packages if the task actually requires byte-level mutation and no archive-to-runtime binary access path is available.

## 10. CLAIM BOUNDARY
This document does NOT claim that File Library deleted or retained every original binary body; the current search interface cannot prove either condition.
It DOES record that physical metadata/evidence is discoverable across sessions while direct runtime binary mounting is not currently exposed.

Production remains `ENG:R47`.
Formal scored count remains `137`.
Formal R140 remains `0/0/0`.

## STATUS TOKEN
`FILE_LIBRARY_ARCHIVE_METADATA_RECOVERABLE__SYNC_R6_PHYSICAL_IDENTITY_DURABLE_ON_HUB__RUNTIME_HEALTHY__LARGE_BINARY_MOUNT_UNRESOLVED__NO_REPEAT_REEXPLANATION_REQUIRED__SYNC_R9_BYTE_REBUILD_REQUIRES_EXACT_SYNC_R6_BYTES`
