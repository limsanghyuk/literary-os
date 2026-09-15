# START HERE — SYNC-R50 / E6-R1 IMMUTABLE FAIL

Date: 2026-09-15

## CURRENT PHYSICAL AUTHORITY
`SYNC-R50`

Root SHA256:
`811cb8557811778de36bb5b1c3404f679a779c71728b76fae0b093b9680e989c`

Parent: `SYNC-R49`
Parent Root:
`ceea3188a4acbe5b58fc198f26bc5e3d2e4e64f9163c81664141c7aef7352762`

Required package read order:
`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

## LEVEL-3 ENTRY GATES
- E1: `CLOSED_PASS`
- E2: `CLOSED_PASS`
- E3: `CLOSED_PASS`
- E4: `CLOSED_PASS`
- E5: `CLOSED_PASS`
- E6-R1: `FAIL__E6_FORMAL_LEVEL3_QUALIFICATION__SAFE_NO_COMMIT`
- Level 3: **NOT ENTERED**

## E6-R1 FRESH SAMPLE
`서림항 야간운항센터 / QUAL_EP01 〈등대가 꺼진 밤〉`

Passed before failure:
- Authority/Fresh Seed/Preregistration GitHub-byte identity and SHA256 seal
- E6C1 stale-advisory challenge PASS
- Responsible Ancestor: `RETRIEVAL_ADVISORY / SELECTOR`
- Action: `ABSTAIN_DROP_ADVISORY`
- Planning PASS: 10 sequences / 50 scene contracts / orphan 0
- Q1-Q4 planning connectivity PASS
- Whole surface: 61,563 chars / 10 sequences / 50 scenes
- Dialogue-format errors 0
- Missing scene openings 0

## CRITICAL FAILURE
The frozen renderer copied internal Scene Contract `state_delta` field/value expressions directly into final screenplay dialogue.

Coordinator audit found 13 internal-state token occurrences, including field names / enum-like state values such as `harbor_open_status`, `ais_relay`, `REVIEW_OPEN`, `procurement_thread`, and relationship-state fields.

The initial automated surface validator did not cover those internal-state token classes and therefore produced a false-negative mechanical PASS. The frozen preregistration rule itself required **zero internal state ID leakage**, so E6-R1 is an immutable scientific FAIL.

Scientific output already existed. Therefore:
- failed surface was NOT edited;
- E6-R1 was NOT rerun or rescored;
- Episode State Commit = 0;
- decision = `SAFE_NO_COMMIT`.

## EXACT SUCCESSOR BOUNDARY
Do not rerun E6-R1.

A new authority must first repair:
1. Semantic State → Surface realization: internal state field/value text may never be copied verbatim into character dialogue or stage direction.
2. Validator coverage: detect snake_case field names, assignment syntax, enum-like ALL_CAPS values, and internal English state prose.

After the repair is sealed, use a **different Fresh Qualification Sample** for the successor formal qualification. Only a successor PASS plus physical/Hub reseal may declare `LEVEL_3_ENTERED`.

## UNCHANGED AUTHORITIES
- Active Engine: `P07-I4H Recovery R3`
- Production: `ENG:R47`
- Formal scored total: `137`
- Latest Formal: `R138`
- Formal R140: `0/0/0`
- DB64 remains non-Production

## MATURITY
`PRE_LEVEL_3__E6_R1_FAILED__SUCCESSOR_REQUIRED`
