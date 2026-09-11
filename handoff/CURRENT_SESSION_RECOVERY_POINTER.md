# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-11

## READ FIRST
1. `handoff/20260911/START_HERE_P07_I4K_NEW_SESSION_HANDOFF_R6_20260911.md`
2. `handoff/20260911/P07_I4K_RESEARCH_SYNC_R24_PHYSICAL_CLOSURE_R1_20260911.md`
3. `handoff/20260911/P07_I4K_RESEARCH_SYNC_R24_DELIVERY_MANIFEST_R1_20260911.json`
4. `handoff/20260911/P07_I4K5R4A_ATTEMPT1_G5_SEMANTIC_NONLOSS_FAIL_R1_20260911.json`
5. `handoff/20260911/P07_I4K5R4A_ATTEMPT2_G5_EARLY_EXECUTION_SUPPLEMENT_R1_20260911.json`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R24__I4K5R4A_ATTEMPT1_PRESCORE_G5_REJECTED__ATTEMPT2_SERIES_SEALED__G5A_PENDING`
R24 root `8b42c029f14f344ce7fbfc9407ab3cce1f9692f16ba8659c6045a327e3a8d043`.

## EXACT RESEARCH STATE
R4A Attempt1: mechanical prescore PASS but G5 shared-upstream semantic nonloss FAIL; prescore rejected before mask/scoring. No quality result.
R4A Attempt2: final provisional attempt. G5A is mandatory before rendering. Fresh Series/Episode `해온 시민극장 / 객석 불이 꺼지기 전에` commit `3bc2da6d8717f2483073fe9cbfd078071f73ea20`.
Outputs: Series/Episode 1; Event Ecology 0; Sequence 0; Scene 0; G5A 0; Control 0; Treatment 0; Mask 0; Judges 0; mapping 0.

## MANDATORY RESUME ORDER
1. Verify R24 root and physical audit PASS.
2. Read Attempt2 fresh Series/Episode seal.
3. Create fresh Event Ecology with explicit mechanism / decision owner / future owner / second-order obligation / `future_adoption_target` for all events.
4. Seal 10 Sequence.
5. Seal 50 Scene.
6. Run G5A; stop if any semantic/future-thread nonloss fails.
7. Only then render Control/Treatment.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Formal 137; latest R138; R140 `0/0/0`.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R24__R4A_ATTEMPT2_SERIES_SEALED__EVENT_ECOLOGY_NEXT__G5A_BEFORE_RENDER`
