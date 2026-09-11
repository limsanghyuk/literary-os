# START HERE — SYNC-R32 NEW SESSION HANDOFF R1

## READ ORDER
CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2.

## CURRENT PHYSICAL AUTHORITY
SYNC-R32 root `b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb`.
Physical closure: `handoff/20260912/SYNC_R32_I4C_INGESTION_GATE_READY_PHYSICAL_CLOSURE_R1_20260912.md`.
Manifest: `handoff/20260912/SYNC_R32_I4C_INGESTION_GATE_READY_DELIVERY_MANIFEST_R1_20260912.json`.
Audit: `handoff/20260912/SYNC_R32_I4C_INGESTION_GATE_READY_PHYSICAL_AUDIT_R1_20260912.json`.

## R4A TRACK
G6 PASS and G7 PASS. Real provider credential was rechecked and remains absent (`HOLD__REAL_PROVIDER_SECRET_ABSENT`). Exact surfaces remain frozen. Mask=1; independent judges=0; mapping open=0. Never self-judge and never open R4A mapping before exactly three valid independent judge packets are sealed.

## I4C EVOLUTION REPLICATION TRACK
Historical qualitative result=`MIXED_QUALITATIVE_SIGNAL`. Fresh unused-scene replication packets are already sealed. Original Stage-B scenes were excluded. J01/J02/J03 responses=0. Replication mapping remains closed and is not present in the nine physical transports.

The response validator and 3-of-3 gate are now sealed and tested:
- Validator commit `d976132e38f1c7baaf5beb57aebe06de456fc6bf`.
- 3-of-3 gate commit `9ad7c0ca7751ca3111e007aad711711fac5eb419`.
- Tooling seal commit `3f6eca77e65a0be4818084d480ad4c698e6f5896`.

## EXACT NEXT LEGAL ACTION
1. Obtain three genuinely independent J01/J02/J03 evaluator response JSONs under the sealed response contract.
2. Validate each response without opening replication mapping.
3. Run the 3-of-3 gate. Only `PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED` permits mapping open.
4. Then open replication mapping exactly once and compute the preregistered positional replication decision. Do not change thresholds after any response is seen.
5. Immediately physical-propagate the result into the next SYNC before further research if session interruption risk remains.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Formal scored total 137; latest Formal R138; Formal R140 `0/0/0`.

## STATUS TOKEN
`SYNC_R32__I4C_PACKETS_SEALED__RESPONSES_0__INGESTION_GATE_READY__REPLICATION_MAPPING_CLOSED__R4A_PROVIDER_HOLD__JUDGES_0__R4A_MAPPING_CLOSED`
