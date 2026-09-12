# CURRENT HANDOFF POINTER
Last updated: 2026-09-12

## READ FIRST
After reading the physical packages in order `CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`, read:

`handoff/20260912/START_HERE_SYNC_R33_PHYSICAL_AUTHORITY_I4C_MIXED_WEAK_NEW_SESSION_HANDOFF_R1.md`

## CURRENT PHYSICAL AUTHORITY
**SYNC-R33** root `39487b9dc0ff12e2c75c16a1d5d8d7192dfb53e1ef14dc71d03c4474f1541d87` is the latest fully materialized and twice-audited physical authority.

Delivery manifest:
`handoff/20260912/SYNC_R33_DELIVERY_MANIFEST_R1_20260912.json`

Physicalization completion receipt:
`handoff/20260912/SYNC_R33_PHYSICALIZATION_COMPLETION_RECEIPT_R1_20260912.json`

## CURRENT RESEARCH STATE
The post-R32 I4C unused-scene replication is now physically included in R33:
- J01/J02/J03 valid and sealed
- 3-of-3 gate PASS
- exact I4C mapping byte replay PASS
- final decision=`MIXED_OR_WEAK_REPLICATION`
- breadth delta `+0.875`
- severity delta `+0.875`
- evaluator directional agreement `3/3`

R4A remains separately frozen: Judges=0 / Mapping open=0.

## EXACT NEXT ACTION
R33 physicalization is closed. The next research action, if undertaken, must begin with a new preregistration on fresh/unseen material for a narrow reproducible craft mechanism. Do not patch the renderer generically from the mixed/weak result. Preserve all Engine/Production/DB/Formal boundaries unless a later qualified promotion explicitly changes them.

## STATUS TOKEN
`CURRENT_HANDOFF__PHYSICAL_SYNC_R33__I4C_MIXED_OR_WEAK_PROPAGATED__R4A_MAPPING_CLOSED__NEXT_MECHANISM_NOT_YET_PREREGISTERED`
