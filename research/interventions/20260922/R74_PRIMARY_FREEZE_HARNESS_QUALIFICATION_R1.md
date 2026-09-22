# R74 Primary Freeze Harness Qualification R1

Date: 2026-09-22

Status:
`PASS__HARNESS_QUALIFIED__SCIENTIFIC_PRIMARY_NOT_STARTED`

## Scope
This qualifies only the deterministic materialization/freeze harness:
`research/interventions/20260922/r74_primary_materialize_freeze_r1.py`

The harness generates **no literary prose** and does not execute R74 Control or Treatment.

## GitHub Actions clean self-test
- PR: #20
- trigger head SHA: `de3e630360e49f3130513a2c6c5ef899c19c365c`
- workflow: `R74 Primary Freeze Harness Selftest`
- run ID: `35738334936`
- job ID: `106781235547`
- conclusion: **success**

## Self-test result
- status: PASS
- synthetic candidates: 48
- deterministic selected cases: 24
- selected distinct works: 15
- max-two-per-work rule: PASS
- missing-R4 exclusion custody injected: fail-closed behavior PASS
- literary prose generation bytes: 0

## Qualified behavior
The harness:
1. verifies DB64 part01 / part02 / logical SHA256;
2. checks logical ZIP CRC;
3. enumerates consumer_ready_r53 planner inputs;
4. verifies required planner / thick / arc and referenced thread-state artifacts;
5. applies R71-work and SOURCE-HOLD exclusions;
6. requires complete R72 R2/R3/R4/R5 exclusion custody;
7. requires the exact 41-case R73 Stage-A exclusion manifest;
8. selects exactly 24 fully fresh cases deterministically using
   `SHA256(preregistration_sha256|case_id)`, max 2/work, >=12 works;
9. freezes ledger and selected DB64 input bundle before any Control/Treatment output.

## Claim boundary
Harness PASS does not imply:
- R74 primary execution;
- F05 efficacy;
- F05 qualification;
- Production promotion;
- Level-3 restoration.

Current scientific primary outputs remain 0.
