# P07-I4D Cumulative Research Evidence Sync — Physical Closure R1

Date: 2026-09-08
Classification: PHYSICAL RESEARCH EVIDENCE SYNC / NO NEW EXPERIMENT / NO ACTIVE ENGINE CHANGE

## 1. Purpose
Repair the physical-research-history gap identified in the session audit. The active engine remains the already sealed P07-I4D authority, while non-promoted P07-I4C R1/R2 and P07-I4E R1/R2 research evidence is physically synchronized into the canonical 5 logical Parts / 9 physical Packages without changing active runtime policy.

## 2. Active engine authority — unchanged
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`

Active C2 SHA256 remains byte-identical:
`1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`

Formal scored count remains 137. Latest formal scored authority remains R138. R140 remains 0 attempts / 0 outputs / 0 scores — HARD BLOCK. DB59 remains frozen at `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## 3. New cumulative physical research authority
`CURRENT_PHYSICAL_RESEARCH_AUTHORITY__P07_I4D_ACTIVE__I4C_I4E_EVIDENCE_SYNC_R1`

This authority distinguishes:
- ACTIVE POLICY: I4A Provider resilience/fail-close + I4B `LiterarySurfaceContractR1` + I4D optional `SurfaceRealizationModeR1`;
- RESEARCH EVIDENCE ONLY: I4C R1/R2 and I4E R1/R2 HOLD outputs, audits, mappings/judgments, repair/state-block receipts, and research scripts/tests.

No I4C/I4E recovery code is inserted into the active C2 materialization order.

## 4. Research sequence preserved
1. P07-I3 inherited broadcast closed-loop authority.
2. P07-I4A: Provider operating layer PASS; six-scene surface repair HOLD. Provider engineering only promoted.
3. P07-I4B: `LiterarySurfaceContractR1` PASS and promoted.
4. P07-I4C R1: whole-episode contract completeness failure; HOLD.
5. P07-I4C R2: speaker-complete recovery; Stage A 12/12 PASS; Human 9 / Candidate 3 / Tie 0 Stage B non-loss gate FAIL; HOLD, State Commit blocked.
6. P07-I4D: targeted `SurfaceRealizationModeR1` PASS; Stage A 9/9; Human 4 / Candidate 3 / Tie 2; promoted.
7. P07-I4E R1: whole-episode mode assignment exposed speaker-authorization and assembler defects; HOLD.
8. P07-I4E R2: strict speaker authorization + exact-scene surgery restored mechanical integrity, but Stage A Treatment 6 / Control 6 / Tie 0 failed the preregistered >=9/12 gate; HOLD, no Stage B, no State Commit.

## 5. Evidence synchronization policy
Raw frozen DB59 human-source files are not duplicated. Full blind packet text is also not duplicated in the sync overlay; hashes, mapping, judgments, selection seals, result ledgers, and source-authority references are preserved. This avoids redundant source duplication while retaining reproducibility and provenance.

## 6. Current 5 Parts / 9 Packages
1. CONTROL `LITERARY_OS_CURRENT_CONTROL_P07_I4D_RESEARCH_SYNC_R1.zip`
   SHA256 `aab03be82acf66de53d49a1101e602dfcd1ecc1841f25177aea4a2e3cb3dd769`
2. A `LITERARY_OS_CURRENT_PART_A_P07_I4D_RESEARCH_SYNC_R1.zip`
   SHA256 `61e321b8c47d4a4181ce3140adbaa084929ae222b733ac97da886c3e83618c14`
3. B1 `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1.zip`
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. B2 `LITERARY_OS_CURRENT_PART_B2_P07_I4D_RESEARCH_SYNC_R1.zip`
   SHA256 `c2a4e3a6fefe2eeaed8d3c9579780b1b9e3699a5c41549d6cfac506c3711ec06`
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

Changed from the I4D package wrapper: CONTROL / A / B2 only.
Byte-identical to I4D: B1 / C1 / C2-A / C2-B / D1 / D2.

## 7. Trust roots
Package Set SHA256:
`49d999d45b94ddcb7059a01e1edf1a92304ce26f282cb867c47a8ab04a7d6d5f`

Manifest SHA256:
`995df5c1c2b15758659344013dfe2605f59bb410a88db30ebd9b2e3c16913eac`

Trust Root file SHA256:
`2274176a8dd6cf201c938ff7108deb015b1b8153e8bad9730d25ee14fdad85f1`

Trust Root material SHA256:
`4867359973e4da052a21105381b1380e7df8bd09065044cbc6657b4e0506214f`

## 8. Physical audit
PASS:
- changed CONTROL/A/B2 preserve all parent I4D entries with 0 missing and 0 CRC/size/compression/nested-ZIP mismatch;
- B1/C1/C2-A/C2-B/D1/D2 are byte-identical to I4D;
- ZIP CRC PASS / duplicate path 0 / unsafe path 0;
- active C2 A||B rejoin remains exact I4D C2 SHA `1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`;
- new evidence secret scan 0 hits;
- post-sidecar nine-package SHA audit PASS.

## 9. Claim boundary
This sync is archival/governance work, not a new scientific experiment and not a new active-engine version. I4C/I4E evidence remains non-promoted. No whole-episode human competitiveness, real OpenAI Live parity, external human consensus, human-writer equivalence, RFV3, CP1 Live, R-F/R-G, Production promotion, or Formal R140 closure is established.

## 10. Next scientific order
Start only from the exact P07-I4D active engine. The next separately preregistered scientific unit is a Mode Selector precision / abstention / operator-intensity probe comparing `NONE` versus eligible mode application while explicitly protecting already-strong scenes. Do not begin that experiment until this sync is reflected in the Current Session Recovery Pointer, Developer Hub, and new-session START_HERE handoff.

## STATUS TOKEN
`CURRENT_PHYSICAL_RESEARCH_AUTHORITY_P07_I4D_SYNC_R1__ACTIVE_ENGINE_I4D_BYTE_UNCHANGED__I4C_I4E_HOLD_EVIDENCE_PHYSICALLY_SYNCED__NO_NEW_EXPERIMENT__P07_ACTIVE_PREFORMAL__R140_HARD_BLOCK`
