# R74 Input Custody / Runtime Access Audit R1

Date: 2026-09-22

Status:
`INPUT_CUSTODY_PRESENT__CONTENT_ACCESS_HOLD__NO_SCIENTIFIC_OUTPUT`

## Root cause
Repeated `TransportTimeoutError` occurs on:
- minimal container health commands;
- Python runtime access;
- prior broad filesystem operations.

The error is therefore classified as an infrastructure/runtime-access failure, not an R74 scientific failure and not evidence of DB64 corruption.

## DB64 custody
Conversation file catalog directly shows both original DB64 R127 split uploads:
- `DB64_POST_R127_HANSEONG_FULL_PIPELINE_INDEPENDENT_THICK_R1_20260921_FINAL_SEALED.zip.part01`
  - size: 141,779,367 bytes
  - expected SHA256: `b033ebf5c00c844634a8180812382d68657d59fd98643d45e8470314ca5994e3`
- `DB64_POST_R127_HANSEONG_FULL_PIPELINE_INDEPENDENT_THICK_R1_20260921_FINAL_SEALED.zip.part02`
  - size: 141,779,367 bytes
  - expected SHA256: `a618f48503afb5b5465f49264259302e4e3c90434ede6ea4c99be700cd4f1785`

Expected logical DB64:
- size: 283,558,734 bytes
- SHA256: `4703e9a99da2deb66eef08f09b08141db6c4d19bc76f77d1c8159dcb7633d6e7`

The files exist in custody. The current blocker is content access/extraction.

## Why Files materialize cannot solve it
Each DB64 split is >100 MiB, exceeding the current Files materialize per-file limit.
The 9MB analysis-only DB64 bundle is accessible as an archive but its internal contents are not text-indexed by Files search.

## R74 scientific consequence
Do NOT:
- generate substitute inputs;
- use R73's asymmetric Stage-B score as R74 evidence;
- call the 17 R73 Control-only cases a fully fresh efficacy set;
- replace unavailable cases after Treatment output.

Current R74:
- preregistered;
- shared semantic representation contract frozen;
- measurement bridge implementation frozen;
- Stage M not executed;
- primary cases not frozen;
- Control/Treatment primary outputs = 0.

## Resume gate
When runtime access is healthy:
1. verify DB64 part01/part02 hashes;
2. reconstruct logical DB64 and verify logical SHA;
3. run R74 Stage M;
4. enumerate fully fresh cases under frozen exclusions;
5. freeze exactly 24 cases before Treatment output;
6. execute symmetric paired experiment.

Physical Authority remains SYNC-R72 until an audited successor package reseal is possible.
