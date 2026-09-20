# R63 — F01 Semantic Applicability + Abstention Gate — Primary Mechanical / Safety Result R1

Date: 2026-09-20
Status:
`R63 = CLOSED_FAIL__PREBLIND_SELECTOR_SAFETY_GATE__LEXICAL_SEMANTIC_FALSE_POSITIVE`

## Frozen prerequisites
Preregistration:
`research/interventions/20260920/R63_F01_SEMANTIC_APPLICABILITY_ABSTENTION_PREREG_R1.md`
commit:
`a91180860dde0f7503a8b47f7358a966df53123f`

Frozen Treatment source SHA256:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

F01-only diff SHA256:
`ff007539ed3843ede68e882ac1538d680687a1b385342335daecb8a44fc0a5ad`

Fresh primary case JSON SHA256:
`5c7f04816c00a2f5afc42a8c2862f5e888000a2fbefde28f9c73f03c1cdb3376`

Fresh primary seal commit:
`581cc4033f673096553ee304ee540060884f4542`

## Arm custody
Exact R58 Control output:
- SHA256: `0c75ca2f20ac14c5770dab819d4ae77490d8cdaebdf5a58569bcd39af1424764`
- bytes: 271400

Frozen R63 Treatment output:
- SHA256: `73a1a57e752050f41201265910f97893d5f272f48321070172440a9b2185f4d6`
- bytes: 286931

## Structural / state mechanical gate
Both arms:
- 12/12 architecture validation PASS
- each case: 4 due + 1 deferred
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate concrete action gate PASS

Treatment selector counts across 48 due obligations:
- ACCEPT: 29
- ABSTAIN: 19

Treatment family diversity:
- distinct precursor families: 15
- entropy: 3.5009619827626763
- repeated path ratio: 0.875

Control:
- distinct precursor families: 6
- entropy: 2.403908991804247
- repeated path ratio: 1.0

The intervention therefore transmitted and did not collapse to always-abstain.

## Pre-blind semantic-safety failure
The preregistered safety rule required every diversified ACCEPT to be semantically licensed by the obligation's dramatic function, not merely by lexical overlap.

At least two clear fresh violations were found.

### R63C01_AIRPORT_DEICING / R63C01-E1
Input:
`제빙 호스 압력이 떨어져 첫 분사 시험이 실패한다`

Treatment:
`PRESSURE_ESCALATION`

Reason emitted:
`LICENSED_ESCALATION_TRAJECTORY`

Defect:
The license accepted the Korean token `압력` as dramatic pressure even though it means physical hose pressure. The obligation requires equipment failure / handling, not a dramatic pressure-escalation transaction.

Classification:
`DOMAIN_POLYSEMY_FALSE_POSITIVE__PHYSICAL_PRESSURE_AS_DRAMATIC_PRESSURE`

### R63C04_SUBWAY_TUNNEL / R63C04-E1
Obstacle:
`막차 운행 전 점검을 끝내야 한다`

Treatment:
`COUNTERMOVE`

Reason emitted:
`LICENSED_RESPONSE_TO_PRIOR_MOVE`

Defect:
The rule searched obstacle text for the substring `막` as evidence of an opposing move. It matched `막차` (last train), where no actor has blocked or countered anything.

Classification:
`SUBSTRING_BOUNDARY_FALSE_POSITIVE__MAKCHA_AS_BLOCKING_MOVE`

This violates the frozen R63 contract:
- absence of positive semantic support is not support;
- ambiguity must ABSTAIN;
- COUNTERMOVE requires an identifiable prior opposing move;
- PRESSURE_ESCALATION requires a dramatic pressure trajectory;
- unsupported family selection is a safety failure before blind quality evaluation.

## Root cause
R63 added a second gate but its evidence extraction remained lexical and partly correlated with the R62 proposal mechanism.

Two failure modes:
1. domain polysemy: the same surface token has different semantic roles;
2. substring collision: unbounded token matching treats a token embedded inside another word as evidence.

Therefore the selector still lacks typed semantic-role evidence.

Scientific diagnosis:
`LEXICAL_LICENSE_IS_NOT_SEMANTIC_LICENSE`

and:
`CORRELATED_LEXICAL_GATE_CANNOT_SAFELY_VALIDATE_LEXICAL_PROPOSAL`

## External blind
NOT RUN.

Reason:
The preregistered pre-blind selector-safety gate already failed.

No blind packet should be dispatched for qualification, because a later favorable quality aggregate cannot override this safety failure.

## Final R63 result
`R63 = CLOSED_FAIL`

Claim:
The fail-closed fallback architecture is directionally useful and successfully repaired the three known R62 failures, but the new license evaluator is not semantically reliable enough for qualification.

R63 does establish:
- exact R58 abstention fallback works mechanically;
- known R62 C06/C08/C11 failure modes can be blocked;
- diversity remains active under abstention.

R63 does NOT establish:
- safe semantic applicability;
- F01 qualification;
- any Production or Candidate promotion.

## Authority consequence
- latest physical authority remains **SYNC-R60**
- active qualified Candidate remains **SYNC-R58 / ADAPTIVE_UL16**
- R62 remains quarantined research evidence
- R63 frozen source becomes additional failed research evidence
- Production remains **ENG:R47 / LEGACY_R53**
- Runtime DB remains **DB59**
- Research DB remains **DB64**
- no 5-Part / 9-Package reseal is required merely for this failed research source, because active runtime authority did not change

## Next research
`R64 = F01 Typed Semantic-Role License Gate`

Required repair direction:
- replace raw substring evidence with typed semantic-role features;
- distinguish physical pressure from dramatic/social pressure;
- require actor/action structure for prior opposing move;
- use token/word boundaries for lexical cues where lexical cues remain;
- preserve exact R58 fallback;
- retain known R62 and R63 failures as regression-only evidence;
- fresh qualification cases must again be created only after R64 source freeze.

Do not begin F04.

Status token:
`R63_CLOSED_FAIL__PREBLIND_SAFETY__LEXICAL_LICENSE_NOT_SEMANTIC_LICENSE__SYNC_R60_UNCHANGED__ACTIVE_SYNC_R58__R64_NEXT`
