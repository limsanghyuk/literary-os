# R67 — F07 Dual-Ledger State Carry Runtime Enforcement Preregistration R1

Date: 2026-09-20
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Sequential identity
- R66 CLOSED PASS — F01 Boundary-Safe Predicate Parser qualified
- R67 CURRENT / PREREGISTERED

## Parent authority
Physical authority:
`SYNC-R64`

Active qualified Candidate:
`R66 F01 Boundary-Safe Predicate Parser / ADAPTIVE_UL16 lineage`

Qualified Candidate runtime SHA256:
`575fd5378c69d282c9b4c39d03e52d4cc436744fa67c792db8515fe91c384e75`

Adaptive source SHA256:
`0558c910896556048bb6acf0e1d4097477c3c31a60d47f16c4bd83e3f6253f1d`

State-carry source SHA256:
`07246dd7db3bf059e838f45b5643ae73a91bf8bc400046b4539f891f644a463d`

Qualified parent/fallback:
`SYNC-R58 / ADAPTIVE_UL16`

Production:
`ENG:R47 / LEGACY_R53`

Runtime DB:
`DB59 frozen`

Research DB:
`DB64 research-only`

## Causal target
Only F07:
`State Carry Runtime Enforcement (상태 이월 런타임 강제)`

R61 status:
`CONTRACT_RESOLVED_RUNTIME_PENDING`

R60 research contract already established:
`TEXT_CANONICAL_STATE_LEDGER (대본 정본 상태 원장)`
must be separated from
`PLANNER_UNREALIZED_OBLIGATION_LEDGER (미실현 기획 의무 원장)`.

R67 implements and tests that contract at runtime.

No F04/F06/F08 intervention.
No DB change.
No Provider prompt/model change.
No Production mutation.

## Observed runtime gap
Current `compile_scene_semantic_commit_packet()` derives:
- relationship/information/social deltas from Scene Contract evidence;
- deferred IDs from scene `residual_after`;
but then enriches deferred rows with architecture-only statement/owners/deltas from the Adaptive Architecture portfolio.

Current `apply_scene_semantic_commit_packet()` stores those enriched rows under canonical runtime state key:
`deferred_obligations`.

Current `adaptive_showrunner_ul16.compile_active_obligations()` consumes that canonical key as if it were a fully carried planning obligation.

This can blur:
`surface-supported open state`
and
`unrealized planner intention`.

## Research question
Can the runtime enforce R60's dual-ledger legality rule while preserving next-episode planning continuity?

## Hypothesis
If canonical carry stores only screenplay/scene-contract-supported state, while unrealized architecture obligations are stored in a separate planner-only ledger with factual access forbidden, then:
1. hidden architecture state cannot silently become canonical fact;
2. open/deferred continuity is preserved;
3. next-episode planning still receives the necessary intended obligation;
4. realized obligations are removed from both ledgers when fulfilled.

## Control
Exact current R66 qualified runtime.

No Control mutation.

## Treatment scope
Permitted changes only in the F07 state-carry path:
- `literary_os_runtime/state_replanning_integrity.py`
- `literary_os_runtime/adaptive_showrunner_ul16.py`
- tests/diagnostics directly required for R67.

Treatment must NOT change:
- R66 F01 selector or boundary-safe semantic parser behavior;
- stage/transaction family selection;
- obligation kind semantics;
- F04 semantic repetition validator;
- F06 scene necessity;
- F08 Provider context;
- DB authority;
- Production path.

## Dual-ledger runtime contract

### A. Canonical State Ledger (정본 상태 원장)
Canonical runtime state may contain only evidence-supported facts/states.

For deferred/open obligations, canonical state may record only evidence-safe fields such as:
- obligation ID;
- OPEN/DEFERRED status;
- source scene IDs;
- evidence mode;
- last touched episode;
- previous canonical open-state record.

It must NOT copy architecture-only:
- statement;
- owners;
- relationship_pair;
- group_refs;
- information_delta;
- relationship_delta;
- social_delta;
- pressure
unless those values are independently realized and committed through Scene Contract semantic deltas.

### B. Planner Unrealized Obligation Ledger (미실현 기획 의무 원장)
Runtime keeps a separate key:
`planner_unrealized_obligations`

This ledger may retain architecture planning metadata needed for future realization.

Every row must explicitly include:
- `factual_access_forbidden = true`
- planner status:
  - `NOT_ESTABLISHED` when architecture-only;
  - `SURFACE_OPEN_BUT_DETAILS_UNESTABLISHED` when a scene confirms the obligation remains open but its detailed architecture metadata is not factual.

### C. Architecture-only deferred obligations
An architecture obligation can appear in the planner-only ledger even when no scene contract realizes or references it.

It must not appear in canonical factual state merely because it exists in architecture.

### D. Scene-supported residual obligations
If a Scene Contract lists an obligation in `residual_after`, canonical state may record that the obligation remains open.

That does not authorize copying the full architecture statement/deltas into canonical state.

### E. Fulfillment
When an obligation is later fulfilled:
- remove it from canonical open/deferred ledger;
- remove it from planner-unrealized ledger.

### F. Downstream planning
`compile_active_obligations()` must consume `planner_unrealized_obligations` for unrealized planning tasks.

It must mark provenance:
`PLANNER_UNREALIZED_OBLIGATION`

It must not treat planner-only metadata as a carried factual state.

Backward-compatibility fallback to legacy `deferred_obligations` is allowed only when the new planner ledger is absent, and must use explicit legacy provenance.

## Frozen deterministic gates

### Gate G1 — Architecture-only contamination
Given an architecture-only deferred obligation absent from Scene Contract residuals:
- canonical `deferred_obligations`: absent;
- canonical information/relationship/social state: unchanged;
- planner ledger: obligation present;
- factual_access_forbidden = true;
- status = NOT_ESTABLISHED.

### Gate G2 — Surface-open / metadata separation
Given a Scene Contract residual ID plus architecture metadata:
- canonical deferred row: open ID + source evidence only;
- architecture statement/deltas absent from canonical row;
- planner ledger retains metadata;
- planner status = SURFACE_OPEN_BUT_DETAILS_UNESTABLISHED.

### Gate G3 — Factual semantic deltas preserved
Scene-supported relationship/information/social deltas still commit identically to Control.

### Gate G4 — Fulfillment cleanup
If an obligation is subsequently fulfilled:
- remove from canonical deferred ledger;
- remove from planner-unrealized ledger.

### Gate G5 — Downstream planner continuity
Adaptive obligation compiler reconstructs future planning obligation from planner-only ledger.
The obligation remains plannable.
Provenance explicitly identifies planner-only source.

### Gate G6 — Hidden-state non-consumption
No planner-only statement/delta may enter:
- `information_state`
- `relationships`
- `social_ecology`
- other canonical factual domains
without Scene Contract evidence.

### Gate G7 — R66 regression
R66 F01 behavior remains unchanged.
Known R62-R65 F01 regression set remains PASS.
R66 fresh primary regression remains PASS.

### Gate G8 — Runtime regression
Whole runtime compile PASS.
Existing state-integrity tests PASS or any changed assertion is explained by the preregistered ledger split only.
No Production or DB mutation.

## Fresh runtime qualification
After Treatment source freeze:
create a fresh deterministic set of at least 12 two-episode state-carry cases spanning:
- architecture-only hidden obligation;
- scene-supported open obligation;
- later fulfillment;
- relationship delta;
- information delta;
- social delta;
- mixed canonical + planner-only state;
- cross-episode planning consumption;
- multiple deferred obligations;
- blocked/preconditioned obligation;
- no-deferred control case;
- rollback/HOLD case.

Inputs must be sealed before Treatment execution.

## Primary qualification
R67 PASS requires:
- all frozen G1-G8 gates PASS;
- fresh runtime set 12/12 PASS;
- hidden-state contamination = 0;
- planner continuity = 12/12 where applicable;
- canonical factual domains contain no architecture-only semantic values;
- exact R66 F01 regression PASS.

No subjective external blind is required for the primary R67 claim because this experiment tests runtime state legality and deterministic carry semantics, not stylistic quality.

## Claim boundary
PASS establishes only:
`F07_DUAL_LEDGER_STATE_CARRY_RUNTIME_ENFORCEMENT = QUALIFIED`

It does NOT establish:
- F04 semantic repetition closure;
- F06 scene necessity closure;
- F08 Provider-context closure;
- full screenplay-surface quality;
- Production promotion.

## Physicalization rule
If R67 implementation changes Candidate runtime and R67 closes PASS:
- create a new 5-Part / 9-Package physical authority;
- preserve exact R66 Candidate as qualified parent/fallback;
- preserve R60 contract evidence and R67 evidence;
- Production remains unchanged unless a separate promotion experiment later authorizes it.

Status token:
`R67_PREREGISTERED__F07_DUAL_LEDGER_RUNTIME_ONLY__PARENT_SYNC_R64__CONTROL_R66_IMMUTABLE__OUTPUTS_0`
