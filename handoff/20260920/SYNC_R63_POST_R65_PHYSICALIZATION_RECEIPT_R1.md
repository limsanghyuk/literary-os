# SYNC-R63 Post-R65 Physicalization Receipt R1

Date: 2026-09-20
Status: `PASS__9_OF_9__R65_FAIL_PHYSICALLY_ALIGNED__R66_NOT_STARTED`

## Authority
- Physical authority: SYNC-R63
- Parent: SYNC-R62
- Active qualified Candidate: exact SYNC-R58 / ADAPTIVE_UL16
- R65: CLOSED FAIL before blind
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64 research-only

## Trust
Trust root:
`94697514918cff9091132fb6adafeb75dadf195c4be5e6e2c51861d561ba3916`

C2 logical:
`979634720b06e931bb9bc8332a068500e754619762c97f3e1695c0f06f9738f3`

Active runtime:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

R65 source evidence:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

R65 evidence ZIP:
`90e138cdcb31fe9d930b65cd8f9ea3cf6d6ea5642786aa4879a01751da2cf5f1`

## Audit
- 9/9 transport SHA PASS
- all package ZIP CRC PASS
- C2 logical ZIP CRC PASS
- duplicates/encrypted/unsafe paths = 0
- active runtime unchanged exact SYNC-R58
- R65 failed source/evidence preserved as non-active
- B1/B2/D1/D2 byte-identical to parent
- B2 remains 268,286,597 bytes, 148,859 bytes under 256 MiB
- secret audit PASS
- OOM 0 / OOM kill 0

## R65 scientific boundary
R65 failed because unbounded phrase matching found `시한` inside `표시한다`, falsely licensing deadline PRESSURE_ESCALATION.

External blind was not run.

Next:
`R66 = F01 Boundary-Safe Predicate Parser Gate`
Status: NOT STARTED.
