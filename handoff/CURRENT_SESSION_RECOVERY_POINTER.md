# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-10

## CURRENT DURABLE STATE
Physical research-sync authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R10__I4K2P_R4_HOLD_ARM_FIELD_MEAN_PARITY`.
Material SHA256: `06717b220bf6c17d9abe5ce39a847dd7154d53e3c4e0de945eb197a0daf7301a`.
Active engine `P07-I4H Recovery R3`; combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Production `ENG:R47`; Formal `137`; latest `R138`; R140 `0/0/0`.

## LATEST CLOSED RESEARCH
I4K-2P R4 primary prereg commit `3dbe53c88aa4030ca20bcca5481e7477d835bbdd`. 12/12 pairs passed candidate broad budgets and pair-total parity. Arm total gap passed. Final-arm parity failed because `second_order_consequence` mean gap 0.156627 exceeded the frozen 0.10 all-field rule. Verdict: `HOLD__ARM_LEVEL_FIELD_MEAN_PARITY_FAIL__NO_FINAL_ARMS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`.

## RESUME ORDER
1. Runtime/filesystem/cgroup/OOM preflight.
2. Verify Sync R10 identity.
3. Do not modify/score R1-R4 HOLD material.
4. Fresh R5 only: target-field-aware parity.
5. Keep identical broad field budgets and pair/arm total parity; keep State Attachment both arms and Propagation Contract Treatment only.
6. Apply field-mean <=10% only to non-target fields; target second_order_consequence/future_carry remain individually bounded but may differ in mean.
7. Seal prereg before output; provisional drafts non-output, max three attempts, hash receipts.
8. Only after full prescore PASS may masking/scoring begin.
9. Only H1-H4 full PASS may authorize I4K-3.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R10_06717B22__I4K2P_R4_HOLD__R5_TARGET_AWARE_PARITY_NEXT__NO_I4K3__ACTIVE_I4H_R3__DB59__FORMAL_137__R140_0_0_0`