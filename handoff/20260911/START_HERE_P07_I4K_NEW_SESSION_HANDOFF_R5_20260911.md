# START HERE — P07 I4K NEW SESSION HANDOFF R5
Date: 2026-09-11

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R23__I4K5R4_INDEPENDENT_CONFIRMATION_PREREG__OUTPUTS_0`

Sync R23 transport root SHA256:
`8c2c283ac7f378b30c23a255d5d9835afc1b056df8865710a09999ffb296e901`

Physical closure:
`handoff/20260911/P07_I4K5R4_PREREG_SYNC_R23_PHYSICAL_CLOSURE_R1_20260911.md`
commit `0323a74cc7f387b82e2dd053240b865465acf8e8`.

Read order: `CONTROL -> A -> B1 -> B2 -> C1 -> C2(A+B) -> D1 -> D2`.

## IMMUTABLE R3 EVIDENCE
I4K-5R3 canonical score seal `90a0d7985025fa0ebf221ae32aaa942b82271b50`; canonical result `c241d0d7d030d143f2cd2e145308f9858953d566`.
Treatment 9W/2T/1L; H1/H2/H3/H4 all PASS. Dialogue +0.375; Stage Direction +0.875; Broadcast Readiness +0.7916666667.
Duplicate recovery score `f760cebfda473696654f535ffefc6c0373100212` is NON-AUTHORITY and quarantined by `61d3d180e804777594c5197a994c67fea1beeadf`.

## ACTIVE R4 EXPERIMENT
`P07-I4K-5R4-PSSB-INDEPENDENT-MASKED-FRESH-CONFIRMATION`
Prereg commit `aa38377c806a1be8041b64394c60f87cd0e333a7`.
R4 freezes R3 PSSB and unchanged H1-H4 thresholds. It requires completely fresh unseen material, byte-identical shared upstream between arms, separated generation/evaluation, three independent masked judges, sealed judge packets before mapping open, and no authoritative quality scoring by the generation agent.

## R4 OUTPUT STATE AT THIS PHYSICAL SEAL
Series/Episode 0; Event Ecology 0; Sequence Plan 0; Scene Plan 0; Control 0; Treatment 0; Mask 0; independent judge scores 0; mapping open 0; human validation 0.

## EXACT NEXT ACTION
Seal a completely fresh R4 Series/Episode state only. Then seal fresh Event Ecology, shared 10-sequence plan, shared 50-scene plan and one byte-identical Shared Upstream Architecture. Do not render either arm before the upstream seal.

## CLAIM BOUNDARY
Even an R4 independent-judge PASS authorizes fresh-human validation only. It does not promote Active Engine, Production, DB, Formal count or R140.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`; Formal 137; latest R138; R140 `0/0/0`.

## INFRASTRUCTURE
Use streaming/selective large-file verification. Page-cache pressure, not OOM or corruption, caused earlier tool timeouts; latest R23 close has OOM=0 / oom_kill=0.
