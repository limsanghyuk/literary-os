# CURRENT NEXT RESEARCH POINTER
Last updated: 2026-09-20

## CURRENT STATE
- Latest physical authority: **SYNC-R60**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Quarantined research evidence: **SYNC-R59 / R62 F01**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64**

## CLOSED
- R59 CLOSED HOLD
- R60 CLOSED PASS
- R61 CLOSED
- R62 CLOSED FAIL — 9W / 0T / 3L

## R63
Title:
`F01 Semantic Applicability + Abstention Gate`

Status:
`IMPLEMENTED_SOURCE_FROZEN__FRESH_PRIMARY_NOT_CREATED`

Preregistration:
`research/interventions/20260920/R63_F01_SEMANTIC_APPLICABILITY_ABSTENTION_PREREG_R1.md`
Prereg commit:
`a91180860dde0f7503a8b47f7358a966df53123f`

Implementation freeze:
`research/interventions/20260920/R63_F01_IMPLEMENTATION_FREEZE_R1.md`
Freeze commit:
`2618f84a09cf27c3d6f8c8c06923a05b0f81dd2b`

Frozen Treatment adaptive source SHA256:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

F01-only diff SHA256:
`ff007539ed3843ede68e882ac1538d680687a1b385342335daecb8a44fc0a5ad`

Known R62 failures C06/C08/C11: regression-only repair PASS.
R58B regression: PASS.
Whole runtime compile: 45/45 PASS.

## NEXT
Create and seal 12 fresh primary cases after the frozen Treatment source, then run exact R58 Control vs frozen R63 Treatment.

No source tuning after fresh-case creation.
Do not start F04.
