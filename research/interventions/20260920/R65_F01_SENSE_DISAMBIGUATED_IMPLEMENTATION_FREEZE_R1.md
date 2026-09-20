# R65 F01 Sense-Disambiguated Semantic Predicate — Implementation Freeze R1

Date: 2026-09-20
Status: `IMPLEMENTED_SOURCE_FROZEN__FRESH_PRIMARY_NOT_CREATED`

## Parent / control
Physical authority:
`SYNC-R62`

Active Control:
`SYNC-R58 / ADAPTIVE_UL16`

Exact Control source SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R64 failed research source SHA256:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

## Preregistration
Canonical:
`research/interventions/20260920/R65_F01_SENSE_DISAMBIGUATED_SEMANTIC_PREDICATE_PREREG_R1.md`

Preregistration commit:
`08f2f148d7b9fbd635594508ae5349fbe712bb04`

## Frozen Treatment source
R65 source SHA256:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

Canonical F01-only diff SHA256:
`5a1bb5e3cd33b2e74083d858d2ed89b6d39d53d7ccdf240ee6fce50ed938c190`

Source-freeze evidence ZIP SHA256:
`61f9eb5e0e0155d43b41788623240d4eb1235aa750ca8b81ecaf33c0ac4dac21`

## Code boundary
PASS.

Changed existing top-level functions versus R64:
- _stage_plan_for_obligation

Added R65 functions:
- _r65_compound_senses
- _r65_semantic_predicates
- _r65_receipt
- _r65_semantic_license
- _r65_transaction_decision

No unrelated top-level function changed or removed.

Code-boundary receipt SHA256:
`be301cdf933015b8fec63a73f746104593e1ca8931716e178115437171264535`

Whole runtime compile:
`45/45 PASS`

Compile receipt SHA256:
`3ef2398dcaf492eebb6883e51773467ca8aa71d26921a09c51c4aa5294536045`

## Known-failure regression
PASS 7/7.

All seven:
- bad family blocked;
- exact R58 fallback;
- architecture validation PASS.

Included:
- R62 C06 COST_BEARING_CHOICE
- R62 C08 PHYSICAL_RISK_FAILURE
- R62 C11 MISINTERPRETATION
- R63 hose pressure PRESSURE_ESCALATION
- R63 막차 COUNTERMOVE
- R63 successful mitigation PHYSICAL_RISK_FAILURE
- R64 표면 마감 false deadline PRESSURE_ESCALATION

Receipt SHA256:
`5b38369f85527da981a1c3eb7c221fc99a840f5bd1c9763e1e3f26043cc0894e`

## R58B regression
PASS:
- sequences 12
- scenes 66
- validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate actions 0
- selector modes: BASELINE_ONLY 8 / ABSTAIN 20 / ACCEPT 9

Receipt SHA256:
`473475f697a71c5cfb30492cda392d0f5cbbc304ae3a2749613a644d1e3c2d99`

## Historical fresh-set regression
R63 fresh set:
- 12/12 PASS
- ACCEPT 27 / ABSTAIN 21
- receipt SHA256 `54bbb5f305c397679cf7ef093e9943cf44e72a6aab5b43e3207f3c55d57e8462`

R64 fresh set:
- 12/12 PASS
- ACCEPT 29 / ABSTAIN 19
- receipt SHA256 `3ebd1fc10d497a2dd9c596ab825ab91001da6ead4fbff1a8a87f80f49ec5cfdc`

These historical sets are regression-only and cannot count toward R65 qualification.

## Freeze rule
This Treatment source is immutable for R65 primary qualification.

Fresh R65 primary cases must be created only after this freeze.
No source tuning is permitted after fresh-case creation.

Status token:
`R65_SOURCE_FROZEN__7BFAA77D__KNOWN_FAILURE_7_OF_7_PASS__R58B_PASS__R63_R64_REGRESSION_PASS__FRESH_PRIMARY_NOT_CREATED`
