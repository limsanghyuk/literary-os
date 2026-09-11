# P07 I4K-5R4 Preregistration — Sync R23 Physical Closure R1
Date: 2026-09-11

## Current Physical Research Authority
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R23__I4K5R4_INDEPENDENT_CONFIRMATION_PREREG__OUTPUTS_0`

Parent Sync R22 transport root: `b23866b816991da70a0262ab430fc5736fd394e838b4508010ed09ad806ba4aa`.
Sync R23 transport-set root: `8c2c283ac7f378b30c23a255d5d9835afc1b056df8865710a09999ffb296e901`.
R4 preregistration commit: `aa38377c806a1be8041b64394c60f87cd0e333a7`.

## Physical Layout
Read order: `CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`.
Changed append-only transports: CONTROL / A / B2.
Byte-identical transports: B1 / C1 / C2-A / C2-B / D1 / D2.

## Definitive Outer Seals
- CONTROL — 110,159,627 bytes — `49e738e87a17e87a83866c6efab9d0d07e0c28ddffd16a5430de51b6b860562d`
- A — 124,735,698 bytes — `337659a75cc662404097550bb72f63ff79dee9176452b10752a9ea6275c00ed0`
- B1 — 196,427,036 bytes — `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 — 256,839,294 bytes — `f7c12630dcedba48cbdda9a8a107c0175985d567211bd983499b01c7060eb34e`
- C1 — 140,020,974 bytes — `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A — 159,184,277 bytes — `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`
- C2-B — 159,184,276 bytes — `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`
- D1 — 138,011,573 bytes — `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 — 173,393,886 bytes — `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

## Physical Audit
R22 parent-entry metadata mismatch in CONTROL/A/B2 = 0 across CRC, compressed size, file size, header offset, compression type and flag bits.
Exactly 5 `research_sync_r23/` entries were added to each changed ZIP; names, bytes and SHA256 values are identical across CONTROL/A/B2.
duplicate / unsafe path / symlink / encrypted entry = 0.
Changed ZIP full CRC/testzip = PASS 3/3.
B2 `unzip -tqq`: exit 0; filename mismatch warning 0; CRC/data errors 0.
Six unchanged transport SHA values exactly match Sync R22.
B Research Experiment/Learning/Recovery Master reassembly = 77,347,512 bytes / `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0` PASS.
Combined C2 / C Narrative Engine Master / DB59 are carried byte-identically from fully audited R22: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`, `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`, `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## R4 State Physically Propagated
Experiment: `P07-I4K-5R4-PSSB-INDEPENDENT-MASKED-FRESH-CONFIRMATION`.
R4 is prospectively preregistered before outputs. It freezes the R3 PSSB intervention and unchanged H1-H4 thresholds, requires completely fresh unseen material, separated generation/evaluation, three independent masked judges, and mapping sealed until all three judge packets are sealed.
R4 output counts at this physical seal: Series/Episode 0; Event Ecology 0; Sequence Plan 0; Scene Plan 0; Control 0; Treatment 0; Mask 0; independent judge scores 0; mapping open 0; human validation 0.

## Immutable Parent Evidence
R3 canonical internal PASS remains immutable: canonical score seal `90a0d7985025fa0ebf221ae32aaa942b82271b50`; final result `c241d0d7d030d143f2cd2e145308f9858953d566`; Treatment 9W/2T/1L; H1/H2/H3/H4 all PASS. Recovery duplicate score remains quarantined and non-authoritative.

## Authority Boundary
No Active Engine / Production / DB / Formal / R140 promotion occurred. Active Engine remains `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Formal 137; latest Formal R138; R140 `0/0/0`.

## Next Legal Action
Seal a completely fresh R4 Series/Episode state only. Then fresh Event Ecology -> shared 10-sequence plan -> shared 50-scene plan -> byte-identical Shared Upstream Architecture. No Control/Treatment render before upstream sealing and no authoritative quality score by the generation agent.
