# R66 F01 Boundary-Safe Predicate Parser — Final Result R1

Date: 2026-09-20
Status: `CLOSED_PASS__EXTERNAL_BLIND_12W_0T_0L__ZERO_CONFIRMED_CRITICAL`

## Authority at experiment close
- Physical authority before post-R66 reseal: **SYNC-R63**
- Active qualified Candidate before R66 close: **SYNC-R58 / ADAPTIVE_UL16**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**

## Frozen chain
Preregistration commit:
`e52ac3fdf06fe45670e9a728cac6fb91c98727e6`

Implementation freeze commit:
`f2a207a86700eb94bfd63a55a7e81d7fc2e26c5f`

Frozen R66 Treatment source SHA256:
`0558c910896556048bb6acf0e1d4097477c3c31a60d47f16c4bd83e3f6253f1d`

Fresh-input seal commit:
`8fcc6bf73c1173e40a9f249dd25777e697646e40`

Fresh primary SHA256:
`9ba77865f1fd4f9f9ec91a23456686c026269f3ec5ed62c3490f2e43065bc5a7`

Pre-blind result commit:
`1bb956f1b75715b6ba4daee2c017e91734885514`

External-blind protocol commit:
`cdc2835ba8249e2991c25edbdac3031b4ed4204e`

## Judgment custody
Raw uploaded judgment SHA256:
- J01: `33fbc3da74a79d2d32121e6bad8f9aa17d5f650e2ceb74c6703f5be42c369612`
- J02: `93962424ebe74008669f59c5e3f971e75cf5930d232df3e714ca1c68e3fa6b9b`
- J03: `84b64bb7bcbab0da3ee7d036c3a2f961f442f303e78ba04cc0f33964fb715587`

Canonical normalized judgment SHA256:
- J01: `65ccf9b433e4963749fad0729357d705f52ee93a37b36d8073d90239a2aa49e3`
- J02: `6b5d388c5b53d0051d2ccabd60d4b0c84bab447703eddb6ddeb141ae9d5a8c9d`
- J03: `6c4885bdf1522611bec6643c7e45abb1fb1323e6ede36b6f9c35d71e71ece750`

All three:
- valid JSON;
- expected judge_id;
- independence_attestation = true;
- 12/12 pairs present;
- all 8 score axes present with integer 1-10 scores;
- winner values valid.

Coordinator mapping JSON SHA256:
`be8d1548598bbd49d0908af0d70c968ab0687467feb99747fa245c08c7371748`

External-blind aggregation JSON SHA256:
`d22ac68d634fd8ac187e9c4039a5e35cb51abbc741bb78f1fa5479472c62e055`

Final external-blind evidence ZIP SHA256:
`440e4105539e7daf53c5f48487b25090f0dbad92be4110f9e10b646139518b0c`

## Mapped 3-judge result
Every judge selected the mapped Treatment arm in every pair.

Pair outcomes:
- R66C01 AQUARIUM_FILTER — Treatment WIN 3/3
- R66C02 SATELLITE_LABEL — Treatment WIN 3/3
- R66C03 GRANT_SUBMISSION — Treatment WIN 3/3
- R66C04 HYDRAULIC_PRESS — Treatment WIN 3/3
- R66C05 ROBOT_ARM — Treatment WIN 3/3
- R66C06 ARCHIVE_SCAN — Treatment WIN 3/3
- R66C07 WIND_SENSOR — Treatment WIN 3/3
- R66C08 PHARMA_BATCH — Treatment WIN 3/3
- R66C09 FILM_LOCATION — Treatment WIN 3/3
- R66C10 PORT_CRANE — Treatment WIN 3/3
- R66C11 GREENHOUSE_FROST — Treatment WIN 3/3
- R66C12 COMMUNITY_CLINIC — Treatment WIN 3/3

Aggregate:
- Treatment wins: **12/12**
- ties: **0/12**
- losses: **0/12**
- wins + ties: **12/12**
- mapped Treatment votes: **36/36**
- confirmed Treatment critical violations under frozen 2-of-3 rule: **0**

## R66C10 critical note
J01 flagged `due obligation omitted` on both blind arms.
After mapping, that is one Treatment critical vote and one Control critical vote from J01.

J02 and J03 did not flag a Treatment critical violation for the mapped Treatment arm; both interpreted the dependency-constrained E1 as blocked/open rather than falsely resolved.

Frozen critical aggregation requires >=2/3 judges on the Treatment arm.
Therefore:
`R66C10_TREATMENT_CRITICAL_CONFIRMED = FALSE`

No judgment was modified or rerun.

## Frozen qualification gate
- Treatment wins >= 7/12: **PASS (12)**
- Treatment wins + ties >= 10/12: **PASS (12)**
- Treatment losses <= 2/12: **PASS (0)**
- zero confirmed Treatment critical violations: **PASS**

Final:
`R66 = CLOSED PASS`

## Score-direction descriptive summary
Across all 36 mapped judge evaluations:
- Transaction Specificity: Treatment 8.194 vs Control 6.917
- Causal Coherence: 8.500 vs 8.056
- Resistance/Choice/Cost: 6.556 vs 5.722
- Non-Mechanical Progression: 7.222 vs 5.139
- Scene/Step Necessity: 7.083 vs 6.278
- Obligation Fidelity: 9.806 vs 9.806
- Semantic Applicability: 8.722 vs 6.472
- Unsupported Novelty / Premature Resolution Safety: 9.028 vs 8.667
- all-axis mean: Treatment 8.139 vs Control 7.132

These descriptive scores do not replace the preregistered win/tie/loss gate.

## Claim boundary
R66 PASS establishes only:

`F01_BOUNDARY_SAFE_PREDICATE_PARSER_GATE = QUALIFIED_AT_PLANNING/SCENE-CONTRACT_LEVEL`

It does NOT establish:
- F04 semantic repetition closure;
- F06 scene necessity closure;
- F07 runtime State Carry enforcement;
- F08 Provider-context closure;
- full screenplay-surface quality;
- Production promotion.

Production remains ENG:R47 / LEGACY_R53.

## Candidate consequence
The frozen R66 source is now a **qualified F01 successor candidate** to the previous SYNC-R58 candidate at the planning/scene-contract scope.

Any change of active candidate binding requires a separate audited physicalization/reseal step.
Until that reseal is complete, physical authority remains SYNC-R63 and the currently packaged active runtime remains the previous exact SYNC-R58 bytes.

## Next operation
`POST_R66_QUALIFIED_CANDIDATE_PHYSICALIZATION`

Required:
- build successor 5-Part / 9-Package authority;
- bind Candidate runtime to exact frozen R66 source;
- preserve exact SYNC-R58 as qualified parent/fallback evidence;
- preserve R62-R65 failed evidence;
- preserve all R66 prereg/source/input/judgment/mapping/result evidence;
- Production unchanged;
- DB59 unchanged;
- full SHA/CRC/C2/trust-root/secret/download audit.

Status token:
`R66_CLOSED_PASS__12W_0T_0L__36_OF_36_TREATMENT_VOTES__ZERO_CONFIRMED_CRITICAL__F01_QUALIFIED__PRODUCTION_UNCHANGED__PHYSICALIZATION_PENDING`
