# P07 I4K-5R3 INTERNAL PASS — SYNC R22 PHYSICAL CLOSURE R2 (FINAL)
Date: 2026-09-11

## FINAL PHYSICAL RESEARCH AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R22__I4K5R3_INTERNAL_PASS__DUPLICATE_RESCORE_QUARANTINED__INDEPENDENT_CONFIRMATION_PENDING`

Parent Sync R21 root: `65093f163ac38ab23e67153421494f0edf06a28bedac5debaa7d3a3be7de57eb`.
Final R22 transport-set root SHA256: `b23866b816991da70a0262ab430fc5736fd394e838b4508010ed09ad806ba4aa`.

`P07_I4K5R3_INTERNAL_PASS_SYNC_R22_PHYSICAL_CLOSURE_R1_20260911.md` and provisional root `ad20094f...` predated propagation of the already-authoritative duplicate-rescore quarantine. R1 is superseded by this R2 and must not be used as current authority.

## PHYSICAL LAYOUT
Read order: `CONTROL -> A -> B1 -> B2 -> C1 -> C2(A+B) -> D1 -> D2`.
Changed append-only transports: CONTROL / A / B2.
Byte-identical transports: B1 / C1 / C2-A / C2-B / D1 / D2.
R22 delivery directory contains all 9 physical transport files, including C2-A and C2-B.

## FINAL AUDIT
- 9/9 outer transport SHA256 values calculated and sealed.
- Changed ZIP full CRC/testzip PASS 3/3.
- R21 parent-entry metadata mismatch = 0 in CONTROL/A/B2.
- Exactly 10 unique `research_sync_r22/` entries in each changed ZIP.
- duplicate / unsafe path / symlink / encrypted entry = 0 for changed ZIPs.
- B2 local/central filename mismatch = 0.
- Combined C2 = 318,368,553 bytes / `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7` PASS.
- DB59 = 259,756,521 bytes / `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9` PASS.

## CANONICAL R3 RESULT
Canonical masked score seal commit: `90a0d7985025fa0ebf221ae32aaa942b82271b50`.
Canonical final result commit: `c241d0d7d030d143f2cd2e145308f9858953d566`.
Treatment 9W/2T/1L, nonloss 11/12. H1 PASS / H2 PASS / H3 PASS / H4 PASS.
Surface deltas: Dialogue/Subtext +0.375; Stage-Direction Playability +0.875; Broadcast Readiness +0.7916666667.
Overall: `PASS__INTERNAL_ONLY_PSSB_REPLICATION_SIGNAL__NEXT_RESEARCH_AUTHORIZED`.

## RECOVERY DUPLICATE QUARANTINE
Stale recovery state caused duplicate score commit `f760cebfda473696654f535ffefc6c0373100212` after the canonical result already existed. It is NON-AUTHORITY. Quarantine commit `61d3d180e804777594c5197a994c67fea1beeadf` preserves the earlier canonical score/result and prohibits replacement, averaging, or a second unblind/result. This quarantine is physically propagated in R22.

## CLAIM BOUNDARY
R3 is masked same-agent internal development evidence only. No Active Engine, Production, DB59, Formal count, R140, OpenAI Live, independent external judge, or fresh-human promotion occurs.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Formal scored count 137; latest Formal R138; Formal R140 `0/0/0`.

## NEXT LEGAL RESEARCH BOUNDARY
I4K-5R4 Independent Confirmation is candidate only (`CANDIDATE_ONLY__NOT_PREREGISTERED__NO_OUTPUTS`). Seal its preregistration before any R4 output.