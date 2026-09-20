# R66 F01 Boundary-Safe Predicate Parser — Implementation Freeze R1

Date: 2026-09-20
Status: `IMPLEMENTED_SOURCE_FROZEN__FRESH_PRIMARY_NOT_CREATED`

## Parent / control
Physical authority:
`SYNC-R63`

Active Control:
`SYNC-R58 / ADAPTIVE_UL16`

Exact Control source SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R65 failed research source SHA256:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

## Preregistration
Canonical:
`research/interventions/20260920/R66_F01_BOUNDARY_SAFE_PREDICATE_PARSER_PREREG_R1.md`

Preregistration commit:
`e52ac3fdf06fe45670e9a728cac6fb91c98727e6`

## Frozen Treatment source
R66 source SHA256:
`0558c910896556048bb6acf0e1d4097477c3c31a60d47f16c4bd83e3f6253f1d`

Canonical F01-only diff SHA256:
`8bec59183b7a408aae19cb598f2b828a1989bf13c3f94263c04b8a0e3f787fc5`

Source-freeze evidence ZIP SHA256:
`c7a6153f832dd3d23d99497a5ad4e1dafc94bf66d136319b5d3542fa50a8ef2d`

## Code boundary
PASS.

Added:
- _r66_phrase_match
- _r66_transaction_decision

Changed:
- _r64_has_phrase
- _stage_plan_for_obligation

Removed:
- none

Code-boundary receipt SHA256:
`25381f42d607e2b7d495dac18a8acdc128b5028cf9a684643bfc357f3b7aeba2`

Whole runtime compile:
`45/45 PASS`

Compile receipt SHA256:
`e75e98073e70e15de10f9ac93315a0ff4e2cdecb2a7c68318ab31bb9132dd1e9`

## Known-failure regression
PASS 8/8.

All eight:
- bad family blocked;
- exact R58 fallback;
- architecture validation PASS.

Included:
- R62 C06 COST_BEARING_CHOICE
- R62 C08 PHYSICAL_RISK_FAILURE
- R62 C11 MISINTERPRETATION
- R63 physical pressure PRESSURE_ESCALATION
- R63 막차 COUNTERMOVE
- R63 successful mitigation PHYSICAL_RISK_FAILURE
- R64 표면 마감 false deadline PRESSURE_ESCALATION
- R65 표시한다 containing 시한 false deadline PRESSURE_ESCALATION

Receipt SHA256:
`06317995e6d1af3c54154b62e4f36fdb006d7ea277cfc956a73b449fab36a8cf`

## R58B regression
PASS:
- sequences 12
- scenes 66
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate actions 0
- selector modes: BASELINE_ONLY 8 / ABSTAIN 20 / ACCEPT 9

Receipt SHA256:
`7c9fe07e156439e13cdbecc39d199f58b79b8d96cc39eed12cab9ef6441bc688`

## Historical fresh-set regression
R63 fresh:
- 12/12 PASS
- ACCEPT 27 / ABSTAIN 21
- receipt SHA256 `58ce454e28de9e922da3c06a8b8876f05752e50a1e7820997c862808e14ee832`

R64 fresh:
- 12/12 PASS
- ACCEPT 29 / ABSTAIN 19
- receipt SHA256 `562f695c435f2948526b77a814fded10d2b2af4b2a6c49f29cd83d6703b8fed0`

R65 fresh:
- 12/12 PASS
- ACCEPT 32 / ABSTAIN 15
- receipt SHA256 `02155221ff2dfef3808a514b719a0332f705897941b970e3e79cee44eb5ffec6`

Historical sets are regression-only and cannot count toward R66 qualification.

## Freeze rule
This R66 Treatment source is immutable for primary qualification.

Fresh R66 primary cases must be created only after this freeze.
No source tuning is permitted after fresh-case creation.

Status token:
`R66_SOURCE_FROZEN__0558C910__KNOWN_FAILURE_8_OF_8_PASS__R58B_PASS__R63_R65_REGRESSION_PASS__FRESH_PRIMARY_NOT_CREATED`
