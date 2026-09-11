# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-11

## READ FIRST
1. `handoff/20260911/START_HERE_P07_I4K_NEW_SESSION_HANDOFF_R4_20260911.md`
2. `handoff/20260911/P07_I4K5R3_INTERNAL_PASS_SYNC_R22_PHYSICAL_CLOSURE_R2_20260911.md`
3. `handoff/20260911/P07_I4K5R3_INTERNAL_MASKED_FINAL_RESULT_R1_20260911.json`
4. `handoff/20260911/P07_I4K5R3_RECOVERY_DUPLICATE_RESCORE_QUARANTINE_R1_20260911.json`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R22__I4K5R3_INTERNAL_PASS__DUPLICATE_RESCORE_QUARANTINED__INDEPENDENT_CONFIRMATION_PENDING`
Definitive R22 root `b23866b816991da70a0262ab430fc5736fd394e838b4508010ed09ad806ba4aa`; closure R2 commit `26943e7c159a156c72570bcba95fce22046d9317`.

## EXACT EXPERIMENT STATE
I4K-5R3 is CLOSED. Canonical score seal `90a0d7985025fa0ebf221ae32aaa942b82271b50`; canonical final result `c241d0d7d030d143f2cd2e145308f9858953d566`.
Treatment = 9W/2T/1L; H1/H2/H3/H4 all PASS. Dialogue +0.375; Stage Direction +0.875; Broadcast Readiness +0.7916666667.
Duplicate recovery score `f760cebfda473696654f535ffefc6c0373100212` is non-authority and quarantined by `61d3d180e804777594c5197a994c67fea1beeadf`.

## MANDATORY RESUME ORDER
1. Verify R22 root `b23866b8...a4aa` and read START_HERE R4.
2. Never score, remask, rerender, or unblind R3 again.
3. Treat `P07-I4K-5R4 INDEPENDENT CONFIRMATION` as candidate-only, outputs 0.
4. Seal R4 prospective preregistration before any R4 output.
5. Freeze PSSB and thresholds; use fresh unseen material and separate generation/evaluation.
6. Run independent masked confirmation first; fresh-human validation next when available.
7. No operational promotion from R3 alone.

## RUNTIME / TOOL NOTE
Some earlier interruptions were page-cache pressure near the 4GiB cgroup limit; recent final R22 audit closed with OOM=0 / oom_kill=0. Use selective/streaming work, avoid duplicate large-file reads and whole-archive extraction, and release page cache safely if necessary.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; Formal 137; latest R138; R140 `0/0/0`.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R22_DEFINITIVE__R3_VALID_INTERNAL_PASS_CLOSED__DUPLICATE_QUARANTINED__NEXT_R4_PREREG`
