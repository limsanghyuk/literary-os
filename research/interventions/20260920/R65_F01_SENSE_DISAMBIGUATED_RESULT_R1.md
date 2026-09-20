# R65 F01 Sense-Disambiguated Semantic Predicate Gate — Result R1

Date: 2026-09-20
Status: `CLOSED_FAIL__PREBLIND_SELECTOR_SAFETY__UNBOUNDED_SUBSTRING_COLLISION`

## Authority at experiment start
- Physical authority: SYNC-R62
- Active qualified Candidate: SYNC-R58 / ADAPTIVE_UL16
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64 research-only

## Frozen prerequisites
Preregistration commit:
`08f2f148d7b9fbd635594508ae5349fbe712bb04`

Implementation freeze commit:
`da2ff1e74f5b89c2ff7e82538caea5eec3dad553`

Frozen R65 Treatment source SHA256:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

F01-only diff SHA256:
`5a1bb5e3cd33b2e74083d858d2ed89b6d39d53d7ccdf240ee6fce50ed938c190`

Fresh input seal commit:
`f2cc0d57f6635f2a702d1d2d037653faf344fcbf`

Fresh primary JSON SHA256:
`44e0377dc088b39af8b3a209625c940a429e42e336ceac266577e5295053b0e4`

## Pre-primary regression
Known R62/R63/R64 failures:
- 7/7 bad families blocked
- 7/7 exact R58 fallback
- 7/7 architecture validation PASS

R58B:
- 12 sequences / 66 scenes
- PASS

R63 fresh regression:
- 12/12 PASS

R64 fresh regression:
- 12/12 PASS

Whole runtime compile:
- 45/45 PASS

## Fresh primary mechanical result
Control exact R58:
- 12/12 architecture validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate concrete-action cases 0
- distinct precursor families 4
- output SHA256:
  `05f546336a3428a9936f31fc13cd62707fba98dbf73cc3966cd8c6f767053928`

Treatment frozen R65:
- 12/12 architecture validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked preservation PASS
- duplicate concrete-action cases 0
- ACCEPT 33 / ABSTAIN 14
- distinct precursor families 7
- output SHA256:
  `2afa490c480b31419a8cda73df4d0d4b33785ef5f837577a60f14d4718551b52`

The intervention transmitted and did not collapse to always-abstain.

## Pre-blind selector-safety failure
Selector audit SHA256:
`e5ecc97a3551064a7323b02607ea636497fc4b2b35b571c93a6bcedd76eaac82`

### R65C06_AUCTION_LEDGER / R65C06-E1
Frozen statement:
`창고 인수 목록에서 한 상자가 빠져 현장 확인을 시작한다`

Frozen visible action:
`경매담당이 상자 번호를 목록과 대조하며 빈 칸을 표시한다`

Treatment selected:
`PRESSURE_ESCALATION`

Reason:
`LICENSED_SENSE_RESOLVED_PRESSURE_PREDICATE`

Assigned sense:
`DEADLINE_PRESSURE`

Actual defect:
The helper inherited unbounded substring phrase matching. The deadline cue `시한` was found inside the unrelated word `표시한다`.

Classification:
`UNBOUNDED_SUBSTRING_COLLISION__SIHAN_INSIDE_PYOSIHANDA`

This input contains no deadline/time-pressure transaction.

## Root cause
R65 fixed the known `표면 마감` / deadline ambiguity and physical-pressure ambiguity, but its sense layer still called a substring matcher for some lexical atoms.

Therefore:
`TARGETED_SENSE_DISAMBIGUATION_IS_NOT_BOUNDARY_SAFE_SEMANTIC_PARSING`

Historical progression:
- R63: lexical license is not semantic license;
- R64: field provenance is not sense disambiguation;
- R65: targeted sense rules still fail if lexical atoms are not token/morpheme bounded.

## External blind
NOT RUN.

Reason:
the preregistered selector-safety gate failed before blind dispatch.
A favorable blind result cannot override this failure.

## Final
`R65 = CLOSED_FAIL`

R65 establishes:
- known R62/R63/R64 failures can be blocked;
- exact R58 fallback remains mechanically sound;
- compound-first sense rules can correct known polysemy;
- useful diversification remains active.

R65 does NOT establish safe F01 semantic applicability.

## Evidence
R65 evidence ZIP SHA256:
`90e138cdcb31fe9d930b65cd8f9ea3cf6d6ea5642786aa4879a01751da2cf5f1`

## Authority consequence
R65 Treatment never becomes active authority.
Active qualified Candidate remains exact SYNC-R58 / ADAPTIVE_UL16.
Production remains ENG:R47 / LEGACY_R53.
Runtime DB remains DB59.
R65 source/output are failed research evidence only.

## Next research
`R66 = F01 Boundary-Safe Predicate Parser Gate`

Required repair:
- eliminate unbounded substring matching from all positive semantic license evidence;
- tokenize/morpheme-bound lexical atoms;
- compound-first word-sense resolution;
- predicate/argument structure for positive licenses;
- lexical atoms may support but never independently establish causal roles;
- exact R58 fail-closed fallback;
- R62/R63/R64/R65 failures regression-only;
- fresh R66 cases only after R66 source freeze.

R66 is NOT STARTED.

Status token:
`R65_CLOSED_FAIL__MECHANICAL_12_OF_12_BOTH_ARMS__SUBSTRING_COLLISION_SIHAN_IN_PYOSIHANDA__BLIND_NOT_RUN__ACTIVE_SYNC_R58_UNCHANGED__R66_NEXT_NOT_STARTED`
