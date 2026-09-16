# RUNTIME / CONTAINER / HUB AUTHORITY SYNC GATE R6

Date: 2026-09-16
Project: Literary OS Development
Classification: **MANDATORY AUTHORITY-SYNC PRECHECK**
Parent execution rules: R5 Turn-Bounded Execution + R4 Atomic Execution.

## Root cause addressed
A later research turn loaded a stale local R1 UL-16 runtime from `/mnt/data` even though the Hub CURRENT pointer had already advanced to canonical UL-16 R2. The local filename existed, but local container bytes do not automatically synchronize with Hub/Library research authority.

This created an authority-desynchronization hazard:

`HUB CURRENT = UL16 R2` while `LOCAL WORKING BYTES = UL16 R1`.

The resulting local replay was therefore non-authoritative regardless of whether its internal tests passed.

## Mandatory precheck before every Candidate research execution
1. Fetch `handoff/CURRENT_NEXT_RESEARCH_POINTER.md` by exact path.
2. Resolve the canonical research package filename and SHA256 named by that pointer/receipt.
3. Locate candidate bytes in the active runtime.
4. Compute local SHA256 before import/execution.
5. Require exact equality with the Hub canonical SHA.
6. If local bytes are absent or mismatched, do **not** substitute an older package with a similar filename.
7. Attempt materialization from the exact persistent Library file ID/path when available.
8. Recompute SHA256 and ZIP integrity after materialization.
9. If canonical bytes cannot be obtained, enter `AUTHORITY_BYTES_UNAVAILABLE_HOLD` and stop research execution.

A filename is never sufficient authority evidence.

## Stale-artifact rule
Any locally generated package derived from superseded bytes must be renamed/quarantined with `STALE_*_NONAUTHORITATIVE` in both container and Library surfaces. It must never be referenced by CURRENT pointers.

## Current incident closure
Canonical Hub UL-16 R2 research runtime:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`

Canonical SHA256:
`7f71484cd2687262d18104b3a9a5cfe727d003d7ed4b616ce8d64702b2da2ca8`

Canonical Library file was materialized into the active container as:
`/mnt/data/LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_CANONICAL_20260916.zip`

Verification:
- size: `18,681,762` bytes;
- SHA256: exact canonical match;
- ZIP CRC: PASS;
- current transaction `memory.events max` delta: 0;
- OOM/OOM-kill: 0.

## Authority boundary
No Production/physical/DB/Formal authority change.

Current physical authority remains SYNC-R53; Production remains ENG:R47; Candidate Base authority remains P07-I4H Recovery R3; DB runtime authority remains DB59 frozen.

## Status token
`R6__AUTHORITY_SYNC_GATE__HUB_POINTER_SHA_MUST_MATCH_LOCAL_BYTES_BEFORE_EXECUTION__STALE_LOCAL_SUBSTITUTION_FORBIDDEN__CANONICAL_UL16_R2_REMATERIALIZED_AND_VERIFIED__NO_AUTHORITY_CHANGE`
