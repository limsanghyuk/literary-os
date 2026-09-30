# UL18 — Partial-Closure / Open-Debt Contract Recovery — Preregistration R1

Date: 2026-10-01

Status:
`PREREGISTERED__NO_IMPLEMENTATION_OUTPUTS__NO_RUNTIME_MUTATION__NO_AUTHORITY_CHANGE`

## Purpose

Repair the exact defect exposed by UL17 Stage B without inventing a new narrative architecture.

UL17 showed that current exact R69 causally consumes THREAD / RELATIONSHIP / INFORMATION / SOCIAL / EVENT / CHARACTER state and preserves irrelevant-metadata invariance, but B06 PAYOFF fails because the adaptive planner conflates **must be touched now** with **must be fulfilled/closed now**.

The repair must recover semantics that already exist elsewhere in the runtime:

- Episode Synopsis Architecture: `due_now[].closure = PARTIAL_ONLY`
- `partial_payoff.mode = PARTIAL_PAYMENT`
- `terminal_contract.no_full_closure = true`
- `debt_budget.full_closure_allowed = false`
- deferred status `KEEP_OPEN`
- R60/R67 planner-unrealized / dual-ledger state carry

This is contract recovery, not a new Showrunner layer.

## Frozen parent evidence

- Physical Authority: SYNC-R74
- Parent runtime: exact R69
- exact R69 SHA256: `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- exact adaptive source SHA256: `740cca05a94dbb59eb9a1600e1c7d98cdc887693aa5ab46fec2bd2eaef78d306`
- UL17 Stage B: `FAIL__EXACT_R69_CAUSAL_ADOPTION_HARD_GATE`
- Failing frozen probe: B06 PAYOFF urgency
- Do not edit or rescore UL17.

## Responsible boundary

`EPISODE_PARTIAL_CLOSURE_CONTRACT -> UL16_OBLIGATION_NORMALIZATION -> DISPOSITION -> SCENE_RESOLUTION -> STATE_CARRY`

Current exact-R69 behavior to repair:

1. `due_raw = due OR not can_defer`
2. every accepted row -> `SELECTED_DUE`
3. every selected obligation -> final `RESOLVE`
4. validation expects every selected due obligation to resolve once

This loses the distinction between **schedule/touch** and **close/fulfill**.

## Frozen intervention

Introduce the smallest research-only semantic distinction needed to preserve the existing contract.

### A. Scheduling and closure are independent

For each normalized obligation derive/preserve:

- `must_touch_now`
- `closure_policy`

Frozen rules:

1. `must_touch_now = due OR not can_defer`
2. explicit source closure/status policy, when present, is authoritative.
3. `due=false AND can_defer=false` means `MUST_TOUCH_KEEP_OPEN`; it must not become fulfilled merely because it cannot be deferred.
4. structured `closure=PARTIAL_ONLY` or `status=KEEP_OPEN` must survive normalization.
5. no natural-language inference from prose is allowed.
6. legacy obligations with `due=true` and no explicit closure policy retain legacy `RESOLVE_ONCE` behavior for bounded compatibility.

### B. Scene realization

- `RESOLVE_ONCE` obligations retain the existing final RESOLVE.
- `PARTIAL_ONLY / KEEP_OPEN / MUST_TOUCH_KEEP_OPEN` obligations must receive observable transaction progress but no `resolved_obligation_ids` entry.
- open touched obligations must remain in a terminal residual/open-debt ledger.

### C. Reverse reconstruction / validation

PASS requires:

- every must-touch obligation is represented in sequence and scene plans;
- every RESOLVE_ONCE obligation resolves exactly once;
- every keep-open/partial obligation resolves zero times;
- open debt survives to terminal residual/state carry;
- deferred/blocked obligations are not falsely fulfilled;
- future-source leakage 0;
- canonical IR validation errors 0.

## Frozen primary tests

### T1 — UL17 B06 exact counterexample
Same PAY_TAPE_1 mutation:
- pressure 0.62 -> 0.88
- can_defer true -> false
- due remains false
- tape remains unverified/open

PASS only if:
- planner schedules/touches it;
- no final fulfillment/closure is asserted;
- residual/open debt survives.

### T2 — Four-state disposition matrix
Test all:
1. due=true / can_defer=false
2. due=true / can_defer=true
3. due=false / can_defer=true
4. due=false / can_defer=false

No case may infer factual closure from urgency alone.

### T3 — UL17 B01-B08 non-regression
B01-B05/B07 must preserve the already-observed causal effects.
B08 must remain architecture-hash and semantic-decision invariant.

### T4 — Existing contract recovery
Structured R109 `PARTIAL_ONLY` / `KEEP_OPEN` inputs must survive normalization and state carry.

## Regression boundary

Before any adoption claim:
- exact runtime unit/regression suite available in the recovered C1 source;
- R66 transaction/stage behavior;
- R67 dual-ledger state carry;
- R68 semantic repetition validator;
- R69 scene-necessity validator;
- canonical IR compile/validate.

Any new failure outside the declared disposition/closure boundary blocks adoption.

## Qualification path

1. Freeze this preregistration.
2. Implement only in a research copy of exact R69.
3. Run T1-T4 and regressions.
4. If PASS, create a fresh UL18 current-byte candidate receipt.
5. Only then repeat fresh multi-strand architecture qualification under UL18; do not rewrite UL17.
6. Architecture-only blind remains required before any 40K screenplay.
7. Actual Candidate runtime adoption requires regression + C1/C2 binding + 9-package reseal + SHA/CRC/Trust Root + developer delivery.

## Authority rule

UL18 research outputs alone do not change Candidate Runtime, Production, DB59, or Physical Authority.

Until an audited physical successor is actually built and delivered:
`Physical Authority = SYNC-R74`.
