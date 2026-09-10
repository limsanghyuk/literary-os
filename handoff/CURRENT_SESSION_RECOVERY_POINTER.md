# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-10

## CURRENT DURABLE STATE
Physical research-sync authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R9__I4K2P_R3_HOLD_PREEMISSION_ADMISSION_EXHAUSTED`.
Nine-file material SHA256: `5a3581e579008798f12b6d7d6650228185ae89095f52c1f5ccab192445745732`.
Active engine `P07-I4H Recovery R3`; combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Production `ENG:R47`; Formal `137`; latest `R138`; R140 `0/0/0`.

## LATEST CLOSED RESEARCH
I4K-2P R3 prereg commit `63a3053b75aaacecfa5fce885578118bbe9829a6`. BASELINE provisional attempts 1-3 exhausted the frozen maximum without all 12 slots satisfying the per-field pair-target ±4-character gate. No final arms, Treatment attempts, mask, scores, unblind, or H1-H4 verdict exist. Verdict: `HOLD__PREEMISSION_BASELINE_ADMISSION_EXHAUSTED__NO_FINAL_ARMS__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`.

## RESUME ORDER
1. Runtime/filesystem/cgroup/OOM preflight.
2. Verify Sync R9 material SHA.
3. Do not modify/score R1/R2/R3 HOLD candidates.
4. Freeze fresh `P07-I4K-2P-R4-BROAD-BUDGET-PREEMISSION-GATED-PROPAGATION-REPLICATION` before output.
5. Keep broad R2 field budgets, deterministic pre-emission admission, max 3 provisional attempts, attempt hashes, State Attachment both arms, Propagation Contract Treatment only.
6. Enforce representation parity by pair-total / arm-mean / field-mean gates, not ±4 chars per field.
7. Only after all final candidates pass admission/parity may masking and scoring begin.
8. Only H1-H4 full PASS may authorize I4K-3.
9. Physical sync after meaningful research.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R9_5A3581E5__I4K2P_R3_HOLD__R4_BROAD_BUDGET_GATE_NEXT__NO_I4K3__ACTIVE_I4H_R3__DB59__FORMAL_137__R140_0_0_0`