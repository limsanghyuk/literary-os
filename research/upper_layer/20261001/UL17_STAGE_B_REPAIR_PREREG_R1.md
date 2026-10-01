# UL17 Stage-B B06 Open-Debt Semantic Repair — Preregistration R1

Date: 2026-10-01
Status: PREREGISTERED__BEFORE_REPAIR_IMPLEMENTATION__NO_AUTHORITY_CHANGE

## Trigger
UL17 Stage B first exact-R69 execution is immutable FAIL because B06 PAYOFF urgency produced false source-due fulfillment, false open-payoff closure, and lost open debt.

## Frozen responsible boundary
`UL16_OBLIGATION_DISPOSITION_AND_SCENE_RESOLUTION_SEMANTICS`

Exact R69 runtime SHA256:
`3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`

Adaptive Showrunner source SHA256:
`740cca05a94dbb59eb9a1600e1c7d98cdc887693aa5ab46fec2bd2eaef78d306`

## Hypothesis
The failure is caused by conflating:
- source due/closable,
- nondeferrable/urgent,
- selected for current-episode touch,
- resolved/closed.

A bounded repair that preserves these as separate semantics can allow a source `due=false, can_defer=false` obligation to be scheduled and advanced without falsely resolving it.

## Allowed implementation changes
Only `literary_os_runtime/adaptive_showrunner_ul16.py` may change, and only at:
1. obligation normalization/disposition;
2. sequence scheduling input for selected obligations;
3. scene final-stage resolution decision;
4. reverse-reconstruction/validation needed to prove open selected debt remains open.

No change is allowed to:
- R66 transaction-family semantic predicates;
- sequence bundling relation score;
- scene action templates except where final close/open status must be represented;
- state-carry runtime;
- provider/rendering code;
- DB authority;
- production path.

## Required semantic states
At minimum the repaired runtime must distinguish:
1. `SELECTED_DUE`: source due and eligible to resolve.
2. `SELECTED_OPEN_TOUCH`: source not due but nondeferrable/urgent; must be scheduled/touched but must not be resolved.
3. `DEFERRED`: source not due and deferrable.
4. `BLOCKED_PRECONDITION`.

## Frozen B06 rule
For `PAY_TAPE_1` under B06:
- source `due=false` remains false;
- `can_defer=false` may force current-episode selection/touch;
- authentication/public resolution must not be invented;
- final resolution/closure is forbidden;
- the obligation must remain open in terminal debt.

## Qualification
Repair PASS requires all:
- original Stage-B B01-B08 rerun from the same frozen fixture/matrix;
- B01-B05/B07/B08 remain PASS;
- B06 causal receipt remains present;
- false_due_fulfillment = 0;
- false_deferred/open_fulfillment = 0;
- lost_open/deferred_debt = 0;
- canonical validation errors = 0;
- irrelevant metadata semantic change = 0;
- exact prior R66/R67/R68/R69 regression suites available in the runtime source remain PASS;
- no future-source leakage.

## Stop rules
If the repair requires changing the frozen fixture, Stage-B matrix, thresholds, or Stage-D rules, STOP and classify protocol change rather than repair PASS.
If unrelated regression changes occur, FAIL and do not proceed to Stage C.

## Authority
This is research-only. A passing patched runtime is not Physical Authority. Physical successor is mandatory only after actual Candidate mutation is adopted, full regression and C1/C2 binding pass, 9-package reseal/audit pass, and developer delivery.
