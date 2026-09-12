# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
SYNC-R32 root `b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb` remains the latest fully physicalized/audited authority.

## READ THESE FIRST AFTER CONTROL-FIRST PACKAGE REVIEW
1. `handoff/20260912/POST_R32_CURRENT_AUTHORITY_SNAPSHOT_R2_20260912.md`
2. `handoff/20260912/START_HERE_POST_R32_I4C_MIXED_WEAK_R33_PHYSICALIZATION_PENDING_NEW_SESSION_HANDOFF_R2.md`

## EXACT STATE
R4A:
- G6/G7 PASS
- provider=`HOLD__REAL_PROVIDER_SECRET_ABSENT`
- Judges=0
- Mapping open=0
- exact surfaces frozen

I4C evolution replication:
- J01/J02/J03 valid and sealed
- 3-of-3 gate=`PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED`
- exact replication mapping replay PASS, SHA `46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`
- final decision=`MIXED_OR_WEAK_REPLICATION`
- breadth delta=`+0.875`
- severity delta=`+0.875`
- evaluator direction=`3/3` middle/late worse
- strong breadth/severity thresholds not met

Post-R32 result is Hub-sealed but not yet included in the developer's nine physical transports.

## MANDATORY RESUME ORDER
1. Verify all 9 SYNC-R32 package hashes and root.
2. Test container/runtime with a minimal command.
3. Before any new experiment, build SYNC-R33 using `handoff/20260912/SYNC_R33_PENDING_DETERMINISTIC_DELTA_MANIFEST_R1_20260912.json`, commit `b34a5c0437186afa415dfdc7a30d58284c12a8e7`.
4. CONTROL/A/B2 append-only overlay `research_sync_r33/`; unchanged six transports remain exact R32 bytes.
5. Perform full physical audit and seal all 9 transports.
6. Only after audit PASS promote current physical authority to SYNC-R33.
7. Preserve R4A Judges=0 / Mapping open=0.
8. Do not modify the frozen I4C result or thresholds.
9. Only after R33 closure may a next fresh craft-mechanism preregistration begin.

## FAILURE MODE
If container transport fails again, do not fabricate SYNC-R33. Keep R32 physical authority, preserve Hub post-R32 research authority, record the runtime incident, and retry physicalization in a functioning session.

## STATUS TOKEN
`RECOVER_FROM_SYNC_R32__LOAD_POST_R32_R2_AUTHORITY__PHYSICALIZE_R33_FIRST__R4A_MAPPING_CLOSED`
