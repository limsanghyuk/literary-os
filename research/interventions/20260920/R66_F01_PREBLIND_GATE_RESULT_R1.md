# R66 F01 Boundary-Safe Predicate Parser — Pre-Blind Gate Result R1

Date: 2026-09-20
Status: `PREBLIND_PASS__WAITING_EXTERNAL_BLIND_3_JUDGES`

## Authority
- Physical authority: SYNC-R63
- Active qualified Candidate: exact SYNC-R58 / ADAPTIVE_UL16
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64 research-only
- R66 Treatment is research-only and is NOT active authority.

## Frozen prerequisites
Preregistration commit:
`e52ac3fdf06fe45670e9a728cac6fb91c98727e6`

Implementation freeze commit:
`f2a207a86700eb94bfd63a55a7e81d7fc2e26c5f`

Frozen R66 Treatment source SHA256:
`0558c910896556048bb6acf0e1d4097477c3c31a60d47f16c4bd83e3f6253f1d`

F01-only diff SHA256:
`8bec59183b7a408aae19cb598f2b828a1989bf13c3f94263c04b8a0e3f787fc5`

Fresh-input seal commit:
`8fcc6bf73c1173e40a9f249dd25777e697646e40`

Fresh primary JSON SHA256:
`9ba77865f1fd4f9f9ec91a23456686c026269f3ec5ed62c3490f2e43065bc5a7`

## Pre-primary regression
Known R62-R65 failures:
- 8/8 bad families blocked
- 8/8 exact R58 fallback
- 8/8 validation PASS

Known-failure regression SHA256:
`06317995e6d1af3c54154b62e4f36fdb006d7ea277cfc956a73b449fab36a8cf`

R58B:
PASS, 12 sequences / 66 scenes.

R63 fresh regression:
12/12 PASS.

R64 fresh regression:
12/12 PASS.

R65 fresh regression:
12/12 PASS.

Whole runtime compile:
45/45 PASS.

Code boundary:
PASS.

## Fresh primary mechanical result
Control exact R58:
- 12/12 architecture validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate concrete-action cases 0
- distinct precursor families 4
- output SHA256:
  `ced989d20216533d8c5764b3bfe130ead884201ce4b5ef1205e5a1b2047de4d7`

Treatment frozen R66:
- 12/12 architecture validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate concrete-action cases 0
- ACCEPT 29 / ABSTAIN 18
- distinct precursor families 8
- output SHA256:
  `dace87d7f8b17124c8be8d9ec4134de88db878517c2978f2366453879f5e8b1b`

The intervention transmitted and did not collapse to always-abstain.

## Selector-safety result
Independent selector-safety audit:
PASS.

Accepted decisions reviewed:
29

Violations:
0

Collision traps explicitly checked:
- `실시한다` must not supply `시한` -> PASS
- `표기한다` must not supply `기한` -> PASS
- hydraulic/physical pressure must not become dramatic pressure -> PASS

Selector-safety audit SHA256:
`11ecce8741a73bc6bc48b9ae170409b6878dd38b74a83cda2b218b0b54c1fcda`

## External blind
READY / NOT YET RUN.

Three independent judge packets are sealed under the separate execution protocol.

No scientific PASS/FAIL qualification may be declared until J01/J02/J03 valid judgments are collected and mapped.

## Authority consequence
No authority promotion.
Physical authority remains SYNC-R63.
Active qualified Candidate remains exact SYNC-R58.
No 5-Part / 9-Package reseal is required while R66 remains open.

Status token:
`R66_PREBLIND_PASS__MECHANICAL_12_OF_12_BOTH_ARMS__SELECTOR_SAFETY_PASS__EXTERNAL_BLIND_PENDING__ACTIVE_SYNC_R58_UNCHANGED`
