# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
SYNC-R26 root `c43ad4f04546e4c883ef961a70846d2f4c414abe2eaab86b5ce12f28410e2b1b`.

## EXACT STATE
R4A Attempt2 surfaces frozen; G6 mask PASS; mask=1; independent judge scores=0; mapping open=0. Masked packet artifact id `10273575016`. Mapping-secret artifact id `10272549788` remains unopened.

## MANDATORY RESUME ORDER
1. Read `handoff/20260912/START_HERE_SYNC_R26_G6_PASS_NEW_SESSION_HANDOFF_R1.md`.
2. Verify SYNC-R26 root.
3. Never regenerate surfaces or G6 mask and never open mapping early.
4. Run G7 duplicate-score/provenance preflight.
5. Run exactly 3 independent real-provider judges; seal all three score packets.
6. Then open mapping once and compute H1-H4/cross-judge decision.
7. After each meaningful result change, immediately reseal 5-Part/9-transport physical packages before continuing if interruption risk remains.
