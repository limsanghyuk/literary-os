# UL-16 Local/Hub Authority Desynchronization Incident Receipt R1

Date: 2026-09-16
Status: `INCIDENT_CLOSED__CANONICAL_R2_REMATERIALIZED__STALE_R1_DERIVATIVES_QUARANTINED__NO_AUTHORITY_CHANGE`

## Incident
During a resumed Multi-work replay turn, the active container still held UL-16 research runtime R1 while the Hub CURRENT pointer had already advanced to canonical UL-16 R2.

Hub canonical R2:
- package: `LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`
- SHA256: `7f71484cd2687262d18104b3a9a5cfe727d003d7ed4b616ce8d64702b2da2ca8`
- canonical receipt: `research/upper_layer/20260916/UL16_MAIN_PATH_INTEGRATION_RECEIPT_R2.md`
- authoritative Multi-work replay: `research/upper_layer/20260916/UL16_R2_MULTIWORK_STRUCTURAL_REPLAY_RECEIPT_R1.md` — 12/12 PASS.

Stale local R1 lineage:
- prior package SHA256: `c1dfda09c97771f56aa88adc402c8fe05a03c0fd2b93205b83dafdc8d2101441`.

A local 61-work aggregate replay and owner-concentration repair were executed against that stale R1 lineage before the Hub/local mismatch was noticed. Those local results are explicitly **NON-AUTHORITATIVE** and do not supersede R2 or its already sealed 12-work replay.

## Root cause
The container file surface does not automatically advance when Hub research authority advances. A similar or identical filename in `/mnt/data` is not authority evidence. The missing precondition was:

`fetch CURRENT pointer -> resolve canonical SHA -> hash local bytes -> require exact match before import/execution`.

## Resolution
1. The stale R1-derived local packages were renamed/quarantined with `STALE_R1_DERIVED_NONAUTHORITATIVE`.
2. Their persistent Library copies were also renamed/quarantined and are not CURRENT candidates.
3. The exact canonical R2 Library file was materialized into the active container as:
   `/mnt/data/LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_CANONICAL_20260916.zip`.
4. Reverification:
   - size `18,681,762` bytes;
   - SHA256 `7f71484cd2687262d18104b3a9a5cfe727d003d7ed4b616ce8d64702b2da2ca8` — exact Hub match;
   - ZIP CRC PASS;
   - `memory.events max` delta 0;
   - OOM/OOM-kill 0.
5. New mandatory precheck: `handoff/20260916/RUNTIME_CONTAINER_HUB_AUTHORITY_SYNC_GATE_R6.md`.

## Authoritative research state after closure
The previously sealed canonical R2 Multi-work replay remains authoritative:
- stratified 12-work panel;
- 12/12 PASS;
- due/defer loss 0;
- future-source use 0;
- sequence range 9..19;
- scene range 77..138;
- structural workload vs scene-budget Spearman rho 0.8392;
- Canonical validation errors 0.

The next research transaction remains the cutoff-safe semantic architecture audit described by `CURRENT_NEXT_RESEARCH_POINTER.md`.

## Authority impact
None. Physical baseline SYNC-R53, Production ENG:R47, Candidate Base P07-I4H Recovery R3, DB59 runtime authority and Formal authority are unchanged.

## Status token
`UL16_AUTHORITY_DESYNC_INCIDENT__CLOSED__STALE_R1_REPLAY_NONAUTHORITATIVE__CANONICAL_R2_BYTES_REMATERIALIZED_SHA_MATCH_CRC_PASS__R6_SYNC_GATE_REQUIRED__NEXT_SEMANTIC_ARCHITECTURE_AUDIT`
