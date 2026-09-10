# P07-I4K-2P R2 Field-Budgeted Propagation Replication — HOLD Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-2P-R2-FIELD-BUDGETED-PROPAGATION-REPLICATION`
Preregistration commit: `34ef87d75ea7974c67c8487b8c34a9a7d33d283b`
Classification: DEVELOPMENT / PREFORMAL / PRESCORE INTEGRITY HOLD
Final verdict: `HOLD__BASELINE_FIELD_LEVEL_BUDGET_MISS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`

## Prospective integrity
The exact GitHub preregistration was sealed with `outputs_before_execution=0`. It froze parent Research Sync R7, fresh synthetic world, 12 BASELINE + 12 PROPAGATION candidates, identical neutral schema, field-level representation budgets, State Attachment for both arms, Second-Order Propagation for Treatment, the 7 masked evaluation axes, hard gates, and H1-H4.

## Prescore result
- BASELINE 12/12 had at least one field-budget violation.
- `future_carry` below minimum: 12/12.
- `second_order_consequence` below minimum: 10/12.
- `coincidence_guard` above maximum: 1/12.
- PROPAGATION field budgets: 12/12 PASS.
- Total arm-mean representation gap: 0.056506, within the frozen <=0.08 gate.
- No candidate was edited after final emission.
- Secret mask 0 / blind scores 0 / unblind 0 / H1-H4 effect verdict 0.

## Root cause
Field budgets existed as generation instructions but there was no fail-closed pre-emission admission gate. Baseline realization compressed second-order and future-carry fields below the frozen minima even though total length remained comparable.

## Claim / repair boundary
This is not a scientific H1-H4 FAIL. It is a prescore integrity HOLD. Do not extend or rewrite the emitted candidates. A fresh retry must use a new experiment ID and define provisional drafts as non-output until deterministic field-budget admission succeeds identically for both arms. Rejected provisional drafts may be regenerated only before final emission; after final arm emission no rewrite/regeneration is allowed.

Preregistration authority note: the GitHub blob at commit `34ef87d75ea7974c67c8487b8c34a9a7d33d283b` is Primary Evidence. Recovery copies may have different byte hashes due formatting but do not supersede the GitHub preregistration.