# CURRENT NEXT RESEARCH POINTER
Last updated: 2026-09-20

## CURRENT
- Physical authority: **SYNC-R63**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59**
- Research DB: **DB64**

## CLOSED
- R62 CLOSED FAIL
- R63 CLOSED FAIL PREBLIND
- R64 CLOSED FAIL PREBLIND
- R65 CLOSED FAIL PREBLIND

## R65
Canonical:
`research/interventions/20260920/R65_F01_SENSE_DISAMBIGUATED_RESULT_R1.md`

Failure class:
`TARGETED_SENSE_DISAMBIGUATION_IS_NOT_BOUNDARY_SAFE_SEMANTIC_PARSING`

Mechanical:
12/12 both arms PASS.

Safety:
FAIL because `시한` was found as an unbounded substring inside `표시한다`.

External blind:
NOT RUN.

## PHYSICAL ALIGNMENT
`POST_R65_RESEARCH_OVERLAY_ALIGNMENT = COMPLETE`

Current physical authority:
**SYNC-R63**

Trust root:
`94697514918cff9091132fb6adafeb75dadf195c4be5e6e2c51861d561ba3916`

## NEXT
`R66 = F01 Boundary-Safe Predicate Parser Gate`

Status:
`NOT_STARTED`

Required repair:
- eliminate unbounded substring matching from all positive license evidence;
- token/morpheme-bound lexical atoms;
- compound-first word-sense resolution;
- predicate/argument evidence for positive licenses;
- lexical atoms may support but never independently establish causal roles;
- exact R58 fail-closed fallback;
- R62/R63/R64/R65 failures regression-only;
- fresh R66 qualification cases only after R66 source freeze.

Do not start F04.
