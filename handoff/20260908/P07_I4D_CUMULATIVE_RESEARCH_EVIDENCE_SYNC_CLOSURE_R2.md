# P07-I4D Cumulative Research Evidence Sync Closure R2

Date: 2026-09-08
Classification: PHYSICAL RESEARCH EVIDENCE SYNC / NO NEW EXPERIMENT / NO ACTIVE ENGINE CHANGE

## Active engine authority — unchanged
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`

Active C2 SHA256:
`1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`

## Current cumulative physical research authority
`CURRENT_PHYSICAL_RESEARCH_AUTHORITY__P07_I4D_ACTIVE__I4C_I4E_I4F_EVIDENCE_SYNC_R2`

Parent cumulative research authority:
`CURRENT_PHYSICAL_RESEARCH_AUTHORITY__P07_I4D_ACTIVE__I4C_I4E_EVIDENCE_SYNC_R1`

This reseal adds P07-I4F only as `RESEARCH_EVIDENCE_ONLY__NOT_ACTIVE_POLICY`. No selector/intensity prototype is inserted into active C2.

## Newly synchronized P07-I4F result
Preregistration commit:
`09f556b9e979623460ee5f5419eb1d51166d4d3a`

HOLD result commit:
`871d71a32fff3106c7b7c1e1911d8cea1a12ecf4`

Final I4F verdict:
`HOLD__SELECTOR_OVERAPPLIES_MODE__ABSTENTION_PRECISION_INSUFFICIENT__NO_PROMOTION`

Key facts:
- pre-output selector validation 15/15 PASS;
- protected S07/S11/S14 abstention NONE 3/3 PASS;
- focused tests 6/6 PASS;
- 36 tri-arm variants mechanical gate PASS;
- judgments sealed before mapping reveal;
- selector best/co-best 5/12 vs preregistered >=8/12 FAIL;
- selector strict-worst 5/12 vs <=1/12 FAIL;
- selected MODE vs NONE non-loss 1/8 and wins 1/8 FAIL;
- selected NONE decisions 4/4 correct PASS;
- selected intensity vs opposite intensity non-loss 3/8 FAIL;
- NONE was blind-best on 10/12 prospective scenes;
- State Commit BLOCKED; no active policy change; no promotion regression.

## Current cumulative 5 Parts / 9 Packages
1. CONTROL `LITERARY_OS_CURRENT_CONTROL_P07_I4D_RESEARCH_SYNC_R2.zip`
   SHA256 `0ac5f6cfcf22ae640c5206379d2a347796ab124d8649446409c6d34f0da7937f`
2. A `LITERARY_OS_CURRENT_PART_A_P07_I4D_RESEARCH_SYNC_R2.zip`
   SHA256 `3be746af414186bb7d707e89b32b31dc9a1e52637ac3ae9e390a2d8dc7eac20e`
3. B1 `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1.zip`
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. B2 `LITERARY_OS_CURRENT_PART_B2_P07_I4D_RESEARCH_SYNC_R2.zip`
   SHA256 `afa89a6b5baa4081fdbb96ca2bb80a796e7381f05f44e930e2c107752e120a90`
5. C1 `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1.zip`
   SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. C2-A `LITERARY_OS_CURRENT_C2_BINARY_A_P07_I4D_SURFACE_MODES_R1.bin`
   SHA256 `d7c8b42d0cbe2ccaddf0c49991eff4a02b0b5a5b931f90b0d477857835d88e62`
7. C2-B `LITERARY_OS_CURRENT_C2_BINARY_B_P07_I4D_SURFACE_MODES_R1.bin`
   SHA256 `52c0f58b4ce007ad61fefee2036ac29d25cd6901ef92f94c00930d77b98531b4`
8. D1 `LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1.zip`
   SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. D2 `LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1.zip`
   SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Changed from Sync R1: CONTROL / A / B2.
Byte-identical to Sync R1: B1 / C1 / C2-A / C2-B / D1 / D2.

## Trust roots
Package Set SHA256:
`84410ea6c7eda4a09b0b004d20c4d083f4da2b49728dac2f2c51bfa1dae91164`

Manifest SHA256:
`bd8a0824ff9694deef3ddb4f02ab4ab25b6dc85e8f3378f8fdc4c30f5088f883`

Trust Root file SHA256:
`872cc3179fa6a4abab29d7d2409aae3fcf1c4f35ad3beeccd72de3527aa7e3f4`

Trust Root material SHA256:
`e5518ef565896ea5edf55cc1573958c8df3efb7a3d7e1c9f09da0f0b2581b529`

## Physical audit
PASS:
- CONTROL/A/B2 preserve every Sync R1 parent ZIP entry with 0 missing and 0 metadata/nested-ZIP mismatch;
- all new entries are confined to `P07_CUMULATIVE_RESEARCH_EVIDENCE_SYNC_R2/`;
- B1/C1/C2-A/C2-B/D1/D2 whole-file byte-identical;
- ZIP CRC PASS / duplicate paths 0 / unsafe paths 0;
- new evidence secret hits 0;
- C2-A||C2-B exact rejoin remains active I4D SHA;
- post-sidecar package SHA audit PASS.

Frozen DB59 SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

Formal scored count remains 137. R140 remains 0/0/0 HARD BLOCK.

## Research diagnosis / next order
I4F shows strong evidence for conservative abstention: frozen NONE choices were correct 4/4 and NONE was blind-best 10/12. The current selector fails because it intervenes too often and does not separately model output-realization reliability.

Do NOT start a whole-episode rerender next. Next separately preregistered unit should use a two-stage decision boundary:
1. `INTERVENE?` vs `ABSTAIN`, with a strong abstention prior and protected-scene invariance;
2. only after intervention eligibility, choose LOW vs STANDARD, with an output-reliability/reject gate before adoption.

The next unit is not started by this sync.

## Claim boundary
Active engine remains P07-I4D. I4F is non-promoted research evidence. No whole-episode human competitiveness, external human consensus, human-writer equivalence, real OpenAI Live parity, RFV3, CP1 Live, official R-F/R-G, Production promotion, or Formal R140 closure is established.

## STATUS TOKEN
`CURRENT_ACTIVE_ENGINE_P07_I4D__CURRENT_RESEARCH_AUTHORITY_I4D_SYNC_R2__I4C_I4E_I4F_EVIDENCE_SYNCED__I4F_SELECTOR_HOLD__NEXT_TWO_STAGE_ABSTENTION_RELIABILITY_NOT_STARTED__FORMAL_137__R140_HARD_BLOCK`
