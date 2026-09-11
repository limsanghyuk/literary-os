# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
SYNC-R32 root `b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb`.

## EXACT STATE
R4A: G6/G7 PASS; provider recheck=`HOLD__REAL_PROVIDER_SECRET_ABSENT`; Judges=0; Mapping open=0; no surface mutation.
Evolution: I4C historical rationale=`MIXED_QUALITATIVE_SIGNAL`; unused-scene annotation replication=`PACKETS_SEALED__RESPONSES_0__INGESTION_GATE_READY__REPLICATION_MAPPING_CLOSED`.

## MANDATORY RESUME ORDER
1. Read `handoff/20260912/START_HERE_SYNC_R32_I4C_INGESTION_GATE_READY_NEW_SESSION_HANDOFF_R1.md` and verify SYNC-R32 root.
2. Do not open either R4A or replication mapping.
3. Obtain J01/J02/J03 response JSONs from genuinely independent fresh evaluators only.
4. Validate each response with the sealed validator.
5. Run the sealed 3-of-3 gate; only PASS authorizes replication mapping open.
6. Then open replication mapping once, verify its SHA `46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`, and apply the frozen preregistered thresholds.
7. Never coordinator-self-judge; immediately reseal physical packages after any meaningful result change.
