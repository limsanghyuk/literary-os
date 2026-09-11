# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-12

## CURRENT PHYSICAL AUTHORITY
SYNC-R27 root `dec5f407671015c9bfb29c34d3bbd40b78ec5f2c4e44bd857a5c3eb3aaf4eb0a`.

## EXACT STATE
R4A Attempt2 surfaces frozen; G6 mask PASS; G7 duplicate-score/provenance preflight PASS. Mask=1; judge scores=0; mapping open=0. Mapping-secret artifact id `10272549788` remains unopened. GitHub Actions `OPENAI_API_KEY` secret was absent, therefore no real-provider judge was dispatched.

## MANDATORY RESUME ORDER
1. Read `handoff/20260912/START_HERE_SYNC_R27_G7_PASS_PROVIDER_HOLD_NEW_SESSION_HANDOFF_R1.md`.
2. Verify SYNC-R27 root.
3. Never regenerate surfaces/mask or open mapping early.
4. If a real-provider secret becomes available, run exactly 3 isolated real-provider judges with receipts. Otherwise use exactly 3 fresh external judge conversations; never emulate them in the coordinator.
5. Seal all 3 valid score packets before mapping open.
6. Then open mapping once and compute H1-H4/cross-judge decision.
7. Immediately reseal physical packages after every meaningful result.
8. While provider remains blocked, parallel knowledge-only diagnostics may proceed without modifying R4A thresholds/surfaces.