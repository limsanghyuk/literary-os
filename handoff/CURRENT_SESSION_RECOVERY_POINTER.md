# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-20

## RECOVERY ENTRY POINT
`handoff/20260920/START_HERE_POST_R62_NEW_SESSION_RECOVERY_FROM_SYNC_R59_R1.md`

## PHYSICAL BASELINE
Developer-held last complete physical set:
**SYNC-R59**

Read order:
`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

Important:
B2 must use corrected R2 transport SHA:
`753db03b5c161d3c016ef95388f93e2dfe2c469d2e1eb6182429b3d16cd549e6`

## CURRENT SCIENTIFIC AUTHORITY
- SYNC-R59: QUARANTINED failed research snapshot
- active qualified Candidate: SYNC-R58 / ADAPTIVE_UL16
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64

## RESEARCH STATE
- R59 CLOSED HOLD
- R60 CLOSED PASS
- R61 CLOSED
- R62 CLOSED FAIL 9W / 0T / 3L
- R63 NOT STARTED

## WHY A PHYSICAL ALIGNMENT IS REQUIRED
SYNC-R59 was physically sealed before the R62 external blind gate closed.

After sealing:
- 3 judge results arrived;
- R62 failed;
- SYNC-R59 was quarantined;
- active qualified Candidate reverted/remained SYNC-R58.

No new runtime code was accepted after SYNC-R59.

Therefore the missing physical update is authority/research alignment, not an unknown source patch.

## FIRST ACTIONS IN A HEALTHY NEW SESSION

### 0. Runtime health
Verify minimal command execution and /mnt/data read/write.

If unhealthy:
`RUNTIME_TRANSPORT_HOLD`

### 1. Verify SYNC-R59
Use hashes and bindings in:
`handoff/20260920/POST_SYNC_R59_PHYSICAL_RECOVERY_RESEAL_PLAN_R1.md`

Any mismatch:
`AUTHORITY_BYTES_UNAVAILABLE_HOLD`

### 2. Load Hub overlay
Read:
- session research ledger
- R62 judge custody matrix
- R62 final external-blind result
- Current pointers

### 3. Build recovery-aligned successor
Before R63:
- preserve R59/R62 runtime as quarantined evidence;
- active executable binding = exact SYNC-R58 qualified runtime;
- include R59-R62 session research history;
- include R62 FAIL/quarantine state;
- rebuild C1/C2 as required;
- preserve DB59;
- full 9-package reseal and audit.

### 4. Deliver all 9 packages
Recovery is not complete until the developer has the newly aligned 9-package set.

### 5. Begin R63
Only after physical alignment.

## ACTIVE / QUARANTINED HASHES

Qualified SYNC-R58:
- runtime:
  `30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`
- overlay:
  `d4215a8a5075054a054d5ca60e10e5992c4139588cccaeb0dabe14281f2fd633`
- adaptive source:
  `42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

Quarantined SYNC-R59:
- runtime:
  `a6a0e65460948562c2cd7146efcb207a6b02ff77403f67a6bf9049792d95d625`
- overlay:
  `059e10a3b2cb71acf3db8144240ebfebeeac6924daf13fdb2d1858f1a3369e41`
- adaptive source:
  `7c150389a688b4d769b96ade341921a77b7fe86289645c0c613a035c6151a377`

DB59:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## CURRENT SESSION INCIDENT
Local container and Python:
`TransportTimeoutError`

Classification:
`RUNTIME_TRANSPORT__NOT_SCIENTIFIC_FAILURE__NOT_PACKAGE_CORRUPTION`

## PROHIBITIONS
- do not rerun R59-R62
- do not start R63 early
- do not start F04
- do not treat SYNC-R59 as qualified
- do not discard SYNC-R59
- do not claim physical recovery complete until 9 new aligned packages are delivered

Status token:
`RECOVERY__SYNC_R59_PHYSICAL_BASE__R62_FAIL_OVERLAY__ALIGN_9_PACKAGES_FIRST__R63_NOT_STARTED`
