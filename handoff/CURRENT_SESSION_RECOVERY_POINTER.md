# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-11

## READ FIRST
1. `handoff/20260911/START_HERE_P07_I4K_NEW_SESSION_HANDOFF_R3_20260911.md`
2. `handoff/20260911/P07_I4K5R2_CLOSED_I4K5R3_PREREG_SYNC_R21_PHYSICAL_CLOSURE_R1_20260911.md`
3. `handoff/20260911/P07_I4K5R3_PSSB_FRESH_REPLICATION_PREREG_R1_20260911.json`
4. `handoff/20260911/P07_I4K5R2_INTERNAL_MASKED_FINAL_RESULT_R1_20260911.json`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R21__I4K5R2_VALID_FAIL_CLOSED__I4K5R3_PSSB_PREREG_OUTPUTS_0`
R21 root `65093f163ac38ab23e67153421494f0edf06a28bedac5debaa7d3a3be7de57eb`; closure commit `67e6d51ac73324a9f257501443dd9bed61e61b31`.

## EXACT EXPERIMENT STATE
I4K-5R2 is closed and immutable: 8W/2T/2L; H1 PASS / H2 FAIL / H3 PASS / H4 PASS.
I4K-5R3 PSSB fresh replication is preregistered at `433dbfa0e9ac9c886dd04b89fddb4bbe7672a11b` with no outputs yet.

R3 outputs at current physical seal:
- Series/Episode 0
- Event Ecology 0
- Sequence Plan 0
- Scene Plan 0
- Control 0
- Treatment 0
- Mask 0
- Scores 0
- Unblind 0

## MANDATORY RESUME ORDER
1. Verify R21 root and read START_HERE R3.
2. Seal completely fresh Series/Episode state.
3. Seal fresh Event Ecology.
4. Seal shared 10-sequence plan.
5. Seal shared 50-scene plan.
6. Seal one byte-identical Shared Upstream Architecture for both arms.
7. Only then render provisional Control and Treatment under frozen R3 arm definitions.
8. Deterministic prescore only; no quality inspection between attempts.
9. Semantic/continuity admission PASS only permits masking/scoring/unblind.

## RUNTIME / TOOL NOTE
R21 audit closed with OOM=0 / OOM-kill=0. Continue selective/streaming large-file work; avoid unnecessary whole archive extraction and concurrent decompression.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Formal 137; latest R138; R140 `0/0/0`.

## STATUS TOKEN
`SESSION_RECOVERY__PHYSICAL_SYNC_R21__I4K5R2_VALID_FAIL_CLOSED__I4K5R3_PREREG_OUTPUTS_0__NEXT_FRESH_UPSTREAM`
