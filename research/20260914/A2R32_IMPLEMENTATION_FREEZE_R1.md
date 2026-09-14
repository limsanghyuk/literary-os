# A2R32 IMPLEMENTATION FREEZE R1

Date: 2026-09-14
Experiment: `P07-DATA-A2R32-UTILITY-CONTROLLED-MINIMAL-NOVELTY-PLANNING-QUALIFICATION`
Maturity state: `PRE_LEVEL_3 / LEVEL_3_ENTRY_QUALIFICATION / E2`

## Status

`IMPLEMENTATION_SOURCE_FROZEN__SCIENTIFIC_OUTPUTS_0__RUNTIME_HOLD`

The pre-output utility-control implementation source has been written and frozen at:

`research/20260914/a2r32_utility_control_r1.py`

Git commit custody seal for source creation:

`8315e0c94ea45f3bdd840eaacfc90ead48ab0036`

Because the container/Python execution transport remains unavailable, SHA256 of the source bytes is **PENDING RUNTIME RECOVERY**. The Git commit is the current immutable pre-output custody seal. A SHA256 seal must be computed and recorded before any retrieval/planning output is accepted.

## Frozen intervention implemented

The source implements only the A2R32 intervention already preregistered:

1. Protected DB59 baseline is not retrieved or mutated by this module.
2. At most one optional advisory may be used.
3. Non-target-axis advisory → `ABSTAIN__NON_TARGET_AXIS`.
4. Case-relevance veto for CHARACTER_STATE / RELATIONSHIP_PRESSURE / CAUSAL_ESCALATION atoms.
5. PHYSICALIZATION affordance veto, including explicit guards against unsupported `FALL` and `BLOOD` actions.
6. PLANT_PAYOFF lifecycle coherence veto requiring long-horizon affordance + lifecycle atom + persistent obligation/object relation.
7. ENSEMBLE_OWNERSHIP requires explicit >=3 actor groups and realizes at most one ownership atom.
8. Minimal novelty budget = maximum 2 atoms per used advisory/plan.
9. Deterministic tie-break order is fixed in code before outputs.
10. Fixed realization-slot mapping:
    - CHARACTER_STATE → S5
    - RELATIONSHIP_PRESSURE → S2
    - CAUSAL_ESCALATION → S4
    - ENSEMBLE_OWNERSHIP → S4/S6
    - PHYSICALIZATION → S3
    - PLANT_PAYOFF → S1/S6
11. Mechanical invariant validation is included; it does not judge literary quality.

## Explicit non-changes

This implementation does **not** change:
- A2R10 retrieval scorer;
- DB59 or DB64 bytes;
- compatibility overlay doctrine;
- structured functional abstraction schema;
- protected DB59 baseline;
- A2R26 optional-advisory + abstention doctrine;
- blind mapping procedure;
- quality rubric;
- final `>=7W / >=10 nonloss / <=2L` gate.

## Output boundary

At this freeze:
- retrieval outputs = 0
- plan outputs = 0
- eligibility result = 0
- mapping = none
- blind packet = none
- blind judgment = none
- result = none

No PASS/FAIL may be claimed from this freeze.

## Runtime recovery requirements before outputs

All must occur in order:

1. minimal runtime command succeeds;
2. A2R32 fresh-pool bytes SHA256-sealed;
3. A2R32 preregistration bytes SHA256-sealed;
4. this implementation source SHA256-sealed;
5. A2R10 scorer / structured abstraction / canonical A2R26 implementation bytes reverified;
6. recovery bundle created for those immutable inputs;
7. only then retrieval/planning outputs may begin.

## Physical-package rule

SYNC-R34 remains the current physical 5-Part / 9-Package authority. This implementation is newer than the R34 physical package and is currently preserved in the developer hub only because the execution/container layer cannot safely reseal transport packages.

Before proceeding beyond the next meaningful scientific gate, the maturity correction + A2R32 preregistration + implementation freeze must be physically incorporated into the next 5-Part / 9-Package reseal (expected next sync number: R35, subject to successful physical audit).

Status token:

`A2R32_IMPLEMENTATION_FROZEN__OUTPUTS_0__RUNTIME_HOLD__PHYSICAL_RESEAL_PENDING`
