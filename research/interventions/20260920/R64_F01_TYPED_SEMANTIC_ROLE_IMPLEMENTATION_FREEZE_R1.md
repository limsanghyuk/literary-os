# R64 F01 Typed Semantic-Role License — Implementation Freeze R1

Date: 2026-09-20
Status: `IMPLEMENTED_SOURCE_FROZEN__FRESH_PRIMARY_NOT_CREATED`

## Parent / control
Physical authority:
`SYNC-R61 / Delivery R2`

Active Control:
`SYNC-R58 / ADAPTIVE_UL16`

Exact Control source SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R63 failed research parent source SHA256:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

## Preregistration
Canonical:
`research/interventions/20260920/R64_F01_TYPED_SEMANTIC_ROLE_LICENSE_PREREG_R1.md`

Git blob SHA:
`0dda0fb20a7311ddafaa3be5c0603e0bf6a3e831`

The preregistration existed before this freeze. A later duplicate create attempt correctly failed with GitHub 422 because the path already existed; no preregistration content was overwritten.

## Frozen Treatment source
R64 source SHA256:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

Canonical local F01-only diff SHA256:
`916933938edfca9e2b8bf9baf9c8f97dd1639847d2b7f4bd95054de82671cbb8`

Source-freeze evidence ZIP SHA256:
`742c9dc9587187eb3cb5f8a116212a8b96af6b8395fd61f7d409d9a348c57d8a`

Evidence ZIP contains:
- exact frozen r64.py;
- exact F01 typed-role diff;
- known R62/R63 failure regression receipt;
- R58B regression receipt;
- R63 fresh-set regression receipt.

## Code-boundary audit
PASS.

Changed top-level functions versus frozen R63 source:
- added: _r64_tokens
- added: _r64_has_token_stem
- added: _r64_has_phrase
- added: _r64_typed_evidence
- added: _r64_receipt
- added: _r64_semantic_license
- added: _r64_transaction_decision
- changed: _stage_plan_for_obligation

No unrelated top-level function changed.

Copied runtime Python compile:
PASS.

## Known-failure regression
PASS 6/6.

All cases:
- bad family blocked = true
- exact R58 baseline fallback = true
- architecture validation = PASS

Included:
- R62 C06 COST_BEARING_CHOICE
- R62 C08 PHYSICAL_RISK_FAILURE
- R62 C11 MISINTERPRETATION
- R63 airport hose-pressure PRESSURE_ESCALATION
- R63 subway 막차 COUNTERMOVE
- R63 food-recall false PHYSICAL_RISK_FAILURE

Receipt SHA256:
`42e8458543ba5d594b51a3d373a04e0cc6b55ef6e25a6e087d744c342f316856`

## R58B regression
PASS:
- sequences 12
- scenes 66
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate actions 0
- selector modes: ACCEPT 9 / ABSTAIN 20 / BASELINE_ONLY 8

Receipt SHA256:
`558a2dcbccecd4590cdc9ed2957e75ba97d29a88846c8c968c9a54b43f11fc06`

## R63 fresh-set regression
The old R63 fresh primary is regression-only for R64.

PASS:
- 12/12 mechanical
- ACCEPT 27 / ABSTAIN 21

Receipt SHA256:
`444f8243dd1a96e7434d33886bd13e23ee2f2c1a526cc1caad08f68c591811f0`

## Freeze rule
The R64 Treatment source hash above is immutable for R64 primary qualification.

Fresh R64 primary cases must be created only after this freeze.
No source tuning is allowed after fresh-case creation.

Any source change requires a new preregistration/freeze revision and invalidates later primary cases.

Status token:
`R64_SOURCE_FROZEN__5118B1C7__TYPED_ROLE_GATE__KNOWN_FAILURE_6_OF_6_PASS__R58B_PASS__FRESH_PRIMARY_NOT_CREATED`
