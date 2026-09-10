# CURRENT HANDOFF POINTER
Last updated: 2026-09-10

## READ FIRST
1. `handoff/20260910/P07_I4K5_R2_RESEARCH_SYNC_R16_PHYSICAL_CLOSURE_R1_20260910.md`
2. `handoff/20260910/P07_I4K5_PRE_RELEASE_PROTOCOL_CORRECTION_R2_20260910.md`
3. `handoff/20260910/P07_I4K5_JUDGE_RELEASE_MANIFEST_R2_20260910.json`
4. `handoff/20260910/P07_I4K5_INDEPENDENT_EXTERNAL_GPT_PREREG_R1_20260910.json`
5. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
6. `handoff/CURRENT_NEXT_RESEARCH_POINTER.md`
7. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R16__I4K5_R2_PACKETS_SEALED_AWAITING_EXTERNAL_JUDGES`
Material SHA256: `4f8c9be99c318fd5f15fc58f8a980f4fa123525a7cf4fc9c2eb3f50551c81ce3`.
Active Engine `P07-I4H Recovery R3`; Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 frozen; Production `ENG:R47`; Formal 137; latest R138; R140 `0/0/0`.

## I4K-5 STATE
Original R1 judge packets are `SUPERSEDED_PRE_RELEASE__DO_NOT_USE` because coordinator-side integrity inspection made their A/B identity inferable before any judge response. Judge responses remained 0; scientific unblind remained 0.

Correct release authority is R2. Protocol correction commit `150a0254792541f1debf8835285c8d6050cb110c`; R2 packet manifest seal commit `c8b9bde3568b02030af70027337ed33d0c385e97`; R2 secret map SHA `2f8f209ab31668756d6fff747ab8993293916d7463fac9c484759b5e17606f47`. Mapping contents remain coordinator-private.

R2 integrity: every judge packet contains the exact two sealed I4K-4 episode bodies as an unordered pair, each 10 sequences / 50 scenes; instructions and JSON response template complete; arm/internal-result leakage in episode bodies 0; ZIP CRC PASS.

Scale boundary: final source files passed the frozen file-level 35k metric at 35,382/35,007 chars. After anonymized metadata-wrapper replacement, packet screenplay bodies are 35,346/34,969. No screenplay content was truncated. Do not claim both metadata-excluded bodies exceed 35k; future work must preregister `screenplay_body_chars` excluding metadata.

## NEXT
Release only R2 J01/J02/J03 to three separate fresh GPT conversations outside this Project. Do not use R1. Seal each exact response before any mapping reveal. J04/J05 are replacement-only for protocol-invalid/no-response. Judge responses 0 / unblind 0 / verdict none.

## STATUS TOKEN
`CURRENT_HANDOFF__SYNC_R16_4F8C9BE9__I4K5_R2_RELEASE_READY__R1_SUPERSEDED__RESPONSES_0__UNBLIND_0__ACTIVE_I4H_R3__DB59__PRODUCTION_R47__FORMAL_137__R140_0_0_0`