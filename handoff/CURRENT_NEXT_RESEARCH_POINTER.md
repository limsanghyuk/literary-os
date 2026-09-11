# CURRENT NEXT RESEARCH POINTER
Last updated: 2026-09-11

## CURRENT PHYSICAL BASELINE
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R21__I4K5R2_VALID_FAIL_CLOSED__I4K5R3_PSSB_PREREG_OUTPUTS_0`
R21 transport-set root SHA256 `65093f163ac38ab23e67153421494f0edf06a28bedac5debaa7d3a3be7de57eb`.
Active Engine `P07-I4H Recovery R3`; C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 frozen; Production `ENG:R47`; Formal 137; latest R138; R140 `0/0/0`.

## IMMUTABLE PREDECESSOR RESULT
I4K-5R2 = valid internal scored FAIL: H1 PASS / H2 FAIL / H3 PASS / H4 PASS. Treatment 8W/2T/2L. Stage-direction +0.125 and broadcast-readiness +0.250 failed frozen +0.30 thresholds. Preserve unchanged.

## ACTIVE EXPERIMENT
`P07-I4K-5R3-PERFORMANCE-SPECIFIC-SURFACE-BINDING-FRESH-REPLICATION`
Prereg commit `433dbfa0e9ac9c886dd04b89fddb4bbe7672a11b`.
Treatment adds only PSSB to the R2 repaired renderer baseline. Shared upstream semantics must be completely fresh and byte-identical between arms.

## CURRENT STATE
fresh Series/Episode = 0; Event Ecology = 0; Sequence Plan = 0; Scene Plan = 0; Control = 0; Treatment = 0; Mask = 0; Scores = 0; Unblind = 0.

## EXACT NEXT ACTION
1. Seal fresh Series/Episode state.
2. Seal fresh Event Ecology.
3. Seal shared 10-sequence plan.
4. Seal shared 50-scene plan.
5. Seal byte-identical Shared Upstream Architecture.
6. Only then begin provisional Control/Treatment rendering.

Do not lower R3 frozen H1-H4 thresholds. Do not inspect quality preference between provisional attempts. First prescore-admitted attempt becomes final.

## STATUS TOKEN
`NEXT_RESEARCH__SYNC_R21__I4K5R3_PSSB__OUTPUTS_0__NEXT_FRESH_SERIES_EPISODE_THEN_EVENT_SEQUENCE_SCENE`
