# SYNC-R26 G6 Mask PASS Physical Closure R1

Date: 2026-09-12
Status: PASS
Physical authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R26__I4K5R4A_ATTEMPT2_G6_MASK_PASS__JUDGES_0__MAPPING_CLOSED`
Parent SYNC-R25 root: `238704e04574386d430d0dfe9b187ca2d6028bc37919bf5e0be463d2b2ed5863`
SYNC-R26 transport-set root SHA256: `c43ad4f04546e4c883ef961a70846d2f4c414abe2eaab86b5ce12f28410e2b1b`

Changed transports: CONTROL / A / B2.
Byte-identical reused transports: B1 / C1 / C2-A / C2-B / D1 / D2.

R4A G6 mask leakage PASS receipt: `b2f68c3aa0a1f7ecda594f2b6034cf9dcabc17cd`.
Masked packet artifact id: `10273575016`.
Mapping-secret artifact id: `10272549788`; mapping remains unopened.
Mask=1; independent judge scores=0; mapping open=0.

Physical package intentionally excludes mapping-secret contents. It includes only the sealed reference/digest so blind evaluation can resume without accidental unblinding.

Next legal action: G7 duplicate-score / judge-provenance preflight, then exactly three independent real-provider judges; seal all three packets before mapping open; then compute H1-H4 and cross-judge independent-confirmation decision.

Unchanged authorities: Active Engine P07-I4H Recovery R3; Production ENG:R47; DB59 frozen; Formal 137; latest Formal R138; R140 0/0/0.
