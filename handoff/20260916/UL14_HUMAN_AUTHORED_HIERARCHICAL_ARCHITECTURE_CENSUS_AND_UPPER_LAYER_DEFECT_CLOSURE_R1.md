# UL-14 HUMAN-AUTHORED HIERARCHICAL ARCHITECTURE CENSUS & UPPER-LAYER DEFECT CLOSURE R1

Date: 2026-09-16
Project: Literary OS Development
Classification: RESEARCH EVIDENCE / DEFECT CLOSURE / CLAIM CORRECTION
Authority change: NONE

## 1. DECISION

The prior statement that the upper planning layer was sufficiently closed/stable is WITHDRAWN.

Current status:

`UPPER_LAYER_GENERATIVE_QUALITY = NOT_QUALIFIED`

The evidence supports a narrower conclusion: the database and several validators contain rich narrative state, but the generative Episode -> Sequence -> Scene planning path does not yet consume that richness without severe structural compression and template bias.

Previous same-chat / virtual screenplay generations are reclassified as `VIRTUAL_ANALOG` unless an actual Candidate runtime path and receipt prove otherwise. They are not evidence of `CANDIDATE_RUNTIME` or `LIVE_PROVIDER` execution.

## 2. FROZEN RESEARCH INPUT

Primary research-support database:
`DB64_POST_R108_PRINCESS_MAN_NATURALNESS_ENDPOINT_NORMALIZED_R53_HARDENED_RESEARCH_SUPPORT_CANDIDATE_R1_20260912_FINAL_SEALED`

Reassembled SHA256:
`19f3c446a73408045d02d4d99e168251dca42da3bfa00abaff1d8f9159d7ea46`

61-work completeness bundle status:
`PASS_61_61_A2_PENDING`

A2 is still pending a separate preregistered engine experiment. Therefore this census does not adopt DB64 as Production DB and does not claim engine-quality validation.

Production DB remains DB59 frozen.

## 3. HUMAN-AUTHORED ARCHITECTURE CENSUS

Primary sealed cohort: 61 works / 1,160 episodes / 11,213 thick sequences / 73,639 runtime scenes.

Observed episode topology:
- sequences per episode: mean 9.666, median 9, p10 6, p90 14, range 2..29;
- exactly 10 sequences: about 10.3% of episodes only;
- scenes per episode: mean 63.482, median 62, p10 46, p90 about 81, range 6..182;
- sequence length: mean about 6.57 scenes, median 7, p10 3, p90 10, range 1..25;
- episodes with every sequence exactly equal length: under 1%.

The counts are descriptive priors only. They are forbidden as generation quotas.

The corpus shows multiple concurrent narrative obligations rather than one dominant linear axis. Earlier census work also found median episode-level relationship changes about 5, character-state changes about 6, and plant/payoff candidates about 5. Runtime scene projection carries nonempty relationship state in the large majority of scenes, although consumer-ready social-ecology summary/evidence coverage is uneven and must not be overclaimed as 61/61.

## 4. CURRENT EPISODE-PLAN COMPRESSION DEFECT

Across the 1,160 current episode plans:
- 1 axis: 178 episodes;
- 2 axes: 269;
- 3 axes: 685;
- 4 axes: 25;
- 5 axes: 3.

A single owner controls >=75% of sequence allocation in about 33.6% of episodes. A single owner controls 100% in about 15.3%.

Declared deferred obligations exist widely, but `DEFERRED` sequence ownership is effectively not consumed by the current sequence allocation path.

This is a representational bottleneck: a rich episode state is compressed into a few axes and then into single-owner sequence allocation.

## 5. SCHEMA AUTHORITY DRIFT

The current authority pointer names `EpisodeSynopsisPlan.v0.3-r1.schema.json`, whose episode-axis cardinality is constrained to 2..3 and whose sequence allocation uses a single owner string.

However, among 1,124 records self-identifying as `EpisodeSynopsisPlan.v0.3-r1`, full JSON Schema validation found only 461 valid and 663 invalid. The failures include axis-cardinality violations, missing/changed planning-context fields, statement-policy drift, open-debt structural drift, newer fields rejected as additionalProperties, and turn-class enum drift.

Therefore the current directory mixes schema generations under one apparent authority. This must not be repaired by silently loosening v0.3-r1. A versioned vNext contract is required.

## 6. HISTORICAL RUNTIME TEMPLATE DEFECT — DIRECT CAUSE

The reconstructed canonical Narrative Engine Master contains historical R134 runtime paths that directly encode the monotonous topology observed in prior broadcast tests.

