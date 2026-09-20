# CURRENT NEXT RESEARCH POINTER
Last updated: 2026-09-20

## CURRENT STATE
- Physical authority: **SYNC-R62** (physical namespace)
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59**
- Research DB: **DB64**

## CLOSED
- R62 CLOSED FAIL 9W/0T/3L
- R63 CLOSED FAIL PREBLIND
- R64 CLOSED FAIL PREBLIND

## R64
Canonical result:
`research/interventions/20260920/R64_F01_TYPED_SEMANTIC_ROLE_RESULT_R1.md`

Failure class:
`FIELD_TYPED_LEXICAL_EVIDENCE_IS_STILL_NOT_SENSE_DISAMBIGUATED_SEMANTICS`

Mechanical:
- Control 12/12 PASS
- Treatment 12/12 PASS
- Treatment ACCEPT 30 / ABSTAIN 18

Safety failure:
`표면 마감` was interpreted as deadline/time pressure, falsely licensing PRESSURE_ESCALATION.

External blind:
NOT RUN.

## PHYSICAL GATE
Post-R64 physical alignment: COMPLETE.

Trust root:
`c9acf57e92663f03c3231b45601dcef622e6bc8ff9cd18876874eaa1bff18b68`

## NEXT
`R65 = F01 Sense-Disambiguated Semantic Predicate Gate`

Status:
`NOT_STARTED`

Required repair:
- predicate/argument or equivalent semantic-role disambiguation;
- compound/process senses cannot trigger unrelated dramatic roles;
- causal structure independently corroborates licenses;
- exact R58 fail-closed fallback;
- R62/R63/R64 failures regression-only;
- fresh R65 cases only after R65 source freeze.

Do not start F04.
