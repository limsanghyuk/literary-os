# R67 F07 Dual-Ledger State Carry Runtime — Implementation Freeze R1

Date: 2026-09-20
Status: `IMPLEMENTED_SOURCE_FROZEN__FRESH_RUNTIME_CASES_NOT_CREATED`

## Parent / Control
Physical authority:
`SYNC-R64`

Control runtime:
`R66 qualified Candidate`

Control runtime SHA256:
`575fd5378c69d282c9b4c39d03e52d4cc436744fa67c792db8515fe91c384e75`

Control adaptive source SHA256:
`0558c910896556048bb6acf0e1d4097477c3c31a60d47f16c4bd83e3f6253f1d`

Control state-carry source SHA256:
`07246dd7db3bf059e838f45b5643ae73a91bf8bc400046b4539f891f644a463d`

## Preregistration
Canonical:
`research/interventions/20260920/R67_F07_DUAL_LEDGER_STATE_CARRY_RUNTIME_PREREG_R1.md`

Preregistration commit:
`f386f5f775416bfc093dcf36b343e06772f94cb9`

## Frozen Treatment
Treatment runtime ZIP SHA256:
`9ab625122d7b572bf781ffa8062271f085cfde2d757e42dd79a18b977d9a72b8`

Treatment adaptive source SHA256:
`6574449a4a0b0520db5993b1f1abe532709b19aa9a5c7dc706df24b8c1fc6b91`

Treatment state-carry source SHA256:
`ce38885171d0f318aeb2142ec16d119814be7fb736ebc361166007b4d2eea087`

Canonical diff SHA256:
`511e7046ac1280965332b7e099e73abc543014f546e666bf18b804d0ece5a621`

Source-freeze evidence ZIP SHA256:
`78358598add2f224f69dca8fc7adcfa12c42a351ad02d69fc7d76c3c6ace9fff`

## Implementation
Runtime now enforces:
- `deferred_obligations` = canonical evidence-safe open-state ledger only;
- `planner_unrealized_obligations` = planner-only unrealized obligation ledger;
- planner rows carry `factual_access_forbidden=true`;
- architecture-only deferred obligations may enter planner ledger but not canonical factual state;
- fulfilled obligations are removed from both ledgers;
- Adaptive Showrunner consumes planner-only ledger with provenance `PLANNER_UNREALIZED_OBLIGATION`;
- legacy rich deferred rows are migrated into planner-only ledger and stripped from canonical state;
- canonical factual state hash excludes planner-only ledger;
- planner ledger hash is tracked separately.

## Pre-freeze gates
G1-G6 deterministic gate receipt:
`e4d7e0b5c725210fc82ae0d6c9c51491597837061a1bcd3e9ca4714d83cca3a1`

Control/Treatment equivalence:
`8069518569ace0cae8df24429f70a292420f410f264c30e64e9e7e2f728e05fd`

Results:
- factual relationship/information/social domains identical to Control — PASS;
- R66 fresh F01 transaction decisions bit-identical — PASS.

Runtime compile:
`45/45 PASS`
Receipt SHA256:
`bd9accc6907e4b6cd489501f069f703c0fa5c34fbe5dfea717441e9cec973df8`

Code Boundary Audit:
PASS.
Receipt SHA256:
`be10fd4ba0c041086349b6169d48695abf0fab3bea8dbc3d508bca8677ae88cf`

## Freeze rule
The Treatment runtime above is now immutable for R67 primary qualification.

Only after this freeze may the fresh 12-case two-episode runtime qualification set be created.

Any Treatment source change requires a new freeze revision and invalidates later fresh cases.

Status token:
`R67_SOURCE_FROZEN__F07_DUAL_LEDGER_RUNTIME__R66_F01_REGRESSION_PASS__FRESH_CASES_NOT_CREATED`
