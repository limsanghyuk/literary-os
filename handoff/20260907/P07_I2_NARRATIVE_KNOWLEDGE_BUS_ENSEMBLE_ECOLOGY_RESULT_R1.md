# P07-I2 Narrative Knowledge Bus / Ensemble Ecology Main-Path Pretest — Result R1
Date: 2026-09-07
Status: PASS__PREFORMAL_DEVELOPMENT
Formal count delta: 0
R140 attempt delta: 0

## Starting authority
CURRENT_PHYSICAL_AUTHORITY__P07_I1_CLOSED_NARRATIVE_LOOP_INTEGRATION_R1
DB59 SHA256: a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9

## Preregistration
handoff/20260907/P07_I2_NARRATIVE_KNOWLEDGE_BUS_ENSEMBLE_ECOLOGY_PRETEST_PREREG_R1.md
Commit: 4ced851ba3bbcc00353ed42f1a6e5482e42afe72

## Implemented main-path change
P07-I2 adds:
- PlanningQuestionRouter
- DB59 NarrativeKnowledgeBus
- bounded NarrativeArchitecturePacket
- Character / Relationship / Thread multi-view evidence
- evidence-derived SocialEcologyEvidenceView with UNKNOWN/fail-close policy
- ENSEMBLE_ECOLOGY_PLAN between EPISODE_PLAN and SEQUENCE_PLAN
- NAP + Ensemble binding into SEQUENCE_PLAN and SCENE_PLAN provider inputs
- I2 integrated transaction receipt binding NAP, ensemble plan, selector, repair routing and state carry

## Fresh DB59 CASE-01 result
Source-safe boundary: target EP06, available source through EP05 only.
Knowledge snapshot: 8 character states / 6 relationship states / 26 thread-state rows / 12 prior THICK sequences.
Selected NAP evidence: 22 items.
Functional RFV2 decision: USE_RETRIEVAL.
Derived Social Ecology: PASS with 2 evidence clusters; canonical_truth=false.
Provider call order:
SERIES_PLAN -> EPISODE_ALLOCATION -> EPISODE_PLAN -> ENSEMBLE_ECOLOGY_PLAN -> SEQUENCE_PLAN -> SCENE_PLAN.
SEQUENCE_PLAN and SCENE_PLAN inputs both contain narrative_architecture_packet and ensemble_ecology_plan.
Selector: COMMIT.
Injected SCENE_SEQUENCE_ID_MISMATCH -> REPLAN_PARENT / SEQUENCE_PLAN.
State carry: committed PASS.
Live provider evidence eligible: false.
Python literary prose generated: false.

## Causal adoption gates
- selected Character-state mutation -> NAP literary payload changed; Ensemble/Sequence input changed: PASS
- selected Relationship-state mutation -> NAP literary payload and Sequence input changed: PASS
- selected Thread/Payoff mutation -> NAP literary payload and Sequence input changed: PASS
- irrelevant unselected raw CharacterArc sidecar mutation -> selected IDs unchanged and literary payload unchanged: PASS
- insufficient ecology evidence -> INSUFFICIENT_EVIDENCE; no invented second group; canonical_truth=false: PASS

## Broadcast-scale semantic development probe
The same I2 main path produced 12 semantic sequences / 60 scene contracts, satisfying the development semantic-scale target. Semantic contracts all ACCEPT; selector COMMIT; state carry committed.
Scope boundary: SEMANTIC_BROADCAST_SCALE_ONLY. This pretest does not claim a 35k-45k-character final screenplay surface and does not substitute for Live provider craft evidence.

## Regression
Exact working I2 overlay nonhistorical suite: 190/190 PASS.
Preserved historical PRE-P07-PRE09 failure remains outside the nonhistorical current gate and is not edited to weaken history.

## Evidence hashes
- narrative_knowledge_bus.py 065a058043850df357f5bfc1fa158d54eeddee34c6a9edcb4f4ec0d020725354
- semantic_orchestration.py 07171a10b9e47f0aacc2a1e0535da7526ca98b69acca33afdc70c23e6b474240
- integrated_authoring_loop.py 6ed8eef365bf34b312d4ee2bbe62abb76bd2ddb80075d792d1e7b83ab6f4341e
- test_p07_i2_narrative_knowledge_bus.py 0396877e45c9a557eadfbcb72f913fde952084ccaffccf7b71e7a243519310aa
- primary result 142a73d4196c747f3f9489fc4fee72d9a637e6e3e320fb445a3291d3c449ca6f
- causal adoption result 278edd2fc264c2e9bed841f2aa277aac8f49bd10d5b6ebdafe0585b8c1bf4031
- broadcast semantic probe 58d60153d8320426942275009317bfa2fe4667d4d635ef063a67daf4d15914aa

## Verdict
PASS__NARRATIVE_ARCHITECTURE_DB_CONSUMPTION_MAIN_PATH_MECHANICALLY_CONNECTED

## Claim boundary / next unit
P07-I2 proves mechanical causal adoption and broadcast-scale semantic planning, not craft superiority. Next unit after physical reseal is P07-I3 Broadcast Surface Development Probe: original synthetic drama, provider-backed or explicit in-session LLM surrogate, 45-60 scenes and 35k-45k Korean characters, followed by craft/continuity/ecology/thread diagnostics and bidirectional re-lowering. RFV3/CP1/R-F/R-G/R140 remain blocked.
