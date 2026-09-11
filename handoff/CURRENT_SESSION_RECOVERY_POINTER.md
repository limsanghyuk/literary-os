# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-11

## READ FIRST
1. `handoff/20260911/START_HERE_P07_I4K_NEW_SESSION_HANDOFF_R6_20260911.md`
2. `handoff/20260911/P07_I4K_RESEARCH_SYNC_R24_PHYSICAL_CLOSURE_R1_20260911.md`
3. `handoff/20260911/P07_I4K5R4A_ATTEMPT2_G5A_PRE_RENDER_SEMANTIC_NONLOSS_PASS_R1_20260911.json`
4. `handoff/20260911/P07_I4K5R4A_ATTEMPT2_SHARED_UPSTREAM_ARCHITECTURE_SEAL_R1_20260911.json`
5. `handoff/20260911/P07_I4K5R4A_EXPRESSION_HYGIENE_INDEPENDENT_CONFIRMATION_PREREG_R1_20260911.json`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R24__I4K5R4A_ATTEMPT1_PRESCORE_G5_REJECTED__ATTEMPT2_SERIES_SEALED__G5A_PENDING`
R24 root `8b42c029f14f344ce7fbfc9407ab3cce1f9692f16ba8659c6045a327e3a8d043`. Post-R24 progress is not physically propagated yet.

## EXACT RESEARCH STATE
R4A Attempt2 Series/Event/10 Sequence/50 Scene all sealed. G5A PASS commit `4f7a6e54d3be12f21d4c7a8802f4a75fbcaca351`. Shared Upstream seal commit `4585fd2c79e386b511f092f2b945aa904ab2cff8`, binding `8e023a006aa9ff9fca9ef5b0a0cf5d5735d69e992f4f102a2e6734c5076aadd6`.
Outputs: Control 0; Treatment 0; Mask 0; Judges 0; mapping 0.

## MANDATORY RESUME ORDER
1. Verify R24 root and read G5A PASS + Shared Upstream seal.
2. Render Control SQ01-SQ10 only from exact sealed 50 Scene semantics.
3. Shared Actor-Visible Expression Hygiene applies; Control has NO PSSB.
4. Run Control scale/hygiene prescore before any Treatment prose.
5. Only after Control PASS render Treatment with same upstream + same expression hygiene + frozen PSSB.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Formal 137; latest R138; R140 `0/0/0`.

## STATUS TOKEN
`SESSION_RECOVERY__SYNC_R24__POST_R24_R4A_ATTEMPT2_G5A_PASS__SHARED_UPSTREAM_SEALED__CONTROL_NEXT`