Examples confirmed in code:
- `detailed_episode_synopsis.py`: `expected_sequences=10` and exact-count enforcement;
- `broadcast_sequence_expansion.py`: every sequence expands through the same five slots: `ENTRY_ACTION`, `PRESSURE_CONTACT`, `COUNTERACTION`, `CONSEQUENCE`, `EXIT_TURN`;
- `scene_architecture.py`: the 50-scene path explicitly validates 10 sequences x 5 scenes;
- another `episode_scene_spine.py` path remains heavily templated, including fixed small plot-line grammar and ordinary/social sequence scene-count rules;
- `episode_architecture.py` uses a small deterministic sequence-role grammar;
- earlier P07-I4K4 prospective treatment/control both preserved 10 sequences / 50 scenes.

Conclusion: the monotonous 10x5 result was not merely weak prompting. It was materially caused by historical runtime topology constraints.

## 7. CANDIDATE PHYSICALIZATION GAP

The small SYNC-R53 post-R53 Candidate upper-layer overlay primarily contains validators/gates such as cutoff-safe projection, weaving validation, terminal-closure validation, and integrated upper-layer harness logic.

It can validate supplied artifacts, but it is not yet a complete generative Episode -> Sequence -> Scene authoring path.

P07-I4H Recovery R3 is principally renderer/intervention wiring over an already-existing scene plan. It does not repair the upstream episode/sequence/scene architecture generator.

Therefore metadata saying that upper-layer capabilities are adopted must be distinguished from executable main-path generation that actually consumes them.

## 8. ROOT-CAUSE MODEL

The defect is a combination of five independent causes:

1. `FIXED_TOPOLOGY_BIAS`: historical 10-sequence / five-slot / 50-scene enforcement.
2. `REPRESENTATION_COMPRESSION`: rich DB state reduced to 1..3 dominant axes and single-owner sequence allocation.
3. `GENERATOR_VALIDATOR_GAP`: recent Candidate research added sophisticated validation concepts without an equally complete generative main path.
4. `SCHEMA_AUTHORITY_DRIFT`: current records and declared schema authority do not describe one coherent contract generation.
5. `EVIDENCE_CLASS_CONFUSION`: same-chat virtual analog outputs were too easily read as evidence about Candidate runtime quality.

These are engineering/research defects, not evidence that DB64 is corrupt.

## 9. CORRECTIVE ACTIONS SEALED BY UL-14

Effective immediately for upper-layer research:

- fixed sequence/scene quotas are prohibited as planner requirements;
- 9-10 sequences / 45-50 scenes remain observational/reference priors only;
- exact 10x5 topology may occur only as an emergent result and requires narrative justification if a template detector flags it;
- Sequence may consume multiple obligations and have multiple owners;
- Scene must be represented as a state-changing transaction with downstream consumers, not a slot label;
- relationship, information, social/resource, event, character, and payoff obligations must survive into the planning graph when relevant;
- `SOURCE_REVERSE_ENGINEERED`, `VIRTUAL_ANALOG`, `CANDIDATE_RUNTIME`, and `LIVE_PROVIDER` are separate evidence classes;
- surface generation is blocked until the architecture gate passes;
- if a scene/sequence is infeasible, replan the lowest responsible ancestor rather than patching prose around a broken plan;
- no Production/Candidate promotion follows from this census.

## 10. NEXT CONTRACT

UL-15 introduces an Adaptive Multi-Obligation Showrunner Planner research contract with three new versioned planning artifacts:

- `EpisodeObligationGraphPlan.v0.1`
- `SequenceWeavePlan.v0.1`
- `SceneTransactionPlan.v0.1`

A0 structural representability has been executed as an engineering precheck only; it is not A2, not a generation-quality result, and not a live Provider result.

## 11. AUTHORITY BOUNDARY

Unchanged:
- Physical baseline: SYNC-R53;
- Production: ENG:R47;
- Candidate Base: P07-I4H Recovery R3;
- Production DB: DB59 frozen;
- formal scored total: 137; latest R138; R140 0/0/0;
- Operational Level-3: SUSPENDED;
- Level 4: NOT_STARTED.

## 12. STATUS TOKEN

`UL14_CLOSED__UPPER_LAYER_STABILITY_CLAIM_WITHDRAWN__FIXED_TOPOLOGY_AND_REPRESENTATION_COMPRESSION_CONFIRMED__GENERATOR_VALIDATOR_GAP_CONFIRMED__SCHEMA_DRIFT_CONFIRMED__EVIDENCE_CLASSES_REPAIRED__UPPER_LAYER_GENERATIVE_QUALITY_NOT_QUALIFIED__UL15_NEXT`
