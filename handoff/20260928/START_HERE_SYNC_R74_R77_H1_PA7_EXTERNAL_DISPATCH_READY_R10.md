# START HERE — SYNC-R74 / R77-H1 PA7 EXTERNAL DISPATCH READY R10

Date: 2026-09-28
Status: **CANONICAL NEW-SESSION HANDOFF**
Supersedes: R9 for research recovery interpretation.
Authority effect: NONE.

## 1. CURRENT AUTHORITY

- Physical Authority: **SYNC-R74**
- Parent: SYNC-R73
- Active Runtime: **exact R69**
- Runtime SHA256: `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Research DB authority: **DB64-R131 research-only**
- Latest externally audited DB candidate: **DB64-R134 — semantic re-audit HOLD**
- Operational Level-3: `SUSPENDED__REQUALIFICATION_REQUIRED`
- Formal latest scored: R138
- Formal R140: NOT_STARTED

No physical successor has completed reseal -> Manifest/Trust Root -> 9/9 delivery -> redownload SHA verification.

## 2. PA7 LATEST VERIFIED SURFACES

Control R4:
- 40,055 chars
- 9 sequences
- 50 scenes
- SHA256 `41f45e7d00dbd9e4a89837cac0c7516c18c5f42fd1edd066015f824f27d36495`
- mechanical status PASS
- immutable

Treatment progression:
- R1: 35,656 chars, FAIL_UNDER_40K_ONLY
- R2: 38,846 chars, FAIL_UNDER_40K_ONLY
- R3 Final: **40,250 chars / 9 sequences / 50 scenes / PASS**
- R3 Final SHA256: `001571fd5ff9b7998a973ced39efa3957ebe515aa06fa8b295c5c2f47cb641ec`
- length difference vs Control: 195 chars = 0.4868% of shorter arm
- identical full scenes: 0
- metadata leak: 0

R2 and R3 were not post-hoc free writing:
- Completion D was preregistered before R2.
- R2 underlength failure was preserved.
- Completion E was preregistered before R3 and restricted to non-blind scenes SC16/SC32/SC45.
- Frozen blind sample remained SC05/12/21/29/38/46.

## 3. PA7 EXTERNAL BLIND DISPATCH

Protocol:
`research/interventions/20260926/R77_H1_PA7_EXTERNAL_3JUDGE_PROTOCOL_R1.json`

Dispatch custody:
`research/interventions/20260928/pa7_external_dispatch_r1/`

Dispatch receipt:
`research/interventions/20260928/pa7_external_dispatch_r1/DISPATCH_BUILD_RECEIPT_R1.json`

Status:
`PASS__3_BLIND_PACKETS__LEAK_0__JUDGE_OUTPUTS_0_OF_3`

Packet hashes:
- J01: `50d8f274286b70b4085d976c3938f1d2f5b58cef0f6397abc60f1c9acafc14e5`
- J02: `eba31aa22ec632638b43e2d8fb6376be82b9587ae3fdea95431f8b5ee81988b2`
- J03: `50d8f274286b70b4085d976c3938f1d2f5b58cef0f6397abc60f1c9acafc14e5`
- each packet chars: 94,330
- mapping present in judge packet: false
- forbidden lineage/internal-score hits: 0
- source surface hashes exposed in packet: false
- prefrozen sample: SC05 / SC12 / SC21 / SC29 / SC38 / SC46

Coordinator mapping:
`research/interventions/20260928/pa7_external_dispatch_r1/COORDINATOR_MAPPING_R1.json`

**DO NOT reveal coordinator mapping until all 3 first schema-valid raw judge judgments are hash-sealed.**

## 4. EXACT NEXT RESEARCH

1. Dispatch J01 packet to a fresh independent evaluator context using only:
   - J01_BLIND_PACKET.txt
   - J01_OUTPUT_SCHEMA.json
2. Seal the first complete schema-valid raw JSON judgment and its SHA256.
3. Repeat independently for J02 and J03. Judges must not see other judge outputs, Project/GitHub, coordinator mapping, system lineage, or prior scores.
4. Only after valid outputs are 3/3:
   - reveal coordinator mapping;
   - compute mapped Control/Treatment whole and surface results;
   - apply frozen Absolute / Paired / Focus / Recoverability gates;
   - do not change the +0.50 / >=4-of-6 focus threshold.
5. If PA7 PASS:
   - rebuild the six R77-H1 launch packets under the >=40K floor;
   - keep the three human targets unopened;
   - run PM0 before any real-provider H1 C/T inference.
6. If PA7 FAIL:
   - preserve the immutable failure;
   - localize the responsible ancestor before any further surface intervention.

## 5. H1 BOUNDARY

- H1 primary C/T outputs: **0**
- Human target story payloads opened: **0**
- Existing six H1 packets embedded in SYNC-R74: `STALE_FOR_EXECUTION__35K_FLOOR`
- Do not execute those historical packets.
- DB64-R134 must not retroactively modify frozen H1 census, selection, Past-Only inputs, hidden targets, or gates.

## 6. CLAIM BOUNDARY

PA7 is a provider-analog matched-length qualification only.
PA7 cannot by itself promote:
- Level-3
- Production
- Runtime
- Runtime DB
- Formal R140

Current project remains PRE-Level-3 / requalification in progress.
