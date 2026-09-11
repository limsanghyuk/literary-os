# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
SYNC-R31 root `22b5d1fd1a03d5a3c06a5c23825b3d64da030f9122dfdb46245631e0ff5ffe86`.

## EXACT STATE
R4A: G6/G7 PASS; provider HOLD; Judges=0; Mapping open=0; no surface mutation.
Evolution: I4C historical rationale=`MIXED_QUALITATIVE_SIGNAL`; unused-scene annotation replication=`PACKETS_SEALED__RESPONSES_0__REPLICATION_MAPPING_CLOSED`.

## MANDATORY RESUME ORDER
1. Read `handoff/20260912/START_HERE_SYNC_R31_I4C_ANNOTATION_PACKETS_SEALED_NEW_SESSION_HANDOFF_R1.md` and verify SYNC-R31 root.
2. Do not open either R4A or replication mapping.
3. Obtain J01/J02/J03 responses from genuinely independent fresh evaluators only.
4. Validate and seal three valid responses; malformed response replacement is allowed only before mapping open and without inspecting aggregate outcomes.
5. Only then regenerate/open replication mapping, verify hash `46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`, and apply frozen thresholds.
6. Never coordinator-self-judge.
7. Immediately reseal physical packages after any meaningful result change.
