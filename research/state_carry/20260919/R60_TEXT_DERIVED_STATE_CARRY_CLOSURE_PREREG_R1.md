# R60 — Text-Derived State Carry Closure (대본 기반 상태 이월 폐쇄) Preregistration R1

Date: 2026-09-19
Status: `PREREGISTERED__INPUTS_FROZEN__OUTPUTS_0`

## 1. Sequential identity
Parent research:
`R59 = CLOSED_HOLD__TEXT_STATE_RECOVERABILITY_INCOMPLETE`

Current research:
`R60 = Text-Derived State Carry Closure (대본 기반 상태 이월 폐쇄)`

No R60 sub-number is a separate research transaction.

## 2. Scientific problem
R59 established:
- all 6/6 P06 due-now states are recoverable from the final screenplay;
- 2/3 episode deferred states are recoverable;
- DEFER-3 (anonymous-source identity -> newsroom internal-log leak) is not recovered from the screenplay and is an architecture-only / hidden-state dependency.

Therefore direct:
`Architecture State -> State Carry`
is unsafe.

## 3. Hypothesis
A dual-ledger State Carry contract can close the loop safely:

A. `TEXT_CANONICAL_STATE_LEDGER`
- contains only state supported by actual screenplay evidence;
- may include explicit unresolved/unknown states;
- may include pending choices;
- never imports an architecture-only fact.

B. `PLANNER_UNREALIZED_OBLIGATION_LEDGER`
- may preserve an intended but unrealized architecture obligation;
- is explicitly non-factual;
- cannot be queried by downstream consumers as if the event/state has already occurred;
- can only be used as a future planning task requiring later surface realization.

## 4. Frozen inputs
Completed P06 screenplay:
- SHA256: `88e74a280be7c657eb241309144475be4fcc702f1052646f31b8fe608e25d653`
- 11 sequences / 55 scenes

Sealed R59 blind reconstruction:
- evaluator: J01
- SHA256: `d7543baf4488112b577bf0ddf4ec35066bcfa1fd72a8f29bb624cfe3a381f2cb`

R59 result:
`research/provider/20260919/R59_P06_OUTPUT_ONLY_REVERSE_RECONSTRUCTION_RESULT_R1.md`

Architecture audit reference only:
- P06 Candidate=A architecture SHA256:
  `01f43f27211b9e9957a14ae48b6ffdc2ef8e5375a497ab7c2c9b77a7918ab493`

The architecture may be used to detect hidden-state contamination. It may not be used as the factual source for the canonical state ledger.

## 5. Allowed canonical-state classes
- `COMMIT_RESOLVED`: a resolution/state change visibly established in screenplay.
- `COMMIT_OPEN`: a continuing unresolved state visibly established in screenplay.
- `COMMIT_OPEN_UNKNOWN`: the screenplay establishes that a relevant value/identity/outcome remains unknown.
- `COMMIT_PENDING_CHOICE`: the screenplay ends with an explicit pending decision/action.
- `COMMIT_RELATIONSHIP_STATE`: relationship status visibly changed.
- `COMMIT_INFORMATION_STATE`: who knows/does not know what is text-supported.
- `COMMIT_SOCIAL_INSTITUTIONAL_STATE`: authority/rule/group state visibly changed.

## 6. Prohibited canonical-state classes
The text canonical ledger must never contain as factual state:
- `ARCHITECTURE_ONLY_STATE`
- `HIDDEN_STATE_DEPENDENCE`
- inferred future event not shown in screenplay
- unverified allegation converted into fact
- planned closure not realized on surface

Such material is:
`WITHHOLD_FROM_CANONICAL_STATE`.

If strategically useful, an unrealized architecture obligation may be stored only in:
`PLANNER_UNREALIZED_OBLIGATION_LEDGER`
with:
`factual_status = NOT_ESTABLISHED`.

## 7. R60 required outputs
1. Text Canonical State Ledger JSON
2. Planner Unrealized Obligation Ledger JSON
3. commit/withhold audit
4. consumer-safety audit
5. final R60 PASS/HOLD result

Every canonical entry requires:
- state_id
- state class
- state text
- evidence scenes
- confidence
- evidence mode
- next-episode consumer role
- source = screenplay/R59 reconstruction

Every unrealized planner obligation requires:
- obligation_id
- intended future planning task
- factual_status = NOT_ESTABLISHED
- canonical_state_access = FORBIDDEN
- required realization condition before future commit

## 8. Primary gate
R60 PASS only if all conditions hold:

1. every canonical committed state has screenplay evidence;
2. all six recovered due-now states are carried without importing unsupported extra facts;
3. unresolved uncertainty remains unresolved rather than falsely closed;
4. DEFER-1 is carried as an open/unverified modification suspicion, not confirmed manipulation;
5. DEFER-2 is carried as the text-supported joint-verification transition;
6. DEFER-3 is absent from factual canonical state;
7. DEFER-3, if retained for planning continuity, is stored only as `UNREALIZED / NOT_ESTABLISHED`;
8. a downstream next-episode consumer can distinguish canonical fact from planner-only obligation without ambiguity.

If any architecture-only state enters factual canonical state:
`R60 = HOLD__HIDDEN_STATE_CONTAMINATION`.

If required screenplay-supported next-episode state is lost:
`R60 = HOLD__TEXT_STATE_LOSS`.

## 9. Claim boundary
R60 validates the state contract and ledger construction.

R60 does NOT by itself prove:
- engine runtime implementation;
- Candidate code consumption;
- regression PASS;
- new physical authority;
- Production promotion.

If R60 PASS later requires engine code changes, those changes belong to a later sequential intervention research number and must follow:
`IMPLEMENT -> REGRESSION -> C1/C2 BINDING -> 9-PACKAGE RESEAL -> NEW PHYSICAL AUTHORITY`.

## 10. Database rule
R60 is screenplay-state validation and does not use DB64 as an answer key.

After R60 closes, later generative-planning experiments should restore the qualified:
`DB64 research fuel + DB59 protected baseline/fallback + structured functional abstraction + utility arbitration + abstention + load/consumption receipts`.

## 11. Authority impact
No authority change.

`CURRENT_PHYSICAL_AUTHORITY = SYNC-R58`
`CANDIDATE = ADAPTIVE_UL16`
`PRODUCTION = ENG:R47 / LEGACY_R53`
`RUNTIME_DB_AUTHORITY = DB59 frozen`

Status token:
`R60_PREREGISTERED__DUAL_LEDGER_STATE_CARRY__TEXT_CANONICAL_VS_UNREALIZED_PLANNER_OBLIGATION__OUTPUTS_0__SYNC_R58_CURRENT`
