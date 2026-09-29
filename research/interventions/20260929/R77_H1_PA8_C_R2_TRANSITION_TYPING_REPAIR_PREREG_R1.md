# R77-H1 PA8-C R2 — Transition Typing Repair Preregistration R1

Date: 2026-09-29
Status: PREREGISTERED__R1_PREFLIGHT_FAIL_PRESERVED__R2_NOT_BUILT__SURFACE_OUTPUTS_0

## Parent failure
PA8-C R1 architecture preflight:
FAIL__UNTYPED_ZERO_GAP_LOCATION_JUMP

Observed:
- scene count: 50
- sequence count: 9
- episode clock: 01:48-03:32
- resource/future-time checks: no reported violations
- zero-gap untyped location jumps: 35

No surface outputs exist. Human target remains unopened.

## Repair target
Only explicit participant movement typing.

## Allowed changes
R2 may add only:
- a frozen internal travel-time matrix;
- per-scene participant transition records;
- transition mode:
  - BETWEEN_SCENES
  - AT_SCENE_OPEN
- travel_min;
- arrival_offset_min;
- transition evidence metadata.

## Frozen rule
For a participant whose current physical location differs from the last canonical location:
1. if elapsed off-scene gap >= travel_min, type BETWEEN_SCENES;
2. otherwise the transition may be typed AT_SCENE_OPEN only when travel_min <= current scene duration;
3. AT_SCENE_OPEN means the participant is not available for destination interaction until arrival_offset_min >= travel_min;
4. if neither condition is possible, R2 build/preflight must FAIL; do not change scene semantics or stretch clocks post hoc.

## Prohibited changes
R2 must not change:
- premise
- cast/voice contracts
- hard-state constraints
- due/deferred sets
- sequence count/functions
- scene count/order
- scene function
- must_change
- scene clock
- scene duration
- location_id
- resource window
- future event/deadline
- frozen blind sample
- arm policy.

## Semantic invariance gate
A semantic projection of R1 and R2 must be byte-identical.

## R2 preflight gates
PASS requires:
- 50 scenes / 9 sequences;
- 01:48-03:32 boundary;
- scene clocks monotonic;
- resource-window violations 0;
- future-event-in-past violations 0;
- every location change has a valid transition;
- impossible transition 0;
- untyped zero-gap jump 0;
- R1/R2 semantic projection hash identical;
- surface outputs remain 0;
- Human target remains unopened.

## Claim boundary
R2 PASS qualifies only the fresh architecture for PA8-D surface generation.
It does not modify exact R69 or create a new Physical Authority.
