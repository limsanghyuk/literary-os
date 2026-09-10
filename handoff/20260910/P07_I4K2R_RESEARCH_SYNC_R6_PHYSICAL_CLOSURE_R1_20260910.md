# P07-I4K-2R Research Sync R6 — Physical Closure R1

Date: 2026-09-10

Physical research-sync authority:
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R6__I4K2R_FAIL_H3_ENSEMBLE_FUTURE_MARGIN`

Full logical 5-Part / 9-transport material SHA256:
`9df7f7f6cc6e3c6790e98e168b6eb82a0c56bb8729280bcf9c2d95309675d216`

Active Development Engine remains `P07-I4H Recovery R3`.
Combined active C2 remains `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7` (318,368,553 bytes).
DB59 remains frozen `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9` (259,756,521 bytes reconstructed from D1+D2).
Production `ENG:R47`; Formal scored count `137`; latest formal `R138`; Formal R140 `0/0/0`.

## Changed transports
Research Sync R6 changes research evidence only:
- CONTROL SHA256 `d99df456a531e1e379f6447b9801b795abc796b6ac410a386bcefb15c0d1e525`;
- Part A SHA256 `31d47b21d31f83bbb50eb83c5029b9bce0046c1771bcb37cad18836eb6b82282`;
- Part B2 SHA256 `1f20fc6478bb179c96fd6d956febae6389477175e2c551db383bfebc82f6f547`.

Byte-identical reuse from Sync R5:
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`;
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`;
- C2-A `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`;
- C2-B `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`;
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`;
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`.

## Physical audit
- CONTROL/A/B2 parent entry metadata mismatch: 0.
- Exactly 13 new R6 evidence entries appended to each changed ZIP.
- duplicate / unsafe / symlink / encrypted: 0.
- ZIP CRC: PASS.
- combined C2 reassembly: PASS.
- DB59 reassembly: PASS.
- post-I4K2R nonhistorical regression: 258/258 PASS.

## Research state
I4K-2R final verdict:
`FAIL__H3_ENSEMBLE_FUTURE_MARGIN_BELOW_PREREG_THRESHOLD__NO_I4K3_ENTRY`.

H1 PASS / H2 PASS / H3 FAIL / H4 PASS. State attachment recovered causal fit, but Attached ensemble+future margin over the best comparator was +0.109375 versus the preregistered +0.15 requirement.

No runtime code, Active Engine, Production, DB, Formal count, or OpenAI Live promotion. Next boundary: diagnose second-order ensemble/future propagation; do not enter I4K-3.