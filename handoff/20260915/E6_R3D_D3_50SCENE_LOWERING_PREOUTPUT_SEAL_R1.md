# E6-R3D D3 50-Scene Contract Lowering — Preoutput Seal R1

Date: 2026-09-15
Parent: E6-R3D D2 PASS
Classification: DEVELOPMENT / PREFORMAL / PLANNING-ONLY

## Status before output
- D2 architecture: SEALED / PASS
- 50-scene contracts: 0
- screenplay prose: 0
- State Commit: 0
- external judgments: 0

## Frozen scene budget
The D2 sequence budgets are frozen:
- SQ01 = 4
- SQ02 = 4
- SQ03 = 5
- SQ04 = 5
- SQ05 = 5
- SQ06 = 6
- SQ07 = 5
- SQ08 = 6
- SQ09 = 5
- SQ10 = 5
Total = exactly 50 scenes.

No sequence budget may change after first D3 scene-contract output.

## Required contract fields per scene
Every scene must contain:
- scene_id
- sequence_id
- primary_axis
- dramatic_owner
- location
- scene_function
- conflict_pressure
- beats[]
- information_action
- relationship_action
- thread_action
- entry_state
- exit_state
- agency_holder
- cross_axis_refs[]

No finished dialogue or stage-direction prose is allowed in D3.

## Hierarchy preservation gates
1. 50/50 scenes assigned to one and only one parent sequence.
2. Per-sequence counts exactly match frozen budgets.
3. No orphan scene.
4. No H0-H3 story axis disappears.
5. Every sequence's D2 `value_shift` is realized by at least one scene transition and preserved at sequence exit.
6. All seven frozen cross-axis collision/convergence points remain represented.
7. At least 8 scenes are primarily owned by Nari-family/governance supporting axes before considering cross-axis co-ownership.
8. At least 6 scenes have decisive agency held by a supporting character rather than Se-won.
9. Relationship operations are not merely decorative: at least 6 scenes alter a later scene's available action/choice.
10. Thread operations are not merely labels: at least 6 scenes open, escalate, constrain, partially pay or carry a thread.
11. At least 5 scenes are low-dialogue candidates by function (observation, physical choice, document action, silence, or visual consequence), to prevent fixed speech topology later.
12. At least 5 scenes are multi-party ensemble candidates.
13. At least 3 scenes use remote/phone/digital communication and must declare both endpoint contexts in later surface realization.
14. Surface prose bytes = 0.

## R3-C inheritance for later surface only
The later screenplay must inherit `SHOW_ONLY_DIRECTION_BOUNDARY`.
D3 contracts may specify physical/subtext targets conceptually, but may not prewrite authorial explanatory stage direction.

## Failure rule
Any missing budget, orphan, lost story axis, lost cross-axis point, or systematic return to one-parent-task decomposition => `HOLD__D3_SCENE_LOWERING_FAIL`.
Do not repair thresholds after output. A failed D3 output remains immutable.

## Successor rule
Only D3 PASS permits a fresh >=35,000-character screenplay surface from these exact sealed 50 scene contracts.
