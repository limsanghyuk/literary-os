# P07-I4I Blind Map Hash Freeze R3

Date: 2026-09-09
Experiment: `P07-I4I-WHOLE-EPISODE-PAIRED-RERENDER-R1`

Control and Treatment are sealed before this map.

Control SHA256: `a48c53df49cd230b381a86795332905b0bf72d73f1374f253d46d58609ca551a`.
Treatment SHA256: `fda8a3e45f4b343245b0c988d77978ec4baec7af59f3d07e3f555cbbd9321ca8`.

Two earlier mask attempts were discarded before any scoring because the first printed A/B content hashes, which made the mapping inferable, and the second reused an unsalted two-state map hash that remained inferable from the first incident. They carry zero scores and no scientific result.

The valid R3 map includes a fresh hidden random nonce, so the committed hash does not reveal which of A/B is Control or Treatment.

Valid secret A/B map R3 SHA256:
`7108578ae345390698750729fccf22c66e21056ebe602e1903ec7f7b5a438e82`.

At this checkpoint:
- blind scores: `0`;
- mapping: not opened;
- evaluator may read only `EPISODE_A_BLIND_R3` and `EPISODE_B_BLIND_R3` / sequence splits;
- map file must not be opened until score seal.

Status: `VALID_BLIND_MAP_R3_HASH_SEALED__SCORES_0__MAPPING_HIDDEN`
