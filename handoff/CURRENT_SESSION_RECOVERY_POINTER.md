# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
SYNC-R28 root `ceb12269eb7562d472e8e375cd78e3f1cbce873bcab4721f9f3baaa9ef131f10`.

## EXACT STATE
R4A surfaces frozen; G6 PASS; G7 PASS; provider secret absent; Mask=1; Judges=0; Mapping open=0. Do not regenerate surfaces/mask or open mapping.
Whole-Episode Degradation Diagnostic is complete with `MIXED_SIGNAL`; result commit `9d6b341f206162eff11e0d937adc4df4255feb9f`.

## MANDATORY RESUME ORDER
1. Read `handoff/20260912/START_HERE_SYNC_R28_WHOLE_EPISODE_MIXED_SIGNAL_NEW_SESSION_HANDOFF_R1.md` and verify SYNC-R28 root.
2. For evolution work, preregister residual whole-episode craft-drift diagnostic BEFORE any new measurements.
3. Use sealed historical surfaces only and keep result knowledge-only.
4. If real provider becomes available, R4A resumes separately with exactly 3 independent judge calls/conversations; keep mapping closed until all 3 score packets seal.
5. Immediately reseal physical packages after meaningful state changes.