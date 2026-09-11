# P07 I4K Reinforcement — Research Sync R20 Physical Closure R1

Date: 2026-09-11

## Final physical authority
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R20__I4K_RESEARCH_ARCHITECTURE_PROMOTED__I4K5R2_ATTEMPT2_REINFORCED_PRESCORE`

Parent physical authority:
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R19__I4K_RESEARCH_ARCHITECTURE_PROMOTED__I4K5R1_PREREG_SURFACE_REPAIR`

Parent material SHA256: `e8cef1a6431cc7618a898e5856a01f95fe2c856570f100e962dc31c74cf59575`.

R20 transport-set root SHA256: `89a1f1b0a5052b81fc18861eb348f5693260136cd75f6deb5d6b9342cfc4b34c`.

Root rule: SHA256 over canonical UTF-8 JSON containing parent authority/material, the ordered 9 transport records with exact delivered filename/bytes/outer SHA256, the immutable reassembly seals, and the R20 status token. The canonical root input and delivery manifest are shipped beside the 9 transports, avoiding CONTROL self-hash circularity.

## 5-Part / 9-transport physical set
Read order remains `CONTROL -> A -> B1 -> B2 -> C1 -> C2 -> D1 -> D2`; logical C2 is `C2-A + C2-B`.

Changed transports:
- CONTROL — 110,143,084 bytes — `bc8e383813d32ebca7e2b707eca4ff5cb43ce04b63f586b6bc6308889395259f`
- A — 124,719,155 bytes — `2873718305c21a8fcd1463ffb7a71f67d0f96176a3051b79d2a7efb72fe7f2c6`
- B2 — 256,822,751 bytes — `5e545da4837d8541c93ec1538b2fabebecddf5408e9188d327583fbd9c7b46de`

Byte-identical reuse from R19:
- B1 — 196,427,036 — `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- C1 — 140,020,974 — `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A — 159,184,277 — `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`
- C2-B — 159,184,276 — `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`
- D1 — 138,011,573 — `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 — 173,393,886 — `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

## Package reinforcement performed
1. Full mount/container/runtime-safe inspection was repeated in mandated order.
2. B2 had three historical ZIP filename metadata inconsistencies. The already-correct local UTF-8 filename bytes were preserved, local UTF-8 flags were corrected, and the central-directory filename records were rebuilt. Compressed evidence payloads were not recompressed. Post-repair local/central filename mismatch = 0 and CRC PASS.
3. CONTROL/A/B2 received identical `research_sync_r20/` recovery-state overlays. B1/C1/C2-A/C2-B/D1/D2 are byte-identical.
4. The stale Hub research-progress state was corrected: I4K-5R2 Attempt2 has Control 10/10 and Treatment 10/10, not Treatment 5/10.
5. The prescore Treatment SQ10 paired-world clock mismatch was corrected before any quality score or unblind at commit `d94150c9d4a4911405624f79a37f447ae8e48c73`.

## Reassembly seals
- Combined C2: 318,368,553 bytes / `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7` / 3,774 entries / CRC PASS.
- DB59: 259,756,521 bytes / `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9` PASS.
- B Research Experiment/Learning/Recovery Master: 77,347,512 bytes / `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0` PASS.
- C Narrative Engine Master: 204,167,926 bytes / `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649` PASS.

## Research checkpoint physically propagated
I4K / Narrative Event Ecology / Narrative Showrunner Architecture remains the promoted continuing upper-layer research architecture. Prior I4K-5 H1/H2 PASS and H3/H4 FAIL remain immutable.

I4K-5R1 remains CLOSED prescore under-scale HOLD. I4K-5R2 Attempt1 remains under-scale and unscored.

I4K-5R2 Attempt2 after the prescore clock correction:
- Control: 10/10, 50 scenes, 42,680 metadata-excluded chars.
- Treatment: 10/10, 50 scenes, 39,860 metadata-excluded chars.
- relative gap: 6.6073102155576375%.
- forbidden Treatment internal/meta literals = 0; CH/SQ IDs = 0; exact long duplicate lines = 0.
- deterministic mechanical gates = PASS.
- semantic/continuity final audit seal = PENDING.
- mask = 0 / scores = 0 / unblind = 0.

Correction receipt commit: `9692ea67b92a0ff6bca3547a947ea90a48e958e6`.
Corrected ordered transport manifest R2 commit: `41bc00e7d4c470cd3e0a3644bdbebff485acf9dd`.
Measurement workflow run: `34560018934`.

## Authorities unchanged
Active Development Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Formal scored count 137; latest Formal R138; Formal R140 `0/0/0`; OpenAI Live authority unchanged.

## Infrastructure
Current 9-transport audit completed without mount/container/runtime failure. OOM and oom_kill remained 0. The cgroup `memory.events max` counter is nonzero, so future work must continue to avoid whole-archive extraction, redundant large-file copies, and uncontrolled concurrent decompression.

## Audit
Final Physical Audit: **PASS**.

## Exact next legal research action
Seal the complete prescore semantic/continuity audit against the frozen shared upstream. Only a full admission PASS may authorize masking/scoring/unblind.

## Status token
`SYNC_R20_REINFORCED__I4K5R2_ATTEMPT2_COMPLETE__CLOCK_CONTINUITY_CORRECTED__MECHANICAL_PRESCORE_PASS__SEMANTIC_AUDIT_PENDING__MASK_0__SCORES_0__UNBLIND_0__ACTIVE_I4H_R3__DB59__PRODUCTION_R47__FORMAL_137__R140_0_0_0`
