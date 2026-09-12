# START HERE — SYNC-R33 PHYSICAL AUTHORITY / I4C MIXED-WEAK
Date: 2026-09-12

## READ ORDER
Read the 9 physical transports in this order:
`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`.

## CURRENT PHYSICAL AUTHORITY
**SYNC-R33** is now the latest fully materialized and twice-audited physical authority.
Transport-set root SHA256:
`39487b9dc0ff12e2c75c16a1d5d8d7192dfb53e1ef14dc71d03c4474f1541d87`

Parent physical authority was SYNC-R32 root:
`b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb`

Delivery manifest:
`handoff/20260912/SYNC_R33_DELIVERY_MANIFEST_R1_20260912.json`

Physicalization completion receipt:
`handoff/20260912/SYNC_R33_PHYSICALIZATION_COMPLETION_RECEIPT_R1_20260912.json`

## PHYSICALIZATION METHOD AND AUDIT
The exact 9 SYNC-R32 parent transports were verified first. Runtime/container minimal commands passed. R33 was then built by copying the exact R32 parent bytes and appending only the sealed `research_sync_r33/` overlay to CONTROL/A/B2. B1/C1/C2-A/C2-B/D1/D2 remain byte-identical to R32.

Changed transports contain exactly 9 R33 overlay entries each. Overlay bytes are identical across CONTROL/A/B2. Changed ZIP CRC, duplicate-name, unsafe-path, symlink, encryption, parent-entry metadata/CRC/size preservation, unchanged-six SHA identity and combined-C2 checks all passed. A second independent fresh-process audit also passed with zero errors.

## I4C RESULT NOW PHYSICALLY INCLUDED
The post-R32 I4C unused-scene independent annotation replication is now physically propagated into SYNC-R33.

- J01/J02/J03 exact frozen response bytes verified.
- 3-of-3 gate: `PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED`.
- Mapping exact replay SHA: `46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`.
- Mapping replay: `PASS__EXACT_MAPPING_BYTE_SEAL_REPRODUCED`.
- Final decision: `MIXED_OR_WEAK_REPLICATION`.
- MIDDLE+LATE minus EARLY breadth: `+0.875`.
- MIDDLE+LATE minus EARLY severity: `+0.875`.
- Independent evaluator direction: `3/3` middle/late worse.
- Frozen strong-positive thresholds were not changed and were not met for breadth/severity.

This remains knowledge-only. It does not authorize a generic renderer patch, historical-score rewrite, Production/Engine/Formal promotion, human-consensus claim or population generalization.

## R4A TRACK
R4A remains unchanged and separate: G6 PASS; G7 PASS; provider=`HOLD__REAL_PROVIDER_SECRET_ABSENT`; independent Judges=0; Mapping open=0; exact surfaces frozen. No R4A H1-H4 verdict exists.

## UNCHANGED AUTHORITIES
Active Engine: `P07-I4H Recovery R3`
Production: `ENG:R47`
Combined C2 SHA256: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`
DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Formal scored total: `137`
Latest Formal: `R138`
Formal R140: `0/0/0`

## NEXT LEGAL RESEARCH STEP
The physicalization prerequisite is now closed. A new experiment may be designed only through a fresh preregistration. Do not infer a broad whole-renderer defect from the mixed/weak I4C result. The next candidate must isolate a narrower, specifically reproducible craft mechanism on fresh/unseen material and retain frozen-input, contract-consumption, relative-effect, absolute-surface and independent-evaluation separation.

No next experiment is declared completed or active by this handoff.

## FAILURE/RECOVERY RULE
If a future container fails, do not fabricate or partially rewrite physical authority. Recover from the exact SYNC-R33 9-transport hashes and root above, verify minimal runtime first, and preserve the unchanged Engine/Production/DB/Formal boundaries.

## STATUS TOKEN
`PHYSICAL_SYNC_R33__I4C_MIXED_OR_WEAK_PHYSICALLY_PROPAGATED__R4A_JUDGES_0_MAPPING_CLOSED__NEXT_CRAFT_MECHANISM_NOT_YET_PREREGISTERED`
