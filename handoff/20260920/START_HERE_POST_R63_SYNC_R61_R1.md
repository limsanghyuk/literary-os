# START HERE — POST-R63 PHYSICAL AUTHORITY SYNC-R61 R1

Date: 2026-09-20
Status: `CANONICAL_HANDOFF__R63_FAIL_PHYSICALLY_ALIGNED__R64_NEXT_NOT_STARTED`

## Important naming note
SYNC-R61 is a physical synchronization ID. It is distinct from the already-closed research experiment R61.

## Current authority
- Latest complete physical authority: **SYNC-R61**
- Parent physical authority: **SYNC-R60**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Quarantined failed research: **R62 F01 and R63 F01**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- R63: **CLOSED FAIL — preregistered pre-blind selector-safety gate**
- R64: **NOT STARTED**

## Why SYNC-R61 exists
R63 ran after SYNC-R60. It failed before external blind evaluation because the semantic-license gate produced lexical false positives. The physical package set therefore required a research-overlay alignment before R64.

SYNC-R61 adds the R63 preregistration/source-freeze/fresh-case/mechanical-safety evidence while keeping the executable current runtime exactly equal to qualified SYNC-R58.

## R63 result
Frozen Treatment source SHA256:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

Fresh primary cases SHA256:
`5c7f04816c00a2f5afc42a8c2862f5e888000a2fbefde28f9c73f03c1cdb3376`

Control output:
`0c75ca2f20ac14c5770dab819d4ae77490d8cdaebdf5a58569bcd39af1424764`

Treatment output:
`73a1a57e752050f41201265910f97893d5f272f48321070172440a9b2185f4d6`

Result:
`R63 = CLOSED_FAIL__PREBLIND_SELECTOR_SAFETY_GATE`

Failure diagnosis:
- physical hose pressure was falsely licensed as dramatic PRESSURE_ESCALATION;
- the substring 막 inside 막차 was falsely treated as evidence for COUNTERMOVE;
- `LEXICAL_LICENSE_IS_NOT_SEMANTIC_LICENSE`;
- `CORRELATED_LEXICAL_GATE_CANNOT_SAFELY_VALIDATE_LEXICAL_PROPOSAL`.

External blind:
`NOT RUN`
because the frozen pre-blind safety gate already failed.

## SYNC-R61 transport hashes
- CONTROL: `e08ccb02fd219e50686d6b6e97661019c284b4c98e68d783cdbabf8178cd668b`
- A: `e50f6a6c690c23068d31fd451a60c92d9ed02cd63c047e53a7ec06ba1896ab49`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2: `35d2d47754ab5e8fc71b2220b49317e58e8fd3b899f66205f66e0b7c75793167`
- C1: `6026ed58aa778882fe219161c2e46bbbb528ad18d520b36ab90e289ff483b155`
- C2-A: `5694f368d66695b841d65a38aff33c71f68b87920288f5dbfb67014ee3743e2d`
- C2-B: `7ce8f8bfae86c62e88027d887098ce18b9ca2d20ca5479518479fd322b6f4c7a`
- D1: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

C2 logical:
- bytes: 376023026
- SHA256: `b9b2869c4ae4e1a17282564a49760c27516f6812bf0a18e3c374a0ea21c53e34`

Trust root SHA256:
`18eaa49ecc2aa514f053466b9718a1e6bda92ea3b6055b28a712cdd71ee3b839`

## Active runtime remains exact SYNC-R58
- integrated runtime: `30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`
- overlay: `d4215a8a5075054a054d5ca60e10e5992c4139588cccaeb0dabe14281f2fd633`
- adaptive source: `42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

Runtime DB:
`DB59 = a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## Audit
- 9/9 transport SHA PASS
- ZIP CRC PASS
- duplicate/encrypted/unsafe ZIP entries: 0
- C2 streaming reassembly PASS
- C1 current runtime = exact SYNC-R58 PASS
- R63 failed source evidence present PASS
- secret-pattern audit PASS
- B2 byte-unchanged from SYNC-R60; 148859 bytes below 256 MiB

## Next research
`R64 = F01 Typed Semantic-Role License Gate`

R64 has not started. It must replace correlated raw lexical licensing with typed semantic-role evidence while preserving exact R58 fail-closed fallback.
