# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-11

## READ FIRST
1. `handoff/20260911/START_HERE_P07_I4K_NEW_SESSION_HANDOFF_R5_20260911.md`
2. `handoff/20260911/P07_I4K5R4_PREREG_SYNC_R23_PHYSICAL_CLOSURE_R1_20260911.md`
3. `handoff/20260911/P07_I4K5R4_INDEPENDENT_CONFIRMATION_PREREG_R1_20260911.json`
4. `handoff/20260911/P07_I4K5R3_INTERNAL_MASKED_FINAL_RESULT_R1_20260911.json`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R23__I4K5R4_INDEPENDENT_CONFIRMATION_PREREG__OUTPUTS_0`
R23 root `8c2c283ac7f378b30c23a255d5d9835afc1b056df8865710a09999ffb296e901`; closure commit `0323a74cc7f387b82e2dd053240b865465acf8e8`.

## EXACT EXPERIMENT STATE
R3 is immutable valid internal PASS; duplicate recovery score is quarantined and non-authoritative.
R4 independent confirmation prereg commit `aa38377c806a1be8041b64394c60f87cd0e333a7` is physically propagated in R23.
R4 outputs at current physical seal: Series/Episode 0; Event Ecology 0; Sequence Plan 0; Scene Plan 0; Control 0; Treatment 0; Mask 0; independent judge scores 0; mapping open 0; human validation 0.

## MANDATORY RESUME ORDER
1. Verify R23 root and read START_HERE R5.
2. Seal completely fresh R4 Series/Episode state.
3. Seal fresh Event Ecology.
4. Seal shared 10-sequence plan.
5. Seal shared 50-scene plan.
6. Seal one byte-identical Shared Upstream Architecture.
7. Only then render provisional Control/Treatment under frozen R4 arm definitions.
8. Prescore mechanics/semantic admission before mask.
9. Build leak-resistant mask; obtain three independent judge packets separately; only then open mapping.

## RUNTIME NOTE
Use streaming/selective large-file work. Earlier transport timeouts were page-cache pressure, not file corruption or OOM kill; latest R23 physical close has OOM=0 / oom_kill=0.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; Formal 137; latest R138; R140 `0/0/0`.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R23__I4K5R4_PREREG_OUTPUTS_0__NEXT_FRESH_SERIES_EPISODE`
