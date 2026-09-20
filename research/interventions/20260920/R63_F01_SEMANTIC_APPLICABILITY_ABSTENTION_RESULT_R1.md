# R63 F01 Semantic Applicability + Abstention Gate — Result R1

Date: 2026-09-20
Status: `CLOSED_FAIL__PRE_REGISTERED_SELECTOR_SAFETY_GATE_FAILED__BLIND_NOT_RUN`

## Authority
- Physical authority: SYNC-R60
- Active qualified Candidate: SYNC-R58 / ADAPTIVE_UL16
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64 research-only
- R63 Treatment never became active authority.

## Frozen inputs
Preregistration commit:
`a91180860dde0f7503a8b47f7358a966df53123f`

Frozen R63 Treatment source SHA256:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

Fresh primary JSON SHA256:
`5c7f04816c00a2f5afc42a8c2862f5e888000a2fbefde28f9c73f03c1cdb3376`

Fresh primary count:
12

Known R62 failures C06/C08/C11 were regression-only and excluded from primary qualification.

## Mechanical primary result
Control:
- exact SYNC-R58
- 12/12 validation PASS
- due recoverable PASS
- due resolved exactly once PASS
- deferred preserved PASS
- blocked preserved PASS
- duplicate concrete-action cases 0
- distinct precursor families 6
- output SHA256 `c47dfbf136ca1b6cd15f3078d27f34ba2041c1065d3dbbb455bcb8fe04652822`

Treatment:
- frozen R63 source
- 12/12 validation PASS
- due recoverable PASS
- due resolved exactly once PASS
- deferred preserved PASS
- blocked preserved PASS
- duplicate concrete-action cases 0
- ACCEPT 29 / ABSTAIN 19
- distinct precursor families 15
- output SHA256 `edc0fef56e184439d0ad1869093d7b13cb5cd8dc50eb22c4735f03e5ad721368`

## Selector-safety audit
Audit SHA256:
`927fa12ddb0731c312f2ad910d5ae98a21d343367f899f00e401e3a5e0be66f5`

### Failure 1 — R63C04_SUBWAY_TUNNEL / R63C04-E1
Treatment selected `COUNTERMOVE`, although no prior opposing move/dependency existed.

Root cause:
the selector used raw substring matching including Korean token `막`; the phrase `막차 운행 전` accidentally satisfied it.

Generated precursor then invented an opponent/institution prior move and retaliatory counter-control action unsupported by the frozen input.

Classification:
`LEXICAL_SUBSTRING_FALSE_POSITIVE__UNSUPPORTED_PRIOR_COUNTERMOVE_INVENTION`

### Failure 2 — R63C10_FOOD_RECALL / R63C10-E1
Treatment selected `PHYSICAL_RISK_FAILURE`.

The frozen obligation describes temperature rise followed by backup-power switching, and its visible action successfully stops the temperature rise. No required failure state exists.

Root cause:
the implementation licensed the family when `failure OR visible_action` existed, although the preregistration required the physical risk/failure itself to be causally required.

Generated precursor invented `실패·손상·제약`.

Classification:
`VISIBLE_ACTION_SUBSTITUTED_FOR_REQUIRED_FAILURE__UNSUPPORTED_FAILURE_INVENTION`

## Frozen gate consequence
The preregistered selector-safety gate states that a fresh Treatment output that invents a prior countermove, physical failure, bargain, false belief, institutional constraint, cost-bearing choice or new fact solely to justify a family causes R63 FAIL.

Therefore:
- selector-safety gate: FAIL
- external blind quality evaluation: NOT RUN
- blind score: N/A
- final: `R63 = CLOSED_FAIL`

No post-hoc source repair is allowed inside R63 after source/case freeze.

## What was learned
R63 repaired the three known R62 regression failures and preserved mechanical integrity, but the semantic-license implementation remained too lexical/permissive.

The doctrine `ABSTAIN -> exact R58 baseline` remains viable; the failed component is semantic evidence detection.

## Next research
`R64 = F01 Structured Semantic Evidence Gate`

Recommended repair:
- token/field-aware evidence rather than raw substring containment;
- typed evidence predicates;
- visible action cannot substitute for required failure;
- lexical overlap cannot manufacture causal preconditions;
- fail closed to exact R58 baseline;
- R63 fresh primary cases become regression-only, never R64 primary qualification cases.

R64 is NOT STARTED.

## Infrastructure note
One TransportTimeout occurred before R63 work began and recovered via the established minimal-health protocol.

A later 9472-character Hub base64 string appeared as 9471 characters when relayed through a long conversation/tool-output path. The authoritative local fresh JSON remained intact and matched its pre-Treatment Hub SHA, so no guessed repair was used and no experiment input changed.

## Authority consequence
Physical authority remains SYNC-R60.
Active qualified Candidate remains exact SYNC-R58 / ADAPTIVE_UL16.
R63 source/output are failed research evidence only.
No Production promotion.
No DB authority change.

Status token:
`R63_CLOSED_FAIL__MECHANICAL_12_OF_12_BOTH_ARMS__SELECTOR_SAFETY_2_VIOLATIONS__BLIND_NOT_RUN__ACTIVE_SYNC_R58_UNCHANGED__R64_NEXT_NOT_STARTED`
