# R72 — F05 Adaptive Distribution / Count Pressure — Preregistration R3

Date: 2026-09-22

Status:
`PREREGISTERED_R3__OUTPUTS_0_FOR_R3__R2_PRIMARY_EXECUTION_HOLD_ADAPTER_DEFECT`

## Why R3 exists
R72-R2 primary execution produced Treatment outputs, but exact R69 Control failed closed on 5/24 cases before Control output because the R2 source adapter converted distinct deferred causal threads into one generic sentence pattern. Exact R69 correctly rejected those inputs as `MECHANICAL_OBLIGATION_PATTERN_REPEAT`.

R72-R2 is therefore preserved as:
`EXECUTION_HOLD__CONTROL_INPUT_ADAPTER_PATTERN_COLLAPSE__NO_SCIENTIFIC_PASS_FAIL`

R2 cases may not be repaired in place or reused.

## R3 narrow repair
Only the deferred-thread source adapter changes:
- use exact source-specific `planner_input.subplot_debt.debt` text matched by thread id;
- if no match exists, use source-specific serialized active-thread record prefixed by work id;
- generic deferred-thread templates are prohibited.

Unchanged:
- exact R69 Control engine;
- F05 Treatment allocator bytes;
- pressure ontology and capacities;
- deterministic gates and blind thresholds;
- R71-work exclusions;
- max 2 cases/work and 8 low / 8 medium / 8 high design.

## Seals
- R3 preregistration JSON SHA256: `7f05670598484efca1a747d85c6b84cf94a4dbc873f2ae79f398550663be3f3b`
- Primary Materialization Protocol R2 SHA256: `c4212f45a1fbc1a68b410837d893911879bdcb3d949971a3d19627966e574376`
- R3 preexecution seal SHA256: `a85ceec0265d855f97e11f9ddc7b517934a91b8d54cd5827b51170f5749bad53`
- R2 hold receipt SHA256: `fbef970e8cbc564c20e7a3a737356bee9db2700ea411d70b2e1848f6c82a03c9`

## Freshness
All 24 R72-R2 primary cases are excluded from R3. R3 must freeze a fresh 24-case ledger before any R3 Treatment output.

## Claim boundary
Planning/allocation layer only. R3 does not alter Production, Active Runtime, DB authority, or operational Level-3 status.
