# START HERE — SYNC-R39 Branch Reconciliation R1

Date: 2026-09-15

## Mandatory physical read order

`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

Current physical research authority:

`SYNC-R39`

Transport root SHA256:

`e60bd46e5f9e41614aaa3a2a227eb8a6fe4a0175e3684ae5180178ae7cc12009`

Parent authority:

`SYNC-R38` root `4611c1e5e0ff9c2ec22750817d5471b06781c018c66d66e9dabd221eac430d9c`

## Scientific reconciliation

Canonical A2R35 is the first completed branch sealed in SYNC-R38:

`PASS 10W / 2T / 0L`, nonloss `12/12`, Mechanical PASS.

A later same-preregistration rerun that produced `FAIL 8W / 1T / 3L` is quarantined as:

`DUPLICATE_BRANCH_NOT_SCORED__AUXILIARY_DIAGNOSTIC_ONLY`

A2R36 was opened from that duplicate FAIL branch and is therefore:

`ABORTED_NOT_SCORED__INVALID_DUPLICATE_PARENT__OUTPUTS_0`

## Current Level-3 Entry state

- E2 DB64 Fuel / Full-Planning Qualification: `CLOSED_PASS`
- E1 Clean Independent/Human Plan-to-Surface Closure: OPEN
- E3 Fresh Whole-Episode Integration: PENDING
- E4 >=3 Episode State Carry: PENDING
- E5 Fault Injection / Autonomous Recovery: PENDING
- E6 Formal Level-3 Qualification: PENDING

Maturity remains:

`PRE_LEVEL_3__LEVEL_3_ENTRY_QUALIFICATION_IN_PROGRESS`

Level 3 has not been entered. Level 4 has not started.

## Stable authority boundaries

- Active Engine: `P07-I4H Recovery R3`
- Production Engine: `ENG:R47`
- Formal scored total: `137`
- Latest Formal: `R138`
- Formal R140: `0/0/0`
- DB59 historical benchmark SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- DB64 candidate SHA256: `19f3c446a73408045d02d4d99e168251dca42da3bfa00abaff1d8f9159d7ea46`
- DB64 is not Production DB.

## Next action

Do not resume A2R36. Proceed from E1 Clean Independent/Human Plan-to-Surface Closure using fresh sealed inputs and independent/human evaluation, then proceed to E3 only after E1 closes.
