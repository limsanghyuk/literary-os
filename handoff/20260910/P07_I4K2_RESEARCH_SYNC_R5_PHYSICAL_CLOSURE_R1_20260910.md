# P07 I4K-2 Research Sync R5 — Physical Closure R1

Date: 2026-09-10

## Current physical research-sync authority
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R5__I4K2_FAIL_H2_EXTERNAL_ONLY_CAUSAL_FIT_DEGRADATION`

Full logical 5-Part / 9-transport material SHA256:
`b8c4d28370e6166851cd996bf89a37892268524824b00c511a3338f85031c87b`

Active engine remains `P07-I4H Recovery R3`.
Combined active C2 remains `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.
DB59 remains frozen `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
Production `ENG:R47`; Formal scored count `137`; latest formal `R138`; Formal R140 `0/0/0`.

## Changed transports in Sync R5
- CONTROL SHA256 `bbdb4e98a2b64f0e056e86b0a6d0f78345b211bbbe163de88127a25d6dd89499`
- Part A SHA256 `144343d385a7fe0ab333d92c86768a692b29d2cecd5ffa2ff5fbb41523acd456`
- Part B2 SHA256 `e9a0e9e6fb1de7965a6c81c93c8a718b1f3d0f8bfc532b44c34e8937f32806cc`

Byte-identical reuse from Research Sync R4:
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`
- C2-B `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

## Physical audit
For CONTROL/A/B2:
- parent entry mismatch: 0
- appended Sync R5 evidence entries: 11 each
- duplicate paths: 0
- unsafe paths: 0
- symlinks: 0
- encrypted entries: 0
- ZIP CRC: PASS

Combined C2 reassembly:
- bytes: 318,368,553
- SHA256: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`
- PASS

DB59 reassembly from D1 part001 + D2 part002:
- bytes: 259,756,521
- SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- PASS

Full manifest SHA256: `14411ed0cd45b134f160f19d002f80e60b1674de87464a3a9901631ee6c6528a`.
Final physical audit SHA256: `bef063c1c493c6f6a54a68220e925df9a620ec2d0ee9d19a28782958a6ab5fce`.

## Scientific state added in R5
I4K-2 `P07-I4K-R2-EXTERNAL-SEARCH-ABLATION` closed as:
`FAIL__H2_EXTERNAL_ONLY_CAUSAL_FIT_DEGRADATION__NO_ADVANCE_TO_I4K3`.

H1 PASS / H2 FAIL / H3 PASS / H4 PASS.
Post-I4K-2 nonhistorical regression: `258/258 PASS`.

## Next boundary
I4K-3 is not authorized from this result. Next research must diagnose and prospectively repair the external-mechanism-to-current-state attachment/routing deficit, then run a fresh preregistered replication before any I4K-3 Event-to-Sequence Causal Adoption study.