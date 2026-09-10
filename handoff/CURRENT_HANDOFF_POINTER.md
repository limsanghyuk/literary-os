# CURRENT HANDOFF POINTER
Last updated: 2026-09-10

## READ FIRST
1. `handoff/20260910/P07_I4K5_RESEARCH_SYNC_R15_PHYSICAL_CLOSURE_R1_20260910.md`
2. `handoff/20260910/P07_I4K5_INDEPENDENT_EXTERNAL_GPT_PREREG_R1_20260910.json`
3. `handoff/20260910/P07_I4K5_JUDGE_PACKET_AND_MAPPING_HASH_SEAL_R1_20260910.json`
4. `handoff/20260910/P07_I4K4_RESEARCH_SYNC_R14_PHYSICAL_CLOSURE_R1_20260910.md`
5. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
6. `handoff/CURRENT_NEXT_RESEARCH_POINTER.md`
7. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R15__I4K5_PREREG_PACKETS_SEALED_AWAITING_EXTERNAL_JUDGES`
Material SHA256: `a21bdf7368541682e30828275e38d7a2018ed3c3d9c1da9eacbadf1af2f3cb8c`.
Active Engine `P07-I4H Recovery R3`; Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`; DB59 frozen; Production `ENG:R47`; Formal `137`; latest `R138`; R140 `0/0/0`.

## I4K-5 STATE
Experiment: `P07-I4K-5-INDEPENDENT-HUMAN-EXTERNAL-QUALIFICATION-GATE`.
Primary execution mode: independent external multi-GPT; human consensus is not claimed by this mode.
Prereg commit `bcad5e951dd9e3358ea7f9696c4ed664ffff58a2`; freeze commit `8e669634fbab5b5712e0a0cace9014def6f5279c`; packet/mapping hash seal commit `48d37639a3cdfdb57176243d6ae03c27e5ab3100`.
Secret mapping SHA256 `725f835788a7e53917d201a3968d1e562df4cb06302915ae2294db760ae19806`; mapping contents remain coordinator-private.
Judge responses 0 / valid judges 0 / unblind 0 / verdict none.

Historical method recovery confirmed same-model AI-judge-AI 15/15 was previously declared unreliable; later designs required multiple independent judges/source hiding/agreement reporting. I4D showed 3 wins+2 ties/9 can be meaningful human-competitive signal; I4G preserved its nonloss threshold even after 8 wins. Therefore I4K-5 uses blind win/tie/loss as primary evidence and ceiling-sensitive small-repeatable-gain logic rather than requiring a large raw-score jump.

## NEXT
Release J01/J02/J03 to three separate fresh GPT conversations outside this Project. Do not share the coordinator map, I4K-4 internal scores, Hub, or other judge responses. Seal each exact response and SHA in receipt order. J04/J05 are replacement-only for protocol-invalid/no-response, never for an unfavorable valid judge. Do not open the map for analysis until three valid responses are sealed.

## STATUS TOKEN
`CURRENT_HANDOFF__SYNC_R15_A21BDF73__I4K5_PREREG_PACKETS_SEALED__JUDGES_0__UNBLIND_0__ACTIVE_I4H_R3__DB59__PRODUCTION_R47__FORMAL_137__R140_0_0_0`