# R76-R2A-R2 Causal-Spine Sequence Cohesion Repair — Preregistration R1

Date: 2026-09-23
Status: `PREREGISTERED__OUTPUTS_0`

## Parent
- R76 Stage-A frozen episode
- R76-R2A-R1 clean-room result: zero-related pair 0, but sequence_count 8 -> FAIL
- R76 Provider-Analog Cleanroom run: 35859943285
- No screenplay surface generated.

## Diagnosis
R2A-R1 removed pairwise-unrelated members, but five 4-obligation bundles remained.
Those bundles were admitted primarily by owner overlap and contained no internal dependency edge.
Therefore the remaining compression is an owner-collision aggregation problem, not lack of unique material.

## Frozen Treatment Rule
1. Preserve R2A-R1 all-pairs cohesion gate: a new obligation may join a bundle only when relation >=2 to EVERY current member.
2. Compute internal causal-spine edges only from explicit `depends_on` relations between members already in the same candidate bundle.
3. If the candidate bundle has ZERO internal dependency edges, maximum bundle size = 3.
4. If the candidate bundle has >=1 internal dependency edge, maximum bundle size = 4.
5. Never split or clone merely to reach a numeric sequence target.
6. No obligation may be omitted, cloned, or rewritten.
7. Deferred obligations remain outside due-sequence bundling.

## Gates
- C1 full due-obligation coverage exactly once.
- C2 cloned/omitted obligations = 0.
- C3 zero-related pair count = 0.
- C4 owner-only four-obligation bundle count = 0.
- C5 sequence_count >=9 (R76 prereg scale gate).
- C6 sequence_count <=14 (DB64-R128 73-work empirical P90 guard; diagnostic guard, not a target).
- C7 R2B semantic-role repair is not changed by this experiment.

## Claim Boundary
Engineering repair qualification at Sequence Architecture layer only.
No screenplay-quality, Production, Operational Level-3, DB64 adoption, or R140 claim.
