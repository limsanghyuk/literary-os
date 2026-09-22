# R72 — F05 Adaptive Distribution / Count Pressure — Preregistration R5

Date: 2026-09-22

Status:
`PREREGISTERED_R5__OUTPUTS_0_FOR_R5__R4_CONTROL_PRECHECK_HOLD_R69_INPUT_VALIDITY_GATE_ADDED`

## Why R5 exists
R72-R4 produced no Treatment outputs. Control-only precheck passed 20/24 cases; 4 cases were rejected by exact R69 because source-tagged `plant_payoff` material normalized to duplicate semantic obligation patterns.

R4 is preserved as:
`CONTROL_PRECHECK_HOLD__R69_PORTFOLIO_INPUT_VALIDITY_REQUIRED__R4_TREATMENT_OUTPUTS_0`

## R5 narrow repair
Before pressure stratification and case selection, every candidate episode's frozen explicit input must pass exact R69:
`compile_active_obligation_portfolio(..., explicit_episode_input=...)`

This gate is **input validity only**:
- no Control architecture count is inspected;
- no Control quality score is used;
- no Treatment output exists at selection time.

Cases rejected by exact R69 fail-closed input semantics are ineligible before selection.

All R72-R2/R3/R4 primary cases are excluded. R5 selects a wholly fresh 24-case ledger.

Unchanged:
- exact R69 Control engine;
- F05 Treatment allocator;
- pressure ontology/capacities;
- thread-state semantics;
- deterministic gates;
- blind thresholds;
- 8 LOW / 8 MEDIUM / 8 HIGH;
- max 2 cases/work.

## Seals
- R4 hold receipt SHA256: `9b8f13ed5ebe1ea613115e68131bd69c5498cb3d53760b596b9d94207fbf97ee`
- R5 preregistration JSON SHA256: `fc4b76f62fe9c38a14abac42a3fda773e0c78ea6aa25b0930be20359c30e85a8`
- Primary Materialization Protocol R4 SHA256: `f2b7663a938697b1b85274fafaafd7f01f4fdea9aaf9c1d656e379c483aa03d7`
- R5 preexecution seal SHA256: `c10f122ae793f230c80e03c67cd72ec2a3d0349af7e643b43f07748cd3d2beda`

## Claim boundary
Planning/allocation layer only. No Production, Active Runtime, DB authority, or operational Level-3 change.
