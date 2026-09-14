# START HERE — SYNC-R42 / E1-R2 EXTERNAL JUDGE PENDING

Date: 2026-09-15

## Physical authority

Current physical candidate authority: **SYNC-R42**

Transport root SHA256:
`921d97529a6d0c9741968b305eba18d7d1a241702a75cc036a5bca9316f2d4ef`

Parent physical authority: **SYNC-R39**
Parent root SHA256:
`e60bd46e5f9e41614aaa3a2a227eb8a6fe4a0175e3684ae5180178ae7cc12009`

Mandatory read order:
`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

R40/R41 local artifacts created during interrupted E1 preparation were not promoted by the Hub and are not parents of R42.

## Stable authority boundaries

- Maturity: `PRE_LEVEL_3__LEVEL_3_ENTRY_QUALIFICATION_IN_PROGRESS`
- Active Engine: `P07-I4H Recovery R3`
- Production Engine: `ENG:R47`
- Formal scored total: `137`
- Latest Formal: `R138`
- Formal R140: `0/0/0`
- DB59 historical benchmark unchanged
- DB64 remains non-Production
- Level 3 has NOT been entered

## E2

Canonical A2R35: PASS `10W/2T/0L`, nonloss `12/12`.
E2 DB64 Fuel / Full-Planning Qualification: `CLOSED_PASS`.

## E1-R1

The first E1 judge packet set was superseded before any external judgment because the screenplay presentation contract was not strict enough and human/candidate source-format asymmetry weakened blindness.

State:
`SUPERSEDED_BEFORE_JUDGMENT__NO_SCORE`

No R1 judge result, mapping open, unblind, PASS or FAIL exists.

## E1-R2

Experiment:
`P07-LEVEL3-E1-R2-FRESH-SURFACE-FORMAT-CLOSURE`

Fresh safe sample:
- 4 works / 12 scenes
- works are fresh relative to R1
- 3 positions per work: EARLY / MIDDLE / LATE
- source-quote-free sanitized semantic contracts only were exposed before candidate seal

Candidate surface format:
- `(씬 설정: ...)`
- `등장인물명: (연기 가능한 행동·표정·시선·호흡·목소리·감정 흐름 지문) 대사`
- `(지문: ...)` allowed/recommended between dialogue turns
- expository dialogue prohibited

Current sealed state:
- candidate units: `12/12`
- mechanical admission: `PASS 12/12`
- candidate bytes: SEALED
- human reference bytes: SEALED after candidate seal
- neutral blind presentation: SEALED
- J01/J02/J03 external judge packets: SEALED
- valid judge responses: `0`
- secret mapping: CLOSED
- mapping SHA256: `8c77653ae9ec47e5dbf0b6ec60cb5c6dde7a3e7b3a1278c2ca4ccc2502ab0b55`

## Exact resume rule

Do NOT regenerate candidates or human references.
Do NOT open the secret mapping.
Do NOT replace a valid unfavorable external judge response.

Next legal actions only:
1. collect exactly the first three valid independent external GPT/Claude responses to J01/J02/J03;
2. seal all three response bytes;
3. validate response schema/independence;
4. only then open the mapping once;
5. apply the frozen E1-R2 gates;
6. immutable-close E1-R2;
7. if PASS, proceed toward E3 Fresh Whole-Episode Integration; if FAIL, diagnose a fresh successor without relabeling R2.

Status token:
`SYNC_R42__E2_CLOSED_PASS__E1_R1_SUPERSEDED_NO_SCORE__E1_R2_CANDIDATE_12_12_MECH_PASS__JUDGE_PACKETS_3__JUDGES_0__MAPPING_CLOSED__NEXT_EXTERNAL_JUDGMENT`
