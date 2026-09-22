# R73 — F05 High-Pressure Ceiling / Effect-Target Diagnostic — Final Closure

Date: 2026-09-22

Final status:
`CLOSED_DIAGNOSTIC_PASS__STAGE_B_EFFICACY_INVALIDATED_METRIC_NONCOMPARABILITY__F05_NOT_QUALIFIED`

## Stage A — valid diagnostic finding
- Fresh HIGH exact-R69 Controls: 41
- Old R72 G9 headroom: **0/41**
- Preregistered economy headroom: **41/41**
- Post-audit allocation-only headroom: **0/41**
- F04 semantic-repetition headroom: **41/41**

This confirms the R72 high-pressure old-G9 target had a ceiling/no-room-for-improvement problem.

## Stage B — mechanically executed, efficacy invalidated
24/24 Treatment outputs completed and the preregistered numerical gates were mechanically satisfied. However, all Control economy violations came from F04 semantic transaction repetition while Treatment allocator output had no equivalent semantic-transaction representation and therefore was not passed through the same F04 validator.

The apparent 24/24 economy improvement is **not admissible as a causal efficacy result**.

Metric comparability audit SHA256:
`9a8e38c5adc8055f81b4676465d9ada1dd2fcc6878ab8c622029ce241aa5dbaf`

Stage-B raw result SHA256:
`35c268423ffa209b391a9b9497c2168fcb265cfb553eeb031090163a07f65395`

Final closure JSON SHA256:
`e0971a74fc1165dd85e661849376aea93996e02fee35c3e4e9621d3570024a45`

## Scientific conclusion
R73 successfully diagnoses a measurement-boundary problem. The high-pressure issue is not captured by old-G9 compression/overload, but the alternative semantic-repetition signal cannot be compared until both arms are represented and measured symmetrically.

F05 remains **NOT QUALIFIED**. R72 remains **CLOSED FAIL**. Production, DB authority, Operational Level-3, and Formal R140 are unchanged.

## Next research
`R74 — F05 Symmetric Semantic-Transaction Measurement Bridge`

Status:
`PLANNED__NOT_STARTED__FRESH_PREREGISTRATION_REQUIRED`

R74 must apply the exact same F04/F06 validators to semantically comparable Control and Treatment structures before any efficacy claim.
