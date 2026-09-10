# P07-I4K-2P R3 Pre-Emission Budget-Gated Propagation Replication — HOLD Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-2P-R3-PREEMISSION-BUDGET-GATED-PROPAGATION-REPLICATION`
Preregistration commit: `63a3053b75aaacecfa5fce885578118bbe9829a6`
Final verdict: `HOLD__PREEMISSION_BASELINE_ADMISSION_EXHAUSTED__NO_FINAL_ARMS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`

The preregistered fail-closed admission gate worked. BASELINE provisional drafts were attempted exactly three times, the frozen maximum. Attempt 3 still left every slot with at least one per-field pair-target violation, concentrated mainly in `second_order_consequence` and several `first_order_consequence` fields. The ±4 Unicode-character per-field pair target was too narrow for reliable natural-language realization within three attempts.

No final BASELINE arm was emitted. PROPAGATION attempts were not started. Secret mask 0 / blind scores 0 / unblind 0 / H1-H4 effect verdict 0. No threshold was changed and no emitted candidate was repaired.

Root cause: R3 solved the R2 problem of unenforced field instructions by adding deterministic pre-emission admission, but over-constrained realization with per-field pair targets of ±4 characters. The next fresh retry may preserve the gate, max-attempt receipts, State Attachment and Propagation contracts while returning to the broader field budgets validated in R2 and enforcing representation comparability at pair-total and arm-mean level rather than exact per-field target matching.

This is an integrity HOLD, not a scientific propagation-effect FAIL. I4K-3 remains unauthorized.