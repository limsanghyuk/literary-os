# R72 — F05 Adaptive Distribution / Count Pressure — Final Closure

Date: 2026-09-22

Final status:
`CLOSED_FAIL__F05_ADAPTIVE_DISTRIBUTION_NOT_QUALIFIED__HIGH_PRESSURE_EFFECT_GATE_FAILED`

## Primary execution
- Winning revision: R5
- Fresh primary cases: 24
- Distinct independently verified DB64 works: 16
- Strata: LOW 8 / MEDIUM 8 / HIGH 8
- Exact R69 Control/Treatment pairs: 24/24 valid
- Blind stage: NOT RUN because deterministic gate G9 failed

## Deterministic gates
- G1 due-now coverage: PASS
- G2 required visible-carrier coverage: PASS
- G3 premature deferred resolution: PASS
- G4 F04 repetition regression: PASS
- G5 F06 unnecessary-scene regression: PASS
- G6 F07 hidden-state contamination: PASS
- G7 R71 visible-causal regression: PASS
- G8 monotonicity: PASS 16/16
- G9 high-pressure effect: FAIL 0/8, required >=6/8
- G10 low-pressure economy: PASS 8/8
- G11 medium-pressure noninferiority: PASS 8/8
- G12 critical violations: PASS, 0

## Interpretation
The frozen HIGH cases did not show a measurable forced-compression/overload deficit in exact R69 Control: all eight Control cases scored zero on the preregistered G9 target. Treatment therefore had no room to produce a strictly smaller violation count. This is a ceiling/no-room-for-improvement result under the frozen metric. R72 thresholds are not changed post hoc.

## Integrity
- R5 preregistration SHA256: `fc4b76f62fe9c38a14abac42a3fda773e0c78ea6aa25b0930be20359c30e85a8`
- R5 case ledger SHA256: `d4398a3568f55258fb664f782f5542431795ab471f944a5df168c5501478a364`
- R5 result SHA256: `a9854210bf21bcc50915cd953abaca6742b150917cc91ba2f5d117ec80292144`
- Final closure receipt SHA256: `a57b6436e6be983109cbb6a0c20d17b3205f902ec004e36733dda3b382e5f5c1`
- Post-result integrity audit SHA256: `3236353df60246db9f7e7734ff71147b5f83b374462d9aa2865b18170341d137`

## Documented protocol metadata deviation
Frozen Materialization Protocol R4 contains a stale `parent_prereg_sha256` field from R2. Actual R5 selection, ledger, and preexecution seal used the sealed R5 preregistration SHA. The 24-case ledger was frozen before primary outputs. The frozen protocol is not rewritten; this discrepancy is preserved as a documentation metadata deviation.

Therefore describe R72 as a frozen-ledger negative result with a documented protocol metadata deviation, not as pristine zero-deviation protocol compliance.

## Authority effect
No Active Runtime change, Production promotion, DB authority change, R70 closure, Formal R140 start, or Operational Level-3 restoration.

## Next
Plan a new preregistered successor:
`R73 — F05 High-Pressure Ceiling / Effect-Target Diagnostic`

Do not alter R72 gates or rescore R72 post hoc.
