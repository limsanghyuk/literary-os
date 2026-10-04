# UL22-B — Adaptive Temporal / Spatial Ordering Repair Preregistration R1

Date: 2026-10-04
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Trigger / 발동 원인
UL21 Treatment preserved multi-strand, due/deferred/open-touch, trusted-root, F04/F06 and Canonical IR gates but failed the frozen spacetime scheduler with 40-45 infeasible placements per variant.

Responsible boundary:
`ADAPTIVE_SEQUENCE_ORDERING_AND_BUNDLING__TEMPORAL_SPATIAL_CONSTRAINT_BLINDNESS`

Historical connection:
PA7 localized a shared episode-architecture chronology defect. PA8 demonstrated that explicit typed transitions can pass preflight, but that logic was not integrated into the current Adaptive Planner.

Parent research candidate for UL22-B:
**UL22-A semantic-target candidate**, research-only.
Physical Authority remains **SYNC-R77**.

## Research Question / 연구 질문
Can the adaptive upper planner consume caller-frozen time windows and locations when ordering/bundling obligations so that a monotonic feasible episode clock exists, without sacrificing independent causal roots, due/deferred/open-touch semantics, scene necessity, or the UL22-A semantic target contract?

## Allowed Intervention / 허용 개입
Only:
- normalize caller-frozen `time_window` and `location_id` into obligations;
- add deterministic temporal-feasibility ordering and bundle-compatibility checks;
- carry typed time/location into Scene blueprint / Canonical IR;
- add spacetime diagnostics/validators.

Forbidden:
- changing obligation selection/disposition;
- changing F01/F04/F06/F07;
- changing UL18 open-touch semantics;
- changing semantic target values from UL22-A;
- inventing new story events to solve timing;
- deleting obligations merely to make the schedule fit;
- quota padding;
- DB/Provider/Production mutation.

## Frozen Scheduling Contract / 동결 스케줄 계약
Input time window:
`[earliest_start, latest_start]` in target-episode local clock.

Input location:
caller-frozen `location_id`.

A sequence/order is feasible only when its scenes can be scheduled monotonically with:
- scene duration = 2 minutes;
- same-location transition = 0;
- default cross-location transition = 5 minutes;
- fixture-specific special transition cost overrides default;
- no scene start after its obligation latest-start boundary;
- no return to an already-expired time window;
- episode clock remains inside the frozen episode window.

Ordering may reorder independent obligations when no dependency prevents it.
Dependencies override pressure ranking.
Bundling may occur only if the combined obligations admit a feasible local ordering.

## Anti-Collapse / 다중 서사선 보호
Temporal ordering must not:
- collapse independent roots into the budget/main plot;
- merge scenes merely because they share time/location;
- erase independent owners/groups;
- falsify an open/deferred obligation;
- turn time order into one monolithic causal chain.

## Deterministic Pre-Freeze Gates / 동결 전 관문
1. simple monotonic windows -> PASS
2. pressure order that would reverse time -> temporal reorder PASS
3. dependency forcing later-before-earlier impossible window -> FAIL CLOSED
4. same-location transition -> 0-minute transition respected
5. cross-location transition -> default 5-minute transition respected
6. special transition override -> respected
7. two individually feasible obligations but infeasible bundle -> do not bundle
8. irrelevant metadata -> schedule invariant
9. open-touch/deferred disposition unchanged
10. UL22-A semantic targets unchanged
11. F04/F06 outputs unchanged
12. Python compile PASS

## UL21 Requalification Gate / UL21 재검증 관문
Using the frozen UL21 fixture and six variants:
- Treatment internal architecture validation PASS;
- spacetime failures = **0 for all six variants**;
- no due/deferred/open-touch regression;
- no F04 repetition group;
- F06 redundant/mergeable count = 0;
- semantic target loss = 0;
- 16-root representation remains;
- scene count must remain obligation-driven; no padding.

## Claim Boundary / 주장 경계
UL22-B PASS only repairs upper-layer spacetime ordering. It does not itself establish independent literary quality.
After UL22-A + UL22-B PASS, a **new unseen fixture** is required before J01/J02/J03 Architecture-Only Blind.

No physicalization until UL22-B qualification closes and broad regression passes.

Status token:
`UL22B_PREREGISTERED__TEMPORAL_SPATIAL_ORDERING_ONLY__PARENT_SYNC_R77_PLUS_UL22A_RESEARCH_CANDIDATE__OUTPUTS_0`
