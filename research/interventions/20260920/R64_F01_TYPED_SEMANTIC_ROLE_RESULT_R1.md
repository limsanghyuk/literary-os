# R64 F01 Typed Semantic-Role License Gate — Result R1

Date: 2026-09-20
Status: `CLOSED_FAIL__PREBLIND_SELECTOR_SAFETY__SEMANTIC_ROLE_POLYSEMY`

## Authority
- Physical authority at experiment start: SYNC-R61 / Delivery R2
- Active qualified Candidate: SYNC-R58 / ADAPTIVE_UL16
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64 research-only
- R64 Treatment never became active authority.

## Frozen prerequisites
Preregistration:
`research/interventions/20260920/R64_F01_TYPED_SEMANTIC_ROLE_LICENSE_PREREG_R1.md`

Prereg Git blob:
`0dda0fb20a7311ddafaa3be5c0603e0bf6a3e831`

Implementation freeze commit:
`b4392dd5ca3f3a413295f355f95f7a688ed75f1b`

Frozen R64 Treatment source SHA256:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

F01-only diff SHA256:
`916933938edfca9e2b8bf9baf9c8f97dd1639847d2b7f4bd95054de82671cbb8`

Fresh input seal commit:
`06cc64986ace6fecd00e190643f39dd41a50f04c`

Fresh primary JSON SHA256:
`4528cc1af5c3fbbc71c5b301749df47dadd3544ff862886593e3e8c028a9b3f7`

## Pre-primary regression
Known R62/R63 failure regression:
- 6/6 bad families blocked
- 6/6 exact R58 fallback
- 6/6 validation PASS

Receipt SHA256:
`42e8458543ba5d594b51a3d373a04e0cc6b55ef6e25a6e087d744c342f316856`

R58B regression:
PASS.

R63 fresh-set regression:
12/12 mechanical PASS.

## Fresh primary mechanical result
Control exact R58:
- 12/12 architecture validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate concrete action cases: 0
- distinct precursor families: 4
- output SHA256:
  `6c25a9737cc5ff5902d80e09010f364a68b8bcd9163ae09a8fc65bd46fb87f35`

Treatment frozen R64:
- 12/12 architecture validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate concrete action cases: 0
- ACCEPT 30 / ABSTAIN 18
- distinct precursor families: 8
- output SHA256:
  `342e4eb3486a056f6c2b11021d8e65617c88d665874da819d12af56c1fb038fd`

The intervention transmitted and did not collapse to always-abstain.

## Pre-blind selector-safety failure
Selector safety audit SHA256:
`bb81ae37bd6f1017b2b5c7b072afce8e7033a87243f25e07ce28527228a47a97`

### R64C04_RARE_BOOK / R64C04-E1
Frozen input statement:
`희귀본 보존실의 표면 마감 작업 중 가습기 경고등이 켜진다`

Treatment selected:
`PRESSURE_ESCALATION`

Reason:
`LICENSED_TYPED_DRAMATIC_PRESSURE`

The license evaluator treated Korean token `마감` as deadline/time-pressure evidence.

In this obligation, however, `표면 마감` means surface finishing. No dramatic, social or time pressure is encoded by that token.

Classification:
`DOMAIN_POLYSEMY_FALSE_POSITIVE__SURFACE_FINISHING_AS_DEADLINE`

This directly violates the preregistered selector-safety override:
semantic-domain polysemy cannot supply the only family license.

## Root cause
R64 improved field provenance and structural preconditions, but still used lexical token stems inside typed fields.

Therefore:
`TYPED_FIELD_PROVENANCE_IS_NOT_TYPED_SEMANTIC_ROLE_DISAMBIGUATION`

R63 failure:
`LEXICAL_LICENSE_IS_NOT_SEMANTIC_LICENSE`

R64 refinement:
`FIELD_TYPED_LEXICAL_EVIDENCE_IS_STILL_NOT_SENSE_DISAMBIGUATED_SEMANTICS`

A field can be appropriate while a token inside that field still has the wrong sense.

## External blind
NOT RUN.

Reason:
the frozen pre-blind selector-safety gate failed.

A favorable blind aggregate cannot override the preregistered safety failure.

## Final
`R64 = CLOSED_FAIL`

R64 establishes:
- exact R58 fail-closed fallback remains mechanically sound;
- R62/R63 known failures can be blocked;
- typed field provenance and structural prerequisites reduce prior false licenses;
- useful diversification remains active.

R64 does NOT establish safe semantic applicability or F01 qualification.

## Evidence
R64 evidence ZIP SHA256:
`60f25fed4a0a05b68efa70268660388717f52b50ce3a5cbc8bbd8973fafc8649`

## Authority consequence
Active qualified Candidate remains exact SYNC-R58 / ADAPTIVE_UL16.
Production remains ENG:R47 / LEGACY_R53.
Runtime DB remains DB59.
R64 source/output become failed research evidence only.
No Candidate or Production promotion.

## Next research
`R65 = F01 Sense-Disambiguated Semantic Predicate Gate`

Required repair:
- semantic predicate must resolve role/sense, not only field provenance;
- physical/process noun compounds must not trigger time/social pressure predicates;
- role evidence should be predicate/argument based where possible;
- family license must be independently supported by causal structure;
- exact R58 fallback remains mandatory;
- R62/R63/R64 failures regression-only;
- fresh R65 primary cases only after R65 source freeze.

R65 is NOT STARTED.

Status token:
`R64_CLOSED_FAIL__MECHANICAL_12_OF_12_BOTH_ARMS__TYPED_FIELD_POLYSEMY_FALSE_POSITIVE__BLIND_NOT_RUN__ACTIVE_SYNC_R58_UNCHANGED__R65_NEXT_NOT_STARTED`
