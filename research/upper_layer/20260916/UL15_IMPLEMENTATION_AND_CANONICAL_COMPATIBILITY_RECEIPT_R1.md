# UL-15 Prototype Implementation & Canonical Compatibility Receipt R1

Date: 2026-09-16
Status: PROTOTYPE_PASS__CANONICAL_IR_COMPATIBILITY_PASS__MAIN_PATH_INTEGRATION_PENDING
Preregistration: `research/upper_layer/20260916/UL15_ADAPTIVE_MULTI_OBLIGATION_PLANNER_PREREGISTRATION_R1.md`

## What was implemented
A standalone research prototype was implemented outside the physical authority packages:
- `adaptive_multi_obligation_planner_r2.py`
- `adaptive_to_canonical_adapter_r1.py`
- unit tests for broadcast depth, due/defer integrity, obligation reconstruction, and variable scene allocation.

No R53 package bytes were modified.

## Prototype architecture
The prototype performs:
1. normalization of EVENT / THREAD / RELATIONSHIP / CHARACTER / INFORMATION / SOCIAL / PAYOFF obligations;
2. explicit due-now vs deferred separation;
3. dependency/pressure-aware adaptive sequence bundling;
4. multi-owner and multi-kind weaving when structurally related;
5. preservation of deferred debt as sequence pressure or terminal deferred ledger without false settlement;
6. variable scene allocation based on obligation burden rather than a 2/3-scene hard rule;
7. broadcast depth guard using the DB64 61-work source-grounded distribution as a prior;
8. scene-level downstream consumer references and physicalization/state-delta requirements;
9. reverse reconstruction of due coverage and deferred preservation;
10. compatibility lowering into the existing R53 Canonical Typed IR V2.

## Synthetic rich-ensemble test packet
The frozen prototype test used:
- 2 event obligations;
- 3 thread obligations;
- 3 relationship obligations;
- 2 character obligations;
- 2 information obligations;
- 1 social obligation;
- 1 payoff obligation;
- six distinct owners;
- two explicitly deferred obligations.

This packet was intentionally multi-strand; it is a structural test, not a literary-quality evaluation.

## Results
Adaptive architecture:
- sequence count: 9;
- scene count: 52;
- per-sequence scene count range: 4..10;
- weaving fraction: 0.556;
- deferred count: 2;
- due obligation reconstruction: PASS;
- deferred preservation: PASS;
- lost due obligations: 0;
- lost deferred obligations: 0;
- false fulfillment of deferred obligations: 0;
- uniform sequence-scene grid: NO.

Unit tests:
- broadcast structural depth: PASS;
- due obligation reconstruction: PASS;
- deferred-not-falsely-fulfilled: PASS;
- total: 3/3 PASS.

## Canonical IR compatibility test
The adaptive result was lowered with `adaptive_to_canonical_adapter_r1.py` into the current R53 canonical representation and passed the actual vendored R53 `canonical_ir_v2` compiler/validator.

Result:
- SeriesIR: 1
- EpisodeIR: 1
- SequenceIR: 9
- SceneIR: 52
- total nodes: 63
- canonical validation errors: 0
- decision: PASS
- graph hash: `428248f282605389a819075948ded25f798e703295d415ad3a2c2be52020f07e`

This proves that the upper planning spine can be replaced without discarding the existing Canonical Typed IR V2 interface.

## Important non-claims
This prototype does NOT prove:
- human-level episode planning quality;
- external literary quality;
- OpenAI Provider qualification;
- production readiness;
- DB64 A2 completion;
- physical Candidate package integration;
- regression closure of the entire current runtime.

The adapter currently uses generic semantic anchor wording for compatibility testing. The next implementation must bind each scene anchor to real story-state obligations rather than generic placeholders before any literary-quality experiment.

## Defect-resolution status
Resolved at prototype level:
- fixed 2/3-scene lowering dependency removed;
- due/defer false-settlement problem explicitly guarded;
- single-owner/single-kind sequence requirement removed;
- variable sequence/scene depth supported;
- reverse reconstruction added;
- canonical downstream compatibility demonstrated.

Still pending:
- integration into the real Candidate Main Path;
- source-state obligation compiler from Narrative State Kernel / Series architecture;
- DB64 distributional-prior consumer with target-leakage guard;
- semantic ScenePlan contract binding real state deltas and downstream consumers;
- integrated regression suite;
- clean physical successor build;
- external blind and live Provider tests.

## Next engineering step
Create UL-16 Main-Path Integration Layer that replaces only the current Episode/Sequence/Scene planning functions while preserving:
- source-safe ingestion;
- Narrative State Kernel;
- Series architecture / Episode allocation where valid;
- Canonical Typed IR V2;
- provider-backed renderer/judge interfaces;
- state commit/carry and integrity controls.

Status token:
`UL15__PROTOTYPE_3_OF_3_PASS__DUE_DEFER_INTEGRITY_PASS__VARIABLE_9_SEQUENCE_52_SCENE_ARCHITECTURE__CANONICAL_IR_63_NODE_ZERO_ERROR_PASS__MAIN_PATH_INTEGRATION_PENDING`