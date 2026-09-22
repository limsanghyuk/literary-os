# R72 — F05 Adaptive Distribution / Count Pressure — Preregistration R4

Date: 2026-09-22

Status:
`PREREGISTERED_R4__OUTPUTS_0_FOR_R4__R3_CONTROL_PRECHECK_HOLD_THREAD_STATE_SOURCE_REQUIRED`

## Why R4 exists
R72-R3 used fresh cases and produced no Treatment outputs. Control-only precheck succeeded on 22/24 cases, but two cases still failed exact R69 input validation because `planner_input.active_causal_threads` had no usable `subplot_debt` text and fallback metadata normalized to repeated generic patterns.

DB64 provides the correct cutoff-safe source:
`seqcard_ko/thread_state_vnext_r36/runtime_safe/<work>/<work>_<target_episode>.thread_state.json`

Each open thread carries a distinct `current_statement` with future leakage forbidden.

R3 is therefore preserved as:
`CONTROL_PRECHECK_HOLD__THREAD_STATE_SOURCE_REQUIRED__R3_TREATMENT_OUTPUTS_0`

## R4 narrow repair
For every active causal thread:
- the target-episode runtime-safe thread-state file must exist;
- every active thread id must map to a nonempty unique `current_statement`;
- exact matched `current_statement` is used as the deferred-thread semantic statement for exact R69 Control;
- a case without complete mapping is ineligible before selection.

R2 and R3 primary cases are excluded. R4 uses a wholly fresh 24-case ledger.

Unchanged:
- exact R69 Control engine;
- F05 Treatment allocator bytes;
- pressure ontology/capacities;
- deterministic gates;
- blind thresholds;
- 8 LOW / 8 MEDIUM / 8 HIGH;
- max 2 cases/work.

## Seals
- R3 control-precheck hold receipt SHA256: `2a4030835d4f91818c64f5727a7b1f46f3be59a0990cc5409612ef3e631f1618`
- R4 preregistration JSON SHA256: `fda646218953bb574bb5ba1ab48bc2e4a1e614a36aa195e21cf5af2489a02320`
- Primary Materialization Protocol R3 SHA256: `99c8122f91d2a525c30970bae2e4ff22bd6e2483afc6d4f60aae3a9f64e328c0`
- R4 preexecution seal SHA256: `a4346776dfcbc5e0c3c8f8a116dd8a220b5586506091aefb87f9e114f1896960`

## Claim boundary
Planning/allocation layer only. No Production, Active Runtime, DB authority, or operational Level-3 change.
