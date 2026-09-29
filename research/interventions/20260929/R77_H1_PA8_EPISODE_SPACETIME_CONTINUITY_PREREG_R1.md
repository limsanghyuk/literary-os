# R77-H1 PA8 — Episode Spacetime Continuity / Responsible-Ancestor Repair Preregistration R1

Date: 2026-09-29
Status: PREREGISTERED__PA8_A_IMPLEMENTATION_NOT_STARTED__OUTPUTS_0

## Sequential identity
- PA6: CLOSED_FAIL__FOCUS_EFFECT_SIZE_GATE
- PA7: CLOSED_FAIL__ABSOLUTE_CRITICAL_VIOLATION_GATE__PAIRED_PASS__FOCUS_PASS_5_OF_6__RECOVERABILITY_PASS
- PA8: CURRENT / PREREGISTERED

## Parent authority
- Physical Authority: SYNC-R74
- Active Runtime: exact R69
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Operational Level-3: SUSPENDED__REQUALIFICATION_REQUIRED
- Formal latest scored: R138
- Formal R140: NOT_STARTED

## Responsible ancestor from PA7
COMMON_EPISODE_ARCHITECTURE_TEMPORAL_SCHEDULING_AND_VALIDATION_LAYER

PA7 established that the residual screenplay-surface intervention itself had a strong positive signal:
- mapped Treatment whole preference: 3/3
- mapped Treatment surface preference: 3/3
- Focus Gate: PASS 5/6
- Recoverability: PASS

PA7 nevertheless failed the frozen Absolute Gate because a shared chronology defect was confirmed on Treatment by 3/3 judges and existed in both arms.

The canonical example is:
- SC22 rear-gate window: 23:20-00:05
- SC30: first delivery truck may arrive 10 minutes before 00:05
- surface SC30 occurs around 00:38 while treating that earlier arrival as future pressure.

## Existing-system boundary
The repository already contains:
- TemporalCoherenceEngine: episode-to-episode state/reveal/residue continuity
- TemporalCIM: episode-indexed relationship evolution
- SpatialConstraintGate: action-level co-location checks

These do not currently qualify the missing layer:
within-episode absolute scene time + event ETA/window + movement time + cross-scene entity/container/location continuity.

PA8 therefore adds a research-only Episode Spacetime Continuity Contract/Gate first. It must not mutate exact R69 until deterministic qualification closes PASS.

## Research question
Can a deterministic within-episode spacetime validator detect causal/continuity impossibilities before screenplay surface realization while permitting explicitly typed non-linear narration such as FLASHBACK and PARALLEL?

## PA8-A treatment scope
Research-only files under:
research/interventions/20260929/pa8_spacetime_r1/

No active runtime, Production, DB, C1, C2 or physical package bytes may change during PA8-A.

## Frozen violation classes
1. SCENE_CLOCK_REVERSAL
   - LINEAR_REALTIME scene begins before the prior forward scene ends.

2. FUTURE_EVENT_IN_PAST
   - an event framed as future has event_time < current scene start.

3. AVAILABILITY_WINDOW_VIOLATION
   - a resource/location/route is used outside its frozen valid window.

4. IMPOSSIBLE_TRAVEL
   - an entity changes location faster than the frozen minimum travel time without a declared teleport/nonlinear exception.

5. ENTITY_MULTI_LOCATION
   - one entity is asserted at multiple physical locations in the same canonical scene state.

6. CONTAINER_TRANSITION_BREAK
   - an entity changes vehicle/container membership without an explicit board/exit/transfer transition.

7. LOCATION_TRANSITION_BREAK
   - an entity changes location with no explicit movement/transfer evidence when the transition is marked evidence-required.

8. CROSS_MIDNIGHT_NORMALIZATION_ERROR
   - clock times crossing midnight are normalized incorrectly, causing a false future/past relation or reverse ordering.

## Timeline modes
- LINEAR_REALTIME: participates in the canonical forward clock and state ledger.
- FLASHBACK: may use earlier time; does not advance or overwrite canonical forward state.
- PARALLEL: may overlap the canonical clock; does not by itself violate monotonicity.
- MONTAGE: must declare a bounded time window; canonical forward time advances only to its declared end.

The validator must not convert legitimate non-linear narration into a failure merely because displayed clock time is earlier.

## PA8-A frozen deterministic set
Exactly 16 cases:
- 8 positive violation cases, one for each frozen violation class;
- 8 negative-control cases.

Negative controls must include:
- valid monotonic linear progression;
- future event exactly at/after current scene time;
- valid use inside availability window;
- location change with sufficient travel time;
- explicit FLASHBACK;
- explicit PARALLEL overlap;
- explicit board/exit/transfer transition;
- valid cross-midnight progression.

The PA7 SC30 chronology pattern must be represented among the 8 positives and must be detected without reading PA7 judge verdicts at runtime.

## PA8-A gates
PASS requires all:
- positive detection: 8/8
- negative-control correct non-detection: 8/8
- FP: 0
- FN: 0
- deterministic rerun produces identical result payload apart from run metadata
- no active runtime / Production / DB mutation
- research-only code boundary audit PASS

Any miss or false alarm => PA8-A CLOSED_FAIL or HOLD according to whether execution is valid.

## No-gaming rules
- no case replacement after first validator execution;
- no threshold/rule edits after first output;
- no special-case string matching for PA7 scene numbers, titles, character names or literal prose;
- no judge-result lookup by the validator;
- no automatic story invention/repair by the validator;
- violations return FAIL/REPLAN_REQUIRED evidence only.

## PA8-B planned integration after PA8-A PASS
Only after PA8-A closes PASS:
- bind ESCC/ESCG between Episode Architecture and Scene Contract in a research candidate;
- demonstrate value change -> consumer receives -> provider input changes -> downstream scheduling changes;
- negative control: irrelevant spacetime field change must not alter provider input;
- preserve PA7 residual surface policy on both future arms.

## PA8-C/D/E planned qualification
After PA8-B causal propagation PASS:
- create a fresh synthetic episode unrelated to PA7 and H1 real works;
- freeze shared semantics before surfaces;
- Control and Treatment both use the PA7-qualified residual surface policy;
- only Treatment receives the new spacetime contract/gate;
- both surfaces >=40,000 chars, no upper cap, no quota padding;
- external 3-Judge blind with mapping revealed only after 3/3 first schema-valid outputs are hash-sealed;
- preserve PA7 Absolute / Paired / Focus / Recoverability gates;
- add a separate continuity gate; do not dilute literary gates.

## Claim boundary
PA8-A PASS qualifies only the deterministic research predicate.
It does not change exact R69, Production, DB59, Operational Level-3, Formal count/R140, H1 primary output count or Human-target custody.

## Physicalization rule
Research-only PA8-A creates no physical-package change.

If a later PA8 phase modifies the candidate runtime and closes its preregistered regression/binding gates:
RESEARCH_FINDING -> IMPLEMENTED_IN_CANDIDATE -> REGRESSION_PASS -> C1/C2_BINDING_PASS -> 9_PACKAGE_RESEAL -> SHA/CRC/CUSTODY_PASS -> NEW_PHYSICAL_AUTHORITY

At that point a successor 5-Part / 9-Package set must be created and delivered. Until then SYNC-R74 remains physical authority.
