# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-12

## CURRENT PHYSICAL RESEARCH AUTHORITY
Latest fully materialized/audited physical authority remains **SYNC-R32** root `b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb`.

A post-R32 research result exists and is Hub-sealed, but **SYNC-R33 is not yet physical authority**. The developer's current physical set is still the 5 logical Parts / 9 transports of SYNC-R32.

Detailed authority snapshot:
`handoff/20260912/POST_R32_CURRENT_AUTHORITY_SNAPSHOT_R2_20260912.md`

Primary new-session handoff:
`handoff/20260912/START_HERE_POST_R32_I4C_MIXED_WEAK_R33_PHYSICALIZATION_PENDING_NEW_SESSION_HANDOFF_R2.md`

## REQUIRED PHYSICAL READ ORDER
`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

SYNC-R32 delivery manifest:
`handoff/20260912/SYNC_R32_I4C_INGESTION_GATE_READY_DELIVERY_MANIFEST_R1_20260912.json`

Important: R32 packages themselves stop at the earlier I4C ingestion-gate-ready state. The post-R32 Hub documents below are required to recover the actual latest research state.

## R4A TRACK
G6 PASS; G7 PASS; provider=`HOLD__REAL_PROVIDER_SECRET_ABSENT`; Mask=1; independent Judges=0; mapping open=0; exact Control/Treatment surfaces frozen. No R4A H1-H4 verdict exists. R4A mapping remains closed and was not affected by I4C unblind.

## EVOLUTION TRACK — POST-R32 SEALED RESULT
I4C unused-scene independent annotation replication is complete.

- J01/J02/J03: 3 valid independent evaluator responses sealed.
- 3-of-3 gate=`PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED`.
- I4C mapping exact replay expected/replayed SHA=`46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`.
- Mapping replay status=`PASS__EXACT_MAPPING_BYTE_SEAL_REPRODUCED`.
- Final decision=`MIXED_OR_WEAK_REPLICATION`.
- Final result commit=`f808af0a0482ba775bcac4df4128726ad5ac0827`.
- MIDDLE+LATE minus EARLY breadth=`+0.875`, severity=`+0.875`.
- Evaluator directional agreement=`3/3` middle/late worse.
- Frozen strong-positive thresholds breadth=`+1.0`, severity=`+2.0`, direction=`>=2/3`; therefore breadth FAIL, severity FAIL, direction PASS.
- This is knowledge-only and does not authorize a generic renderer intervention or any authority promotion.

## R33 PHYSICALIZATION BOUNDARY
Deterministic R32→R33 delta manifest:
`handoff/20260912/SYNC_R33_PENDING_DETERMINISTIC_DELTA_MANIFEST_R1_20260912.json`

Delta manifest commit:
`b34a5c0437186afa415dfdc7a30d58284c12a8e7`

R33 mutation rule:
- append-only changed: CONTROL/A/B2 under `research_sync_r33/`
- byte-identical: B1/C1/C2-A/C2-B/D1/D2
- only after full physical audit PASS may CURRENT PHYSICAL AUTHORITY advance to R33.

## NEXT LEGAL ACTION
Before any new scientific experiment:
1. Verify all nine SYNC-R32 transports and root.
2. Verify a functioning container/runtime with a minimal command.
3. Full-physicalize SYNC-R33 from exact R32 parent bytes plus the sealed deterministic delta.
4. Audit and close all nine transports.
5. Only then consider a new fresh craft-mechanism preregistration.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 frozen SHA `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Formal scored total `137`; latest Formal `R138`; Formal R140 `0/0/0`.

## STATUS TOKEN
`PHYSICAL_SYNC_R32__HUB_POST_R32_I4C_MIXED_OR_WEAK__R33_PHYSICALIZATION_REQUIRED_FIRST__R4A_JUDGES_0_MAPPING_CLOSED`
