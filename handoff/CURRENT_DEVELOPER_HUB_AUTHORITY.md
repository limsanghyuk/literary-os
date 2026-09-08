# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-09

## CURRENT PHYSICAL PACKAGE AUTHORITY
`LITERARY_OS_SYNC_R8_I4H_RUNTIME_PROMOTION_20260909`
This remains the latest physically closed developer-deliverable **5 Parts / 9 transport files** authority.

Package-set material SHA256:
`4e93e545c670d9672b4c4a8e943df9d4a02702a1de707916cb6274d0a145712d`

Final physical audit SHA256:
`2be6d7cc124cf194adee8a5733b06d578c2a4df4339cc3153547aa4601f2b345` — PASS.

Combined C2 SHA256:
`eb49afacc0ef0377fc619e33c01603fe69ffcdc7d242a041a5a1d2c26c0d3ef0`

DB59 frozen SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## CURRENT ACTIVE ENGINE AUTHORITY
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_R1`
Active Development Engine = **P07-I4H**.
Production remains `ENG:R47`.
Formal scored count remains `137`.
Formal R140 remains `0/0/0`.

## SYNC R9 PACKAGING RECOVERY AUTHORITY
Mandatory recovery document:
`handoff/20260909/P07_SYNC_R9_PACKAGING_RECOVERY_MANIFEST_R1_20260909.md`
Commit `31931895de1bb0504bf19366d655ca64adb36560`.

This document is the authoritative reconstruction recipe for the next physical package set.

Recovery sufficiency is explicitly split:
- **Research-state recovery from Hub alone: YES.** All post-Sync-R8 valid research state is durable on GitHub.
- **Exact physical 9-file recreation from Hub alone: NO.** The GitHub repository is not a byte backup of the nine large Sync R8 transport binaries.
- **Physical Sync R9 rebuild: YES**, when a fresh session has all three inputs:
  1. a healthy writable runtime;
  2. an exact byte-identical Sync R8 nine-file set whose nine outer hashes match the recovery manifest;
  3. this GitHub Hub.

Once those inputs exist, no prior chat-only state is required for the Sync R9 build.

## POST-SYNC-R8 RESEARCH STATUS
I4I has been preregistered and its complete common plan is durable on GitHub:
- preregistration `e4bb3a9571db87c7553b183c8a39c3bdb498a143`
- series/synopsis freeze `623a57f04684c3729b2a12e117db9fc8982c0bd2`
- sequence-plan freeze `234cda5bca761002a6b4d01a988cb0ce345e2426`
- SC01-SC56 freeze `72109d52d69ba5aacafde3e5a6e660bd587c45a1`
- complete plan manifest `ba658c7ede8de40bac6e4aaabdc325115ce8a82e`
- plan-freeze checkpoint `b4ec59a91a894f05131a19167db49c41776cf3a3`

This material is **NOT yet physically synchronized** into a newer 5-Part / 9-Package set and must not outrank Sync R8 physical authority.

I4I execution remains:
- Control outputs 0;
- selector decisions 0;
- Treatment outputs 0;
- scores 0;
- no I4I PASS/HOLD/FAIL result.

## SYNC R9 EXACT TRANSPORT CHANGE MAP
When rebuilding Sync R9 from exact Sync R8 parent files:

Must change:
- CONTROL
- PART A
- PART B2

Must remain byte-identical to Sync R8:
- PART B1
- PART C1
- PART C2-A
- PART C2-B
- PART D1
- PART D2

There is no post-Sync-R8 runtime or DB59 code/data change.
Therefore combined C2 must remain:
`eb49afacc0ef0377fc619e33c01603fe69ffcdc7d242a041a5a1d2c26c0d3ef0`

DB59 must remain:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

The complete filenames, parent SHA256 values, append-only evidence list and audit procedure are frozen in the Sync R9 Packaging Recovery Manifest.

## PACKAGING BLOCKER
Current-session diagnostics:
- minimal container read/write + tiny-ZIP probe -> `ClientError`;
- separate Python filesystem + tiny-ZIP + SHA256 probe -> `ClientError`.

Therefore reliable package creation, CRC checking, SHA closure, C2 rebuild and final 9/9 physical audit are currently unavailable in this session.

Packaging blocker checkpoint:
`handoff/20260909/P07_POST_SYNC_R8_PACKAGING_BLOCKER_CHECKPOINT_R1_20260909.md`
Commit `3e9ae77479b163d00dff2aa2084d45d59fdb2b56`.

## HARD RESEARCH FREEZE
No further I4I generation, Treatment, scoring or subsequent research experiment may execute until post-Sync-R8 material has been incorporated into a newly built and fully audited physical package set.

The next package authority must be **Sync R9**.

## NEXT EXACT OPERATION
1. Start only in a healthy writable runtime.
2. Mount exact Sync R8 9-file physical inputs.
3. Verify all nine outer SHA256 values against `P07_SYNC_R9_PACKAGING_RECOVERY_MANIFEST_R1_20260909.md`.
4. Revalidate Sync R8 CRC / duplicate-path / unsafe-path integrity.
5. Copy B1/C1/C2-A/C2-B/D1/D2 byte-identically.
6. Build new CONTROL/A/B2 by append-only integration of the exact durable post-Sync-R8 evidence from Hub.
7. Audit Sync R9: all nine outer hashes, ZIP CRC, duplicate=0, unsafe=0, manifests, unchanged combined C2, unchanged DB59, package-set material hash.
8. Write the final Sync R9 physical audit.
9. Deliver all nine Sync R9 files to the developer.
10. Only after developer-deliverable Sync R9 closure may I4I Control generation resume.

## CLAIM BOUNDARY
- Sync R9 does not yet exist.
- Hub fully preserves the current research and exact rebuild recipe, but does not by itself contain the parent large transport bytes.
- Latest physically closed authority = Sync R8.
- No Production, formal-count, R140, OpenAI Live or I4I-result change.

## STATUS TOKEN
`DEVELOPER_HUB__SYNC_R8_LAST_PHYSICAL_AUTHORITY__SYNC_R9_RECOVERY_MANIFEST_COMPLETE__HUB_RESEARCH_STATE_RECOVERABLE__SYNC_R8_9_BINARIES_REQUIRED_FOR_PHYSICAL_REBUILD__RESEARCH_FROZEN__FORMAL_137__R140_0_0_0`
