# R72 — F05 Adaptive Distribution / Count Pressure — Final Closure

Date: 2026-09-22

## Final status

`CLOSED_FAIL__F05_ADAPTIVE_DISTRIBUTION_NOT_QUALIFIED__HIGH_PRESSURE_EFFECT_GATE_FAILED`

## Valid primary execution
Winning revision: **R5**

- fresh cases: 24
- distinct works: 16
- Control/Treatment valid pairs: 24/24
- exact Control: current R69 `adaptive_showrunner_ul16.compile_adaptive_architecture`
- Treatment: frozen R72 F05 allocator R2

## Deterministic gates
PASS:
- G1 due-now coverage
- G2 required visible-carrier coverage
- G3 premature deferred resolution = 0
- G4 F04 semantic repetition regression = 0
- G5 F06 unnecessary-scene regression = 0
- G6 F07 hidden-state contamination = 0
- G7 R71 visible-causal-realization regression = 0
- G8 monotonicity 16/16
- G10 low-pressure economy: **8/8** improved
- G11 medium-pressure noninferiority: **8/8**
- G12 critical violations: **0**

FAIL:
- G9 high-pressure effect: **0/8 improved**, required **>=6/8**

Exact R69 Control already had zero frozen forced-compression/overload violations in all eight HIGH-pressure cases, so under the preregistered metric there was no measured violation for F05 to reduce.

## Consequence
R72 is a scientific FAIL under its frozen gate. F05 is not qualified. Blind judging is not run because deterministic primary gates did not all pass.

This does **not** imply that the allocator is unsafe:
- all required atoms were preserved;
- all required visible carriers were preserved;
- critical violations were zero;
- LOW-pressure allocation economy improved 8/8.

It means the preregistered claim that F05 would reduce HIGH-pressure forced-compression/overload relative to exact R69 Control was not demonstrated.

Do not change the metric post hoc and reinterpret R72 as PASS.

## Revision history
- R1: metrology-scale defect, no primary outputs.
- R2: primary execution HOLD; 5/24 exact Control input-adapter failures; no scientific score.
- R3: Control-only precheck HOLD 22/24; Treatment outputs 0.
- R4: Control-only precheck HOLD 20/24; Treatment outputs 0.
- R5: fresh 24 cases, Control precheck 24/24, primary execution 24/24, scientific FAIL on G9.

## Evidence hashes
- R5 scientific result SHA256: `a9854210bf21bcc50915cd953abaca6742b150917cc91ba2f5d117ec80292144`
- R5 fresh ledger SHA256: `d4398a3568f55258fb664f782f5542431795ab471f944a5df168c5501478a364`
- R5 case-freeze seal SHA256: `190c6f29c37cc2a1f69b415ac8cbbc45e7bb1755772ba2b3c8fe31d30a11b1db`
- R5 Control precheck SHA256: `6e60eb5d5c8025bd793c1fe845e710f825dc4956143864a007e1347b9cbe6353`
- Final closure receipt SHA256: `a57b6436e6be983109cbb6a0c20d17b3205f902ec004e36733dda3b382e5f5c1`

## Authority effect
No Active Runtime promotion.
No Production change.
No DB authority change.
No R70 change.
No operational Level-3 restoration.

## Next research boundary
Before Integrated Closed Narrative Loop Requalification, run a fresh preregistered **F05 high-pressure ceiling / effect-target diagnostic**. R72 itself remains closed FAIL.
