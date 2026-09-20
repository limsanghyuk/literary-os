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
`PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

Canonical preregistration:
`research/interventions/20260920/R63_F01_SEMANTIC_APPLICABILITY_ABSTENTION_PREREG_R1.md`

Preregistration commit:
`a91180860dde0f7503a8b47f7358a966df53123f`

Control:
exact SYNC-R58 / ADAPTIVE_UL16.

Treatment boundary:
R62 F01 diversification lineage + semantic-license gate + exact R58 fallback on ABSTAIN. No F04/F06/F07/F08 patch.

Known R62 losses C06/C08/C11 are regression-only and cannot enter the fresh primary qualification set.

Next operation:
`IMPLEMENT_R63_F01_LICENSE_GATE -> KNOWN_FAILURE_REGRESSION -> SOURCE_FREEZE -> FRESH_12_CASE_PRIMARY`

Do not start F04.
