# R74 F05 Symmetric Semantic-Transaction Measurement — Recovered Final Closure Report R1

Date: 2026-09-24
Recovery status: CONSOLIDATED_FROM_SEALED_R74_HUB_ARTIFACTS_AND_DURABLE_PROGRESS_RECORD
Authority effect: NONE

## Final status

CLOSED_NO_EFFICACY_VERDICT__CANONICAL_R127_RAW_ACCESS_BLOCKED

F05 remains NOT QUALIFIED.

## Purpose

Repair the R73 measurement asymmetry by forcing exact-R69 Control and unchanged R72-F05 Treatment through one shared arm-independent semantic representation and the same frozen R68 F04 / R69 F06 validators.

## Frozen authority

- Physical Authority: SYNC-R72
- Active Runtime: exact R69
- Runtime SHA256: 3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1
- Treatment allocator: unchanged R72 F05 Adaptive Pressure Allocator R2
- Allocator SHA256: 9aa36906be260b3ae734340e0d9be951692a18088bc1a40ae5c829e166088c0f
- Canonical R74 preregistration SHA256: 8ae36a1a2c56b147bb76181b6b9f9a16e979977c3ec6d34fd74c0be7e61cf0dd
- Expected canonical DB64-R127 logical SHA256: 4703e9a99da2deb66eef08f09b08141db6c4d19bc76f77d1c8159dcb7633d6e7

## Measurement bridge

R3 bridge SHA256:
a68f463177310d3857dd773811ba05400248e65436d686a81087184df1d4a6a7

R3 narrow repair:
- absent transaction_obligation_ids => unresolved/fail-closed
- present empty transaction_obligation_ids: [] => valid obligationless scene
- obligationless non-RESOLVE scenes excluded from F04 obligation-level semantic repetition
- obligationless scenes remain eligible for F06 removal/merge testing

No F04 threshold, F06 rule, allocator, generation rule, or efficacy threshold changed.

## Stage M qualification

Final:
PASS__M1_M7_ALL_PASS__R68_F04_16_OF_16__R69_F06_16_OF_16

Gates:
- M1 Identity parity: PASS
- M2 Arm-swap invariance: PASS
- M3 Serialization invariance: PASS
- M4 R68 F04 regression: 16/16 PASS
- M5 R69 F06 regression: 16/16 PASS
- M6 Missing-semantic fail-closed: PASS
- M7 Code boundary: PASS

Clean Actions:
- run 35736951547
- artifact 10697258101
- artifact digest 5e8807593307b9242e2c95c3b43f47c6c0462bf5b1ba4a8c87b63c55a5a91469

## Primary freeze harness

Harness:
research/interventions/20260922/r74_primary_materialize_freeze_r1.py

Clean self-test:
- run 35738334936
- job 106781235547
- PASS
- deterministic 24-case selection
- max 2/work
- >=12 works
- incomplete exclusion custody fails closed
- prose generation bytes 0

## Exclusion-custody recovery

Initial Hub audit found R72 R2/R3/R4/R5 exact primary IDs unavailable outside historical C2.
During the later session, historical C2 was inspected and R3/R4 deterministic selections / historical failure anchors were reproduced; R72 exclusion custody was recovered sufficiently for the later recovery freeze work recorded in:
research/interventions/20260923/R74_R75_R76_PROGRESS_R1.md

Preserved later findings:
- R72 R2/R3/R4/R5 exclusion custody recovered
- R3/R4 historical selection anchors reproduced
- R4 historical 20-OK / 4-pattern-fail precheck reproduced

## Why no efficacy verdict

The sealed R74 primary requires exact canonical DB64-R127 raw authority.

The original R127 parts remained in Library custody, but the active file-service boundary did not permit direct raw-byte materialization and full current-session byte verification of the expected logical SHA.

A temporary cohort enumerated from R128 root planner paths was discovered to be noncanonical because the sealed harness requires R127 consumer_ready_r53 enumeration.

That execution was explicitly invalidated before scoring:
INVALIDATED_PRE_SCORE__NONCANONICAL_COHORT_ENUMERATION

Therefore:
- no primary efficacy PASS
- no primary efficacy FAIL
- F05 remains NOT QUALIFIED
- no Production change
- no Runtime authority change
- no Operational Level-3 change
- no R140 effect

## Canonical R74 source files

Preregistration:
research/interventions/20260922/R74_F05_SYMMETRIC_SEMANTIC_TRANSACTION_MEASUREMENT_BRIDGE_PREREG_R1.md

Bridge implementation:
research/interventions/20260922/r74_symmetric_semantic_measurement_bridge_r3.py

Stage-M result:
research/interventions/20260922/R74_STAGE_M_QUALIFICATION_RESULT_R1.md

Freeze harness result:
research/interventions/20260922/R74_PRIMARY_FREEZE_HARNESS_QUALIFICATION_R1.md

Historical custody audit:
research/interventions/20260922/R74_PRIMARY_EXCLUSION_CUSTODY_AUDIT_R1.md

Later consolidated closure:
research/interventions/20260923/R74_R75_R76_PROGRESS_R1.md

## Resume rule

Do not reopen R74 by default.

Only reopen if exact canonical R127 bytes are available for a preregistration-faithful replay.
The strategic research path has moved on: R75 -> R76 -> R77-H0/H1.
