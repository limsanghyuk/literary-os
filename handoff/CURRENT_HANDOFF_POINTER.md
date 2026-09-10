# CURRENT HANDOFF POINTER
Last updated: 2026-09-10

## READ FIRST
1. `handoff/20260910/P07_I4K2P_R4_RESEARCH_SYNC_R10_PHYSICAL_CLOSURE_R1_20260910.md`
2. `handoff/20260910/P07_I4K2P_R4_ARM_PARITY_HOLD_CLOSURE_R1_20260910.md`
3. `handoff/20260910/P07_I4K2P_R3_RESEARCH_SYNC_R9_PHYSICAL_CLOSURE_R1_20260910.md`
4. `handoff/20260910/P07_I4K2P_R2_RESEARCH_SYNC_R8_PHYSICAL_CLOSURE_R1_20260910.md`
5. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
6. `handoff/CURRENT_NEXT_RESEARCH_POINTER.md`
7. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`

## CURRENT PHYSICAL / ENGINE / DB AUTHORITY
Physical research-sync authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R10__I4K2P_R4_HOLD_ARM_FIELD_MEAN_PARITY`.
Full 5-Part / 9-transport material SHA256: `06717b220bf6c17d9abe5ce39a847dd7154d53e3c4e0de945eb197a0daf7301a`.
Active Engine remains `P07-I4H Recovery R3`; combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Production `ENG:R47`; Formal `137`; latest `R138`; R140 `0/0/0`.

## LATEST RESEARCH
I4K-2P R4: `HOLD__ARM_LEVEL_FIELD_MEAN_PARITY_FAIL__NO_FINAL_ARMS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`.
Primary prereg commit `3dbe53c88aa4030ca20bcca5481e7477d835bbdd`; a later duplicate prereg commit `647dfe8c369fa6eaf208458c8864fd820d3c3fc2` is non-authoritative.
12/12 matched pairs passed individual broad budgets and pair-total parity; arm total gap 0.030499 <=0.05. The only failed final-arm parity gate was `second_order_consequence` field-mean gap 0.156627 >0.10. Final arms/mask/scores/unblind remain 0.

## PHYSICAL SYNC R10
Changed CONTROL/A/B2 only; parent-entry mismatch 0; 21 evidence entries appended; CRC/path safety PASS. Other six transports byte-identical from R9; C2 and DB59 remain unchanged.

## EXACT NEXT BOUNDARY
Fresh target-field-aware parity retry only. Keep same broad per-candidate budgets and total verbosity parity. Apply cross-arm field-mean <=10% only to non-target representation fields; `second_order_consequence` and `future_carry` remain individually bounded by the same budgets but are exempt from cross-arm mean equality because they carry the propagation treatment. H1-H4 remain unchanged. I4K-3 remains unauthorized.

## STATUS TOKEN
`CURRENT_HANDOFF__SYNC_R10_06717B22__ACTIVE_I4H_R3__I4K2P_R4_HOLD_TARGET_FIELD_PARITY__R5_TARGET_AWARE_PARITY_NEXT__NO_I4K3__DB59__FORMAL_137__R140_0_0_0`