# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-10

## CURRENT PHYSICAL RESEARCH AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R10__I4K2P_R4_HOLD_ARM_FIELD_MEAN_PARITY`
Full 5-Part / 9-transport material SHA256: `06717b220bf6c17d9abe5ce39a847dd7154d53e3c4e0de945eb197a0daf7301a`.
Active Development Engine remains `P07-I4H Recovery R3`.
Combined active C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Production `ENG:R47`; Formal `137`; latest `R138`; R140 `0/0/0`.

## LATEST RESEARCH
I4K-2P R4: `HOLD__ARM_LEVEL_FIELD_MEAN_PARITY_FAIL__NO_FINAL_ARMS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`.
Primary prereg commit `3dbe53c88aa4030ca20bcca5481e7477d835bbdd`. A later duplicate prereg commit `647dfe8c369fa6eaf208458c8864fd820d3c3fc2` is non-authoritative.
R4 proved that broad per-candidate budgets + pre-emission admission + pair-total parity can all pass. The remaining integrity failure was applying <=10% cross-arm field-mean equality to the treatment-bearing `second_order_consequence` field itself (gap 0.156627). Final arms and scientific scores were never emitted.

Research Sync R10 changed CONTROL `b55be3bb0dc643bd42f49c2acfcb2897034d15b18c092a2e9a1f5e5970ddaa9e`, A `7da5edef689e822da94ebf2d8c651332ce30e9bd96f47b546d6940652bf2b95b`, B2 `4e30630ebe800028f97bfff61efb55c6bffcf14ef603478e0f7ad72e04d610a2`; B1/C1/C2-A/C2-B/D1/D2 byte-identical from R9. Parent mismatch 0; 21 evidence entries appended; CRC/path safety PASS; C2/DB59 unchanged.

## NEXT
Fresh R5 target-field-aware parity replication. Same broad per-field budgets both arms; same total verbosity controls; non-target fields only must satisfy cross-arm mean <=10%; `second_order_consequence` and `future_carry` remain individually bounded but are exempt from cross-arm mean equality. State Attachment both arms and Propagation Contract Treatment remain mandatory. H1-H4 effect thresholds unchanged. I4K-3 remains unauthorized.

No Active Engine/Production/DB/Formal/OpenAI Live promotion.