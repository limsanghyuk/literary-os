# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
SYNC-R32 root `b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb` remains the latest fully physicalized/audited authority.

## EXACT STATE
R4A: G6/G7 PASS; provider=`HOLD__REAL_PROVIDER_SECRET_ABSENT`; Judges=0; Mapping open=0; surfaces frozen.
I4C evolution replication: J01/J02/J03 sealed valid; 3-of-3 gate PASS; I4C replication mapping exact replay SHA PASS; final decision=`MIXED_OR_WEAK_REPLICATION`. I4C replication mapping is legitimately open; R4A mapping remains closed.

Post-R32 result is Hub-sealed but full SYNC-R33 physicalization is pending because the current CAAS/Jupyter/container transport layer repeatedly returns `TransportTimeoutError` even for minimal commands.

## MANDATORY RESUME ORDER
1. Read `handoff/20260912/START_HERE_POST_R32_I4C_MIXED_WEAK_R33_PHYSICALIZATION_PENDING_NEW_SESSION_HANDOFF_R1.md`.
2. Verify SYNC-R32 root `b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb` and confirm container minimal command succeeds.
3. Before any new experiment, build SYNC-R33 using `handoff/20260912/SYNC_R33_PENDING_DETERMINISTIC_DELTA_MANIFEST_R1_20260912.json`, commit `b34a5c0437186afa415dfdc7a30d58284c12a8e7`.
4. Audit and seal all 9 transports; only then promote physical authority to SYNC-R33.
5. Preserve R4A Judges=0 / Mapping open=0.
6. Do not modify the frozen I4C result or thresholds.
7. Only after R33 closure may a next fresh craft-mechanism preregistration begin.
