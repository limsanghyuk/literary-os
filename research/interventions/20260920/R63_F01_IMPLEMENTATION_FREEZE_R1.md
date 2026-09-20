# R63 F01 Semantic Applicability + Abstention — Implementation Freeze R1

Date: 2026-09-20
Status: `IMPLEMENTED_SOURCE_FROZEN__PRE_PRIMARY__FRESH_CASES_0`

Preregistration:
`research/interventions/20260920/R63_F01_SEMANTIC_APPLICABILITY_ABSTENTION_PREREG_R1.md`
Commit:
`a91180860dde0f7503a8b47f7358a966df53123f`

## Frozen lineage
Physical parent:
`SYNC-R60`

Control source:
`SYNC-R58 / ADAPTIVE_UL16`
SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R62 research parent source:
`7c150389a688b4d769b96ade341921a77b7fe86289645c0c613a035c6151a377`

R63 frozen Treatment adaptive source SHA256:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

R63 F01-only diff SHA256:
`ff007539ed3843ede68e882ac1538d680687a1b385342335daecb8a44fc0a5ad`

Canonical diff:
`research/interventions/20260920/R63_F01_ONLY.diff`

## Code-boundary result
PASS.

Only the R62 F01 transaction-stage selector boundary was changed:
- exact R58 baseline-stage helper;
- family-specific semantic-license gate;
- deterministic ACCEPT / ABSTAIN diagnostics;
- fail-closed fallback to exact R58 precursor.

No intentional change to:
- obligation compiler;
- sequence graph;
- resolution semantics;
- F04 semantic-repetition validator;
- F06 necessity;
- F07 State Carry runtime;
- F08 Provider context;
- DB authority;
- Production path.

Whole runtime Python compile:
`45 / 45 PASS`

## Known-failure regression
R62 known cases were used only as implementation regression, not qualification.

All 12 historical R62 synthetic cases:
`12 / 12 architecture validation PASS`

Known unanimous R62-loss repair:
- C06-T1: COST_BEARING_CHOICE -> ABSTAIN -> COMPLICATE_THREAD
- C08-R1: PHYSICAL_RISK_FAILURE -> ABSTAIN -> TEST_BOUNDARY
- C11-I1: MISINTERPRETATION -> ABSTAIN -> PROBE_INFORMATION

Known-12 mechanical receipt SHA256:
`9ce1071a5e322d99de5a6251623dcb6726b052c0b08866b677d4d97f80b43a3f`

## R58B regression
PASS:
- sequences 12
- scenes 66
- weaving_fraction 0.917
- unique actions 66
- duplicate scene-function signatures 0
- due resolved exactly once PASS
- deferred preservation PASS
- blocked preservation PASS
- issues []

Selector diagnostics on R58B:
- BASELINE_ONLY 8
- ACCEPT 18
- ABSTAIN 11

R58B receipt SHA256:
`4976ef133ebe580f1613b01881cdaad8d7d232fcfddf695b1ca4fe54c9de6d5d`

This demonstrates that R63 is not an always-abstain implementation.

## Freeze rule
The Treatment source above is now immutable for the R63 primary qualification.

No further selector tuning is allowed after creation of the fresh primary cases.

Any source change requires a new R63 preregistration/freeze revision and invalidates subsequently created primary cases.

## Next operation
Create exactly 12 new cutoff-safe fresh paired cases after this source freeze, then execute:
`Control exact R58 vs Treatment frozen R63`

Status token:
`R63_SOURCE_FROZEN__7236EBA3__KNOWN_FAILURE_REPAIR_PASS__R58B_PASS__FRESH_PRIMARY_NOT_CREATED`
