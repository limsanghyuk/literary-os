# P07 I4J R1 Control Scale-Floor HOLD — Physical Research Sync R3 Closure

Date: 2026-09-10

Package authority:
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R3__I4J_R1_CONTROL_SCALE_FLOOR_HOLD`

Full logical 5-Part / 9-transport material SHA256:
`7564dae4e61a15b5bfd57a7bb60745a4d3155c91711dc30ff105f799a95b312a`

Active Development Engine remains `P07-I4H Recovery R3`.
Production remains `ENG:R47`.
DB Authority remains frozen DB59.
Formal scored count remains `137`; latest formal `R138`; Formal R140 `0/0/0`.

## I4J R1 STATE

Experiment: `P07-I4J-R1-FRESH-COVERAGE-ENDPOINT-VALIDATION`.

Final classification:
`HOLD__CONTROL_UNDER_SCALE_FLOOR__NO_SELECTOR__NO_REVISION_POOL__NO_ARMS__NO_SCORES__NO_SCIENTIFIC_H1_H4_VERDICT`.

Fresh plan:
- 10 sequences;
- 50 scenes;
- active Scene→Renderer bridge 50/50 PASS;
- frozen plan manifest SHA256 `34c06bd359b707f98168562d068d5fa06e66b9feab57617654ddb87ad989c92c`.

Single Control attempt:
- 17,928 Unicode chars versus preregistered >=35,000 floor;
- 10 sequences / 50 scenes;
- SHA256 `0a8fbbe0017b1ecb92ae616839441ee4c7050a05a097114162128e5887f5a7ea`.

Selector, Revision Pool, Coverage Arms and Blind Scores remain 0.

## PHYSICAL SYNC R3

Changed transports:
- CONTROL `c3c46b8d68de83a90c158d516a59031fe2d867a6df8522709b01d2e0c3c6e323`;
- Part A `0d0c9e45b11bcf9515362e0af79eedd0952fb7ef442d83bc9e3cb345ca773be0`;
- Part B2 `a31b0a8b6f9ec418c63979810ae52e1a358c2d5652132969179b4c9febc1dd89`.

Reused byte-identically from Research Sync R2:
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`;
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`;
- C2-A `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`;
- C2-B `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`;
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`;
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`.

Combined C2 remains byte-identical:
- bytes `318368553`;
- SHA256 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.

DB59 was reassembled from D1 part001 + D2 part002:
- bytes `259756521`;
- SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

Changed ZIP audit:
- parent entry mismatch 0 for CONTROL/A/B2;
- exactly 7 new Sync R3 evidence entries appended to each;
- duplicate path 0;
- unsafe path 0;
- symlink 0;
- encrypted 0;
- ZIP CRC PASS.

Runtime code changed: false.
DB changed: false.
Active engine changed: false.
Production/formal state changed: false.

## NEXT RESEARCH BOUNDARY

I4J J1 is closed as a pre-selector HOLD and must not be resumed by editing or expanding the Control. Before another I4J causal retry, create a separate preregistration with prospective scale-realization safeguards. The adopted I4K Phase 0 research/design track remains separate and may proceed according to its existing protocol.