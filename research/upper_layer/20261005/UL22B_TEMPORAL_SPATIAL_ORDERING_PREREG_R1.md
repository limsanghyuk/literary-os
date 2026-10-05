# UL22-B — Temporal/Spatial Ordering Repair Preregistration R1

Date: 2026-10-05
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Trigger / 발동 원인
UL21 closed before blind dispatch because the current Adaptive planner produced 40-45 infeasible scene placements per variant under a preregistered monotonic spacetime scheduler.

Responsible boundary:
`ADAPTIVE_SEQUENCE_ORDERING_AND_BUNDLING__TEMPORAL_SPATIAL_CONSTRAINT_BLINDNESS`

The same defect class had previously appeared in PA7 shared Episode Architecture chronology. PA8 demonstrated that explicit transition typing can detect/prevent this class, but those constraints were not consumed by the current Adaptive planner.

## Parent / 부모
Physical Authority: **SYNC-R77**
Active Runtime: **UL20_F04_TRUSTED_ROOT_SUCCESSOR_RUNTIME_R1**
UL22-A research candidate is qualified but not physicalized.
UL22-B implementation must be applied on top of the frozen UL22-A source.

## Intervention boundary / 개입 경계
Allowed changes only in `adaptive_showrunner_ul16.py`:
1. preserve caller-frozen `location_id` and `time_window` as typed obligation fields;
2. preserve an optional caller-frozen `spacetime_context` containing episode window and transition minutes;
3. when at least one scheduled obligation has a valid time window, make dependency ordering use earliest feasible deadline/start as the primary ready-set ordering key, with pressure/id only as deterministic tie-breaks;
4. in typed-spacetime mode, only weave into the current adjacent bundle when relationship/dependency/group relatedness already qualifies **and** the bundle remains temporally compatible;
5. propagate typed location/time window into Scene graph and EpisodeResult/Canonical IR lowering;
6. add a deterministic upstream spacetime validator using the frozen scheduler contract.

Forbidden:
- changing due/deferred/open-touch selection or closure;
- changing transaction-stage selection;
- changing scene-count rules;
- changing visible-action generation;
- changing F04/F06;
- changing trusted-root validation;
- changing Semantic Target logic from UL22-A;
- using target/future episode source;
- DB/Provider/Production mutation.

## Historical compatibility / 역사 호환
If no valid caller-frozen time window is present:
- `_dependency_order` must use the exact historical pressure/id behavior;
- bundle search/selection must use the exact historical all-bundles behavior;
- scene location/time lowering must remain the historical functional-locus/VARIABLE representation.

Thus all untyped historical R66-R69/UL18/UL20 fixtures remain behaviorally identical by construction.

## Typed scheduler contract / 형식화 스케줄러 계약
Input `spacetime_context` may contain:
- `episode_window=[HH:MM,HH:MM]`
- `default_cross_location_transition_minutes`
- `special_transition_minutes={"A>B":minutes}`

Each typed scene inherits its source obligation's `location_id` and `time_window`.

Validation:
1. generated scene order is immutable for the audit;
2. each scene duration = 2 minutes;
3. same location transition = 0;
4. different location transition = special value if present, otherwise default;
5. earliest start = max(previous end + transition, window start);
6. if earliest start > window end -> FAIL;
7. if final scene end exceeds episode window -> FAIL.

## Pre-freeze deterministic cases / 동결 전 결정론 사례
At minimum:
1. UNTYPED_SENTINEL -> parent/candidate ordering/bundling bit-identical.
2. SIMPLE_REVERSAL -> 18:00 item may not precede a 16:30 deadline item when dependencies do not require it.
3. DEPENDENCY_OVERRIDES_TIME -> prerequisite remains before dependent.
4. IMPOSSIBLE_DEPENDENCY -> validator FAIL, never silently reorder across dependency.
5. ADJACENT_OVERLAP_WEAVE -> related overlapping obligations may weave.
6. NONOVERLAP_NO_WEAVE -> related but non-overlapping windows may not create a bundle that causes backward time.
7. LOCATION_TRANSITION -> special/default transition cost enforced.
8. UL22A_SEMANTIC_TARGET_SENTINEL -> target fields unchanged.

## Qualification gates / 자격 관문
Before source freeze:
- deterministic 8/8;
- Python compile 45/45;
- untyped historical path source-equivalence or output-equivalence PASS;
- UL22-A semantic-target 16/16 preserved.

After source freeze, seal a fresh primary suite before execution.

PASS requires:
- fresh primary 16/16;
- FP0/FN0 for feasible/infeasible classification;
- no due/deferred/open-touch regression;
- F04/F06/trusted-root regression PASS;
- no scene-count/stage/action drift except order/bundle changes causally required by typed spacetime;
- UL21-derived dense schedule probe reaches 0 spacetime failures without obligation cloning;
- no single-causal-spine collapse introduced.

## Claim boundary / 주장 경계
UL22-B PASS establishes typed spacetime ordering/validation at the architecture level only.
It does not establish independent literary quality.
After UL22-B PASS, UL22-A+UL22-B must be integrated into a successor research runtime, then a **new unseen** Architecture Requalification must be run before any physical promotion or Provider screenplay.

Status token:
`UL22B_PREREGISTERED__TEMPORAL_SPATIAL_ORDERING_AND_VALIDATION_ONLY__NO_OUTPUTS`
