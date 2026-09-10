# P07-I4K-1 Research Sync R4 — Physical Closure R1

Date: 2026-09-10

Physical research-sync authority:
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R4__I4K0_EXIT_PASS__I4K1_PASS_TO_I4K2`

Full 5-Part / 9-transport material SHA256:
`90b0cbd6702be6eccea6f203f015ad7ce6e43bbd5dfa8fd5fb6bd0543cee76ab`

Changed transports this sync:
- CONTROL SHA256 `749c5a50600229d4d64c61ce160dd95cb8f48cf14970f27157834e1cb37ad788`
- Part A SHA256 `413e4d3d90ba803f6e72dea55941b303c6f64aa5d5da4b9891769dc6fecf4041`
- Part B2 SHA256 `95bd4585e510770bba68f3d1d22bb5775ae24412b303b145f794e793a5fc70a9`

Byte-identical reuse from Sync R3:
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`
- C2-B `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Physical audit:
- CONTROL/A/B2 parent entry mismatch: 0
- exactly 7 I4K evidence entries appended to each changed ZIP
- duplicate path: 0
- unsafe path: 0
- symlink: 0
- encrypted: 0
- ZIP CRC: PASS
- combined C2 reassembly: 318,368,553 bytes / SHA256 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`
- DB59 reassembly: 259,756,521 bytes / SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- post-I4K1 nonhistorical regression: 258/258 PASS

Research state:
- I4K-0 Exit Gate PASS
- I4K-1 PASS_TO_I4K2
- Active Engine remains P07-I4H Recovery R3
- Production ENG:R47
- DB59 frozen
- Formal scored count 137
- latest formal R138
- Formal R140 0/0/0

Next exact boundary: preregister I4K-2 Search Ablation before any I4K-2 candidate output.
