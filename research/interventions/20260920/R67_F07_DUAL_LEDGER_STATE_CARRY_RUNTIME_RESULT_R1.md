# R67 F07 Dual-Ledger State Carry Runtime Enforcement — Final Result R1

Date: 2026-09-20
Status: `CLOSED_PASS__DUAL_LEDGER_RUNTIME_ENFORCEMENT_QUALIFIED`

## Authority at experiment close
- Physical authority before post-R67 reseal: **SYNC-R64**
- Active qualified Candidate before R67 close: **R66 F01 Boundary-Safe Predicate Parser**
- Qualified parent/fallback: **exact SYNC-R58**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**

## Frozen chain
Preregistration commit:
`f386f5f775416bfc093dcf36b343e06772f94cb9`

Implementation freeze commit:
`826487d54e2f7cbedfb6040c49775bbf64ffd9a0`

Fresh-input seal commit:
`c39d71a425ad2bc2de68dce4f13fa794d5ecc32c`

Frozen Treatment runtime SHA256:
`9ab625122d7b572bf781ffa8062271f085cfde2d757e42dd79a18b977d9a72b8`

Frozen Treatment adaptive source SHA256:
`6574449a4a0b0520db5993b1f1abe532709b19aa9a5c7dc706df24b8c1fc6b91`

Frozen Treatment state-carry source SHA256:
`ce38885171d0f318aeb2142ec16d119814be7fb736ebc361166007b4d2eea087`

## What R67 changed
R67 enforces the R60 dual-ledger contract at runtime.

### Canonical State Ledger (정본 상태 원장)
`deferred_obligations` now carries only evidence-safe open/deferred state:
- obligation ID;
- OPEN/DEFERRED status;
- Scene Contract evidence;
- last touched episode;
- prior canonical open-state record.

Architecture-only statement/owners/deltas/pressure are not copied into canonical deferred state.

### Planner Unrealized Obligation Ledger (미실현 기획 의무 원장)
New runtime key:
`planner_unrealized_obligations`

It retains future planning metadata with:
`factual_access_forbidden = true`

Planner states distinguish:
- `NOT_ESTABLISHED`
- `SURFACE_OPEN_BUT_DETAILS_UNESTABLISHED`
- legacy migration provenance where applicable.

### Hash separation
Canonical factual hash excludes the planner-only ledger.
Planner ledger has its own independent hash.

Changing only planner intention cannot change canonical factual identity.

### Downstream consumption
Adaptive Showrunner consumes planner-only unrealized obligations with provenance:
`PLANNER_UNREALIZED_OBLIGATION`

It no longer requires rich architecture metadata to be stored in canonical deferred state.

## Pre-freeze gates
- G1-G6 deterministic legality gates: PASS
- factual relationship/information/social commit equal to Control: PASS
- R66 fresh F01 transaction decisions bit-identical: PASS
- runtime compile: 45/45 PASS
- code-boundary audit: PASS

## Fresh qualification
Fresh 12-case two-episode runtime set was created only after Treatment source freeze.

Fresh input SHA256:
`414d099308e3606acff8483c899eb4cd7f4b5783e2c98bc2b01ba20629d1cfcb`

### Treatment
- PASS: **12/12**
- hidden-state contamination: **0**
- planner continuity: **11/11 applicable**
- canonical factual domains contain no architecture-only semantic values
- HOLD/no-mutation path: PASS
- later fulfillment cleanup: PASS
- legacy migration split: PASS

Treatment result SHA256:
`d213fcb33b8a390206e158cd7d539cc4aa174e9e31f9ed3f2dafe05680ba51e3`

### Control
Exact R66 Control under the same R67 legality contract:
- PASS: **2/12**
- FAIL: **10/12**

Primary Control failure classes:
- architecture-only unrealized obligations were not preserved for downstream planning;
- surface-open residual obligations stored architecture metadata inside canonical deferred state;
- hidden architecture semantics could appear in canonical open-state rows;
- legacy rich deferred rows remained unsplit.

Control result SHA256:
`5f788dc0b6297ffad88afe261a2de7ed7d40e31822298dccfdd0e1d637ba6dd7`

Primary qualification summary SHA256:
`1906b9cc806615a14ad1729649b98c3939cf5a6987f64eb498b4b722d67234d1`

Final evidence ZIP SHA256:
`2081b12fba92c612852472b19ee27f56257127acdba1bbf11b51dbcd1df326e9`

## Final verdict
All preregistered primary gates pass.

`R67 = CLOSED PASS`

Qualified claim:
`F07_DUAL_LEDGER_STATE_CARRY_RUNTIME_ENFORCEMENT = QUALIFIED`

## Scientific meaning
R60 established the legal state doctrine at research-contract level.

R67 demonstrates that the Candidate runtime now enforces it:
`Actual Scene Evidence (실제 장면 근거)`
→ `Canonical Factual Carry (정본 사실 상태 이월)`

and separately:
`Unrealized Architecture Obligation (미실현 구조 의무)`
→ `Planner-Only Ledger (기획 전용 원장)`
→ `Future Planning Consumption (향후 기획 소비)`
→ only after surface realization
→ `Canonical Commit (정본 커밋)`.

This closes the previously identified F07 runtime-enforcement gap.

## Claim boundary
R67 PASS does NOT establish:
- F04 Semantic Repetition Validator closure;
- F06 Scene Necessity closure;
- F08 Provider Context closure;
- full screenplay-surface quality;
- Production promotion.

## Authority consequence
R67 Treatment is eligible to become the next qualified Candidate runtime through a separate audited physicalization step.

Production remains:
`ENG:R47 / LEGACY_R53`

Status token:
`R67_CLOSED_PASS__F07_DUAL_LEDGER_RUNTIME_QUALIFIED__12_OF_12_FRESH__ZERO_HIDDEN_STATE_CONTAMINATION__PLANNER_CONTINUITY_11_OF_11__PRODUCTION_UNCHANGED__PHYSICALIZATION_PENDING`
