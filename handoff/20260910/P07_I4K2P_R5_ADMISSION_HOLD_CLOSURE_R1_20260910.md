# P07-I4K-2P R5 — Pre-Emission Admission HOLD Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-2P-R5-TARGET-FIELD-AWARE-PARITY-PROPAGATION-REPLICATION`
Preregistration commit: `b2a074f777de085fb5692178de559926f58dd109`
Final verdict: `HOLD__ONE_BASELINE_SLOT_EXHAUSTED_ADMISSION_ATTEMPTS__NO_FINAL_ARMS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`

Target-aware parity worked as intended. Target fields `second_order_consequence` and `future_carry` were no longer forced to cross-arm mean equality while identical broad individual budgets and total verbosity controls remained frozen.

After the frozen maximum three provisional attempts, 23/24 arm members were eligible. All 12 matched-pair total gaps were <=5% in the final provisional pool. The only remaining failure was S03 BASELINE `second_order_consequence` = 43 Unicode chars versus the frozen minimum 45 on attempt 3.

Because the attempt cap was frozen at three, no fourth rewrite was allowed. Final BASELINE arm 0 / PROPAGATION arm 0 / mask 0 / blind scores 0 / unblind 0. No H1-H4 effect verdict exists.

This is an integrity HOLD, not a propagation-effect FAIL. Root cause is residual natural-language realization variance under a too-small provisional attempt allowance after the representation design itself was repaired. A fresh retry may prospectively increase only the pre-emission provisional attempt allowance while preserving all broad field budgets, target-aware parity, State Attachment, Treatment Propagation Contract, hard gates and H1-H4 effect thresholds. I4K-3 remains unauthorized.