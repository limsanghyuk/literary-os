# R77-H1 PA8-B — Spacetime Causal Integration Preregistration R1

Date: 2026-09-29
Status: PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0

## Parent evidence
PA8-A:
PASS__TP8__TN8__FP0__FN0__DETERMINISTIC

Canonical result:
research/interventions/20260929/pa8_spacetime_r1/PA8_A_DETERMINISTIC_RESULT_R1.json

## Purpose
Test whether qualified Episode Spacetime Continuity data is actually consumed between Episode Architecture and Scene Contract/provider input, rather than merely stored or logged.

## Adoption standard
A positive causal path requires:
spacetime value changes
-> integration consumer receives the changed value
-> compiled Scene Contract/provider input changes
-> deterministic downstream schedule/replan behavior changes
-> receipt exposes the propagation.

A negative control requires:
an irrelevant/non-consumed metadata value changes
-> compiled provider input remains byte-identical
-> downstream schedule remains byte-identical.

## Scope
Research-only under:
research/interventions/20260929/pa8_spacetime_r1/

No modification to:
- exact R69 active runtime
- Production
- DB59
- C1/C2
- H1 frozen Human targets
- Formal count/R140.

## Frozen semantics
The fixture freezes:
- four existing scene semantic functions;
- scene order;
- actors/entities;
- no new scene/action/decision/outcome may be invented by the scheduler.

Only scheduling metadata may change.

## Frozen integration fields
Consumed:
- earliest_start
- latest_start
- duration_min
- predecessor
- min_gap_after_predecessor
- resource availability window
- event deadline/future-time requirement

Ignored:
- research_note
- display_label
- diagnostic_comment

## Deterministic scheduling rule
For each LINEAR_REALTIME scene in frozen order:
1. start >= earliest_start;
2. start >= predecessor_end + min_gap_after_predecessor;
3. start must permit the whole scene inside every required availability window;
4. event deadlines/future requirements must remain temporally possible;
5. if no feasible start <= latest_start, return REPLAN_REQUIRED;
6. do not create, delete, reorder or semantically rewrite a scene.

## Frozen causal cases
C1 RELEVANT_EARLIEST_START_SHIFT:
Changing a consumed earliest_start must change the compiled provider input and scheduled start.

C2 RELEVANT_TRAVEL_GAP_SHIFT:
Changing min_gap_after_predecessor must change compiled provider input and scheduled start.

C3 RELEVANT_AVAILABILITY_CONFLICT:
Changing a consumed resource window so no feasible slot remains must change provider input and downstream status to REPLAN_REQUIRED.

C4 PA7_LIKE_DEADLINE_CONFLICT:
A scene scheduled after a declared future event/deadline must fail closed rather than silently treating the event as future.

N1 IRRELEVANT_METADATA_SHIFT:
Changing only research_note/display_label/diagnostic_comment must leave provider input hash and schedule hash byte-identical.

N2 SEMANTIC_INVARIANCE:
All positive and negative variants preserve the frozen scene semantic payload byte-identically.

## Gates
PASS requires:
- C1 positive propagation PASS
- C2 positive propagation PASS
- C3 fail-closed propagation PASS
- C4 PA7-like conflict fail-closed PASS
- N1 irrelevant-field invariance PASS
- N2 semantic invariance PASS
- deterministic rerun identity PASS
- active runtime/Production/DB effect NONE.

Any gate failure closes PA8-B FAIL/HOLD before 40K generation.

## Claim boundary
PASS establishes only research-candidate causal consumption of the spacetime contract.
It does not yet establish screenplay quality, full runtime adoption, real-provider equivalence, Production promotion, Level-3, or Formal R140.

## Next if PASS
PA8-C: freeze a fresh synthetic episode architecture with explicit ESCC fields before either arm surface exists.
Control and Treatment will share semantics and the PA7 residual surface policy; only Treatment receives PA8 spacetime enforcement.
