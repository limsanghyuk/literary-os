# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
**SYNC-R33** root `39487b9dc0ff12e2c75c16a1d5d8d7192dfb53e1ef14dc71d03c4474f1541d87` is the latest fully physicalized and twice-audited authority.

## READ THESE FIRST AFTER CONTROL-FIRST PACKAGE REVIEW
1. `handoff/20260912/START_HERE_SYNC_R33_PHYSICAL_AUTHORITY_I4C_MIXED_WEAK_NEW_SESSION_HANDOFF_R1.md`
2. `handoff/20260912/SYNC_R33_DELIVERY_MANIFEST_R1_20260912.json`
3. `handoff/20260912/SYNC_R33_PHYSICALIZATION_COMPLETION_RECEIPT_R1_20260912.json`

## EXACT STATE
R4A:
- G6/G7 PASS
- provider=`HOLD__REAL_PROVIDER_SECRET_ABSENT`
- Judges=0
- Mapping open=0
- exact surfaces frozen

I4C evolution replication:
- J01/J02/J03 valid exact frozen responses
- 3-of-3 gate=`PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED`
- exact replication mapping replay PASS, SHA `46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`
- final decision=`MIXED_OR_WEAK_REPLICATION`
- breadth delta=`+0.875`
- severity delta=`+0.875`
- evaluator direction=`3/3` middle/late worse
- strong breadth/severity thresholds not met
- result is physically propagated in `research_sync_r33/` within CONTROL/A/B2

## R33 PHYSICAL INTEGRITY
Changed roles: CONTROL/A/B2, each with 9 identical R33 overlay entries.
Byte-identical roles: B1/C1/C2-A/C2-B/D1/D2.
Combined C2 SHA=`58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.
Initial full audit PASS and independent fresh-process re-audit PASS, errors=0.

## MANDATORY RESUME ORDER
1. Load and verify SYNC-R33 root/manifest before doing new work.
2. Test container/runtime with a minimal command before large archive operations.
3. Preserve R4A Judges=0 / Mapping open=0.
4. Do not modify frozen I4C results, mappings, response bytes, thresholds or historical scores.
5. If starting new research, preregister a narrow falsifiable craft mechanism on fresh/unseen material before generation/evaluation.
6. Preserve Engine/Production/DB/Formal boundaries unless a later qualified promotion explicitly changes them.

## FAILURE MODE
If container transport fails, do not fabricate a successor sync. Keep SYNC-R33 physical authority, record the runtime incident, and resume from the exact R33 9-transport hashes/root in a functioning session.

## STATUS TOKEN
`RECOVER_FROM_SYNC_R33__I4C_MIXED_WEAK_PROPAGATED__R4A_MAPPING_CLOSED__NEXT_MECHANISM_NOT_YET_PREREGISTERED`
