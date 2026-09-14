# A2R35 Branch Reconciliation R1

Date: 2026-09-15

## Decision

`CANONICAL_R38_PASS_BRANCH_RETAINED__LATER_RERUN_QUARANTINED`

The canonical A2R35 branch is the first completed branch physically incorporated into SYNC-R38:

- A2R35 result: `PASS 10W / 2T / 0L`
- Treatment nonloss: `12/12`
- Mechanical gate: PASS
- plan SHA256: `a0d68a37a3eb1e48be5aeb714c4fa63345038e034dd2f404342b891f97ed220a`
- mapping SHA256: `1d640d5a518fe49bf0f4c5a965c3d7265f104bd136aef703576faec77988cd06`
- blind judgment SHA256: `a42f299529d9b7ee22c1e1dbb1702ee68bb9fa560888a190204eeff8bb08fc03`
- final result SHA256: `b6e727dbadcc25f2fc81394e143e1b26664b0cfdec34067749d6df9f7c444168`
- closure SHA256: `fa0b8e0795f40477205dc728406eaedc4ee3f9347e2db92e0d1ee7c10396e201`
- E2: `CLOSED_PASS`

A later 2026-09-15 local branch reused the same A2R35 experiment/preregistration but produced different plan/mapping/judgment/closure bytes and `FAIL 8W / 1T / 3L`:

- plan SHA256: `82ae28c13b7952c5d4213489bee43c962da264f3a6fb8f70e42fd61f69c09132`
- mapping SHA256: `b732b3fde15ef126dd6d958ba5832114ed6404974680356befb3caf9b09587ad`
- blind judgment SHA256: `000a89b1d93857b5b3b4ba169db32c3012d04862a192e63caa169b0d940eca1e`
- closure SHA256: `6387f78d84cab1a25e87d73c79e4387127cc5ea0ae3465126ac08a7b84653b14`

Because a completed preregistration may not be rerun, rescored, or relabeled after unblind and immutable closure, the later branch is classified:

`DUPLICATE_BRANCH_NOT_SCORED__AUXILIARY_DIAGNOSTIC_ONLY`

It may not alter the canonical A2R35 result or E2 authority.

## A2R36 disposition

A2R36 was opened from the later duplicate A2R35 FAIL branch. Therefore:

`A2R36 = ABORTED_NOT_SCORED__INVALID_DUPLICATE_PARENT__OUTPUTS_0`

A2R36 may not resume.

## Current scientific state

- A2R35 canonical: `PASS 10W/2T/0L`
- E2 DB64 Fuel / Full-Planning Qualification: `CLOSED_PASS`
- DB64 remains non-Production.
- Active Engine remains `P07-I4H Recovery R3`.
- Production Engine remains `ENG:R47`.
- Formal scored total remains `137`, latest Formal `R138`, R140 `0/0/0`.
- Maturity remains `PRE_LEVEL_3__LEVEL_3_ENTRY_QUALIFICATION_IN_PROGRESS`.
- Level 3 not entered.
- Level 4 not started.

## Next gate

`E1_CLEAN_INDEPENDENT_HUMAN_SURFACE_CLOSURE`

After E1: `E3 -> E4 -> E5 -> E6 -> LEVEL_3_ENTERED` only if all gates PASS.

## Physical synchronization

This reconciliation is physically incorporated into audited `SYNC-R39`.

SYNC-R39 transport root SHA256:

`e60bd46e5f9e41614aaa3a2a227eb8a6fe4a0175e3684ae5180178ae7cc12009`
