# R66 External Blind Pending Handoff R1

Date: 2026-09-20
Status: `R66_ACTIVE__PREBLIND_PASS__WAITING_EXTERNAL_BLIND_3_JUDGES`

## Authority
- Physical authority: SYNC-R63
- Active qualified Candidate: exact SYNC-R58 / ADAPTIVE_UL16
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59
- Research DB: DB64
- R66 Treatment: research-only, not active

## R66 frozen chain
Preregistration commit:
`e52ac3fdf06fe45670e9a728cac6fb91c98727e6`

Implementation freeze commit:
`f2a207a86700eb94bfd63a55a7e81d7fc2e26c5f`

Fresh-input seal commit:
`8fcc6bf73c1173e40a9f249dd25777e697646e40`

Pre-blind result commit:
`1bb956f1b75715b6ba4daee2c017e91734885514`

External-blind protocol commit:
`cdc2835ba8249e2991c25edbdac3031b4ed4204e`

## Pre-blind state
- Control 12/12 PASS
- Treatment 12/12 PASS
- selector-safety PASS
- Treatment ACCEPT 29 / ABSTAIN 18
- known failures 8/8 blocked
- external blind NOT YET RUN

## Judge packet hashes
- J01: `c87f361fbec52d52b98f840d0045b493839bd5d12a147a54bc0ed552f6edba4b`
- J02: `e263ab9c5ed4fc5b96e91f95a0f845607d851021e0d9c0b332f3cdd37df40222`
- J03: `390b528c3a7aff921e7143b9657725cd9287c1f77a314e399a5aee950181fde6`
- dispatch bundle: `0a5b7f99dcfffebf15a2ace135388511312ca21fd7721fe1ec592aeeff340f0f`
- coordinator mapping JSON: `be8d1548598bbd49d0908af0d70c968ab0687467feb99747fa245c08c7371748`
- coordinator secret ZIP: `86942e71c3f7d289c44df67f63b17ee3811848c36dbbb400788f23a5991204a5`

## Continuation
Collect valid J01/J02/J03 judgments independently.
Do not reveal coordinator mapping until all three valid judgments are sealed.
Then map/aggregate using the frozen R62-style majority rule and frozen R66 gate.

Do not tune R66 source, regenerate cases, regenerate packets, or replace an unfavorable valid judgment.
