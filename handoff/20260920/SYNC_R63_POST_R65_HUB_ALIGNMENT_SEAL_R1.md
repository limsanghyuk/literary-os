# SYNC-R63 Post-R65 Hub Alignment Seal R1

Date: 2026-09-20
Status: `HUB_AND_PHYSICAL_AUTHORITY_ALIGNED__R65_CLOSED_FAIL__R66_NEXT_NOT_STARTED`

## Current authority
- Physical authority: **SYNC-R63**
- Parent: **SYNC-R62**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Failed research evidence: **R62 + R63 + R64 + R65**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- R65: **CLOSED FAIL before external blind**
- R66: **NOT STARTED**

## Current physical trust
Trust root:
`94697514918cff9091132fb6adafeb75dadf195c4be5e6e2c51861d561ba3916`

C2 logical:
`979634720b06e931bb9bc8332a068500e754619762c97f3e1695c0f06f9738f3`

Active runtime:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

R65 failed source:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

R65 evidence ZIP:
`90e138cdcb31fe9d930b65cd8f9ea3cf6d6ea5642786aa4879a01751da2cf5f1`

## R65 scientific closure
Mechanical:
- Control 12/12 PASS
- Treatment 12/12 PASS
- Treatment ACCEPT 33 / ABSTAIN 14

Selector safety:
FAIL.

Fresh failure:
`R65C06_AUCTION_LEDGER / R65C06-E1`

The deadline cue `시한` was falsely matched inside the unrelated word `표시한다`, licensing `PRESSURE_ESCALATION` where no deadline/time pressure exists.

Diagnosis:
`TARGETED_SENSE_DISAMBIGUATION_IS_NOT_BOUNDARY_SAFE_SEMANTIC_PARSING`

External blind:
NOT RUN.

## Physical audit
- 9/9 transport SHA PASS
- all ZIP CRC PASS
- duplicates / encrypted / unsafe paths = 0
- C2 logical reassembly PASS
- exact SYNC-R58 active runtime PASS
- R65 failed source/evidence preserved as non-active PASS
- B1/B2/D1/D2 byte-identical to SYNC-R62
- secret-pattern audit PASS
- B2 margin under 256 MiB: 148,859 bytes
- OOM 0 / OOM-kill 0

## Hub transaction commits
- R65 preregistration: `08f2f148d7b9fbd635594508ae5349fbe712bb04`
- R65 canonical diff: `f8b14861ecf94ab1635c7ba644fbe3fa82314d05`
- R65 implementation freeze: `da2ff1e74f5b89c2ff7e82538caea5eec3dad553`
- R65 fresh cases custody: `10ac5233aa3f8bb974db32b0beaca601343ca61b`
- R65 fresh input seal: `f2cc0d57f6635f2a702d1d2d037653faf344fcbf`
- R65 result: `b1bdd77a6fd9ffc4da9bc5cdb00f38b2c8f27713`
- SYNC-R63 START HERE: `84e1b04c3e75e07f2259b6851bf1fdbd07a27e57`
- SYNC-R63 physical receipt: `a9d7773533f95e44467691934684519da6009214`
- CURRENT_DEVELOPER_HUB_AUTHORITY: `542587d599eba918bc9f4fab828bb91609f53a70`
- CURRENT_NEXT_RESEARCH_POINTER: `611f30674c45e59861b0ab089c8fd0bb46fb31e6`
- CURRENT_HANDOFF_POINTER: `2f58456947307b360c7a41c7e9c94f11d4dd09a5`
- CURRENT_SESSION_RECOVERY_POINTER: `475a43e7da5989ee1579557a259ea8b32bafe085`

## Next
`R66 = F01 Boundary-Safe Predicate Parser Gate`

R66 is NOT STARTED.

A fresh session must verify the SYNC-R63 trust root and transports, then may preregister R66.

Status token:
`SYNC_R63_HUB_ALIGNED__R65_CLOSED_FAIL_PREBLIND__ACTIVE_SYNC_R58__R66_NEXT_NOT_STARTED`
