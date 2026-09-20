# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-20

## CANONICAL READ FIRST
`handoff/20260920/START_HERE_POST_R65_SYNC_R63_R1.md`

Supporting:
- `handoff/20260920/SYNC_R63_POST_R65_PHYSICALIZATION_RECEIPT_R1.md`
- `research/interventions/20260920/R65_F01_SENSE_DISAMBIGUATED_RESULT_R1.md`

## CURRENT AUTHORITY
- Physical authority: **SYNC-R63**
- Parent: **SYNC-R62**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Failed research evidence: **R62 F01 + R63 F01 + R64 F01 + R65 F01**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**

## RESEARCH STATE
- R59 CLOSED HOLD
- R60 CLOSED PASS
- R61 CLOSED
- R62 CLOSED FAIL — 9W / 0T / 3L
- R63 CLOSED FAIL — preblind selector safety
- R64 CLOSED FAIL — preblind semantic-role polysemy
- R65 CLOSED FAIL — preblind boundary-unsafe substring collision
- R66 NOT STARTED

## TRUST
SYNC-R63 trust root:
`94697514918cff9091132fb6adafeb75dadf195c4be5e6e2c51861d561ba3916`

C2 logical:
`979634720b06e931bb9bc8332a068500e754619762c97f3e1695c0f06f9738f3`

Active runtime remains exact SYNC-R58:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

R65 failed source evidence:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

## R65 RESULT
Mechanical:
Control 12/12 PASS; Treatment 12/12 PASS; Treatment ACCEPT 33 / ABSTAIN 14.

Selector safety:
FAIL before external blind.

Failure:
deadline cue `시한` was falsely matched inside `표시한다`, licensing PRESSURE_ESCALATION without any deadline.

Diagnosis:
`TARGETED_SENSE_DISAMBIGUATION_IS_NOT_BOUNDARY_SAFE_SEMANTIC_PARSING`

External blind:
NOT RUN.

## NEXT
`R66 = F01 Boundary-Safe Predicate Parser Gate`
Status: **NOT STARTED**.
