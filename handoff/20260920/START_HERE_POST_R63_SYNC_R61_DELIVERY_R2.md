# START HERE — POST-R63 SYNC-R61 DELIVERY CORRECTION R2

Date: 2026-09-20
Status: `CANONICAL_HANDOFF__R63_FAIL_PHYSICALLY_ALIGNED__DELIVERY_R2__R64_NEXT_NOT_STARTED`

## Why R2 exists
The first SYNC-R61 physicalization record (R1) was written to Hub before the nine transport files were retained and delivered to the developer. The logical research/authority state was valid, but delivery custody was incomplete.

R2 reconstructs the same post-R63 authority state from verified SYNC-R60 parent bytes and sealed R63 evidence, then retains and exposes all nine transport files.

The old R1 receipt is preserved as history but is superseded for transport custody.

## Current authority
- Logical physical authority: **SYNC-R61**
- Transport revision: **R2**
- Parent physical authority: **SYNC-R60**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Failed research evidence: **R62 F01 + R63 F01**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- R63: **CLOSED FAIL — pre-blind selector-safety gate**
- R64: **NOT STARTED**

## R63 canonical result
Canonical Hub result:
`research/interventions/20260920/R63_F01_PRIMARY_MECHANICAL_SAFETY_RESULT_R1.md`

Primary diagnosis:
`LEXICAL_LICENSE_IS_NOT_SEMANTIC_LICENSE`

A later custody-reinforcement deterministic rerun did not replace or rescore R63; it confirmed the same fail boundary and found an additional PHYSICAL_RISK_FAILURE false license.

Supplement:
`research/interventions/20260920/R63_F01_SEMANTIC_APPLICABILITY_ABSTENTION_RESULT_R1.md`

Diff custody metadata correction:
`research/interventions/20260920/R63_DIFF_CUSTODY_CORRECTION_R1.md`

## SYNC-R61 Delivery R2 transport hashes
- CONTROL: `d771ac2ab3ad5178e6a3ca87fd651f33303712d0fa37242b9c45dbc0077294e3`
- A: `b97e259f84c93ecec14cec55dc59ae1add60e88cdd5d6528731ba1964c6435d0`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2: `35d2d47754ab5e8fc71b2220b49317e58e8fd3b899f66205f66e0b7c75793167`
- C1: `d714700c05a3c5626d1aae20ae871f3ac499d26e2010efd85599e7b0cac6c9b9`
- C2-A: `8a4097e4732fb350f5e837e0edafb8bbbd80ffa4ffb657f55da326fcb1df3e20`
- C2-B: `af3902888225a7886d9554389219db16b60b1bd92834c0f7a42aae98f67c9d50`
- D1: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

C2 logical:
- bytes: `376056706`
- SHA256: `067a85718bccd95aba48f7384ea995fbde41c0695204f266e679e30fa9d4c200`

Trust root SHA256:
`1e592e73665beeaf59aee33cd7c5d72075854d863308ae0262d5237b453edce1`

## Active runtime
Exact SYNC-R58 remains active:
- runtime: `30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`
- overlay: `d4215a8a5075054a054d5ca60e10e5992c4139588cccaeb0dabe14281f2fd633`
- source: `42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R63 failed source retained as non-active evidence:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

## Audit
- 9/9 transport SHA PASS
- ZIP CRC PASS
- duplicate entries 0
- encrypted entries 0
- unsafe paths 0
- C2 reassembly PASS
- active runtime exact SYNC-R58 PASS
- R63 failed source present in C1/C2 PASS
- secret-pattern audit PASS
- B2 byte-identical to SYNC-R60; margin below 256 MiB limit: 148,859 bytes
- OOM 0 / OOM kill 0

## Next
`R64 = F01 Typed Semantic-Role License Gate`

R64 is NOT STARTED.

A fresh session must verify this R2 trust root and transport hashes first. It must not use the superseded R1 transport hashes for custody.
