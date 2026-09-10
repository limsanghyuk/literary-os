# P07-I4K-2P R4 — Arm-Parity HOLD Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-2P-R4-BROAD-BUDGET-PREEMISSION-GATED-PROPAGATION-REPLICATION`
Primary preregistration commit: `3dbe53c88aa4030ca20bcca5481e7477d835bbdd`
Verdict: `HOLD__ARM_LEVEL_FIELD_MEAN_PARITY_FAIL__NO_FINAL_ARMS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`

All 12 matched pairs passed individual broad budgets and pair-total parity. Arm mean total gap was `0.0304989 <= 0.05`. State Attachment and Treatment Propagation requirements were satisfied in the admitted provisional pool.

Final-arm parity failed only because `second_order_consequence` field-mean relative gap was `0.1566265 > 0.10`; `future_carry` was `0.0919067` and passed. No final arm was emitted. Mask 0 / blind scores 0 / unblind 0 / H1-H4 effect verdict 0. No candidate was repaired after admission.

Root cause: the parity design applied the same <=10% field-mean constraint to a mechanism-bearing target field. Treatment necessarily allocates more of the same total representation budget to explicit second-order transfer/decision structure, so equalizing that target field itself suppresses the intervention rather than controlling a nuisance confound.

Repair boundary: a fresh retry may retain identical broad per-candidate budgets, pair-total <=5%, arm-total <=5%, and <=10% field-mean parity for non-target representation fields, while prospectively exempting `second_order_consequence` and `future_carry` from cross-arm field-mean parity. These target fields remain individually bounded by the same broad budgets in both arms. Effect H1-H4 thresholds must remain unchanged. I4K-3 remains unauthorized.

Authority note: a later duplicate preregistration commit `647dfe8c369fa6eaf208458c8864fd820d3c3fc2` was created after the earlier valid prereg and is non-authoritative; Primary preregistration evidence is commit `3dbe53c88aa4030ca20bcca5481e7477d835bbdd`.