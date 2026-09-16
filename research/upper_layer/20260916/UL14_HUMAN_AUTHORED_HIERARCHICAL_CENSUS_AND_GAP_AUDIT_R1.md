# UL-14 Human-Authored Hierarchical Architecture Census & Candidate Gap Audit R1

Date: 2026-09-16
Project: Literary OS Development
Status: CLOSED__GAP_CONFIRMED__UPPER_LAYER_QUALIFICATION_REVOKED_PENDING_REPAIR

## Purpose
Re-audit the assumption that the Candidate upper planning layer was sufficiently mature, using the latest sealed research-support database and the actual R53 Candidate/Main-Path source rather than ChatGPT conceptual analog generation.

## Evidence boundary
- Physical production/runtime authority remains SYNC-R53 / ENG:R47 / DB59.
- Research-support source: DB64 R108 Final Sealed + 61-work Learning Bundle.
- DB64 A2 remains PENDING; DB64 data completeness is not Candidate engine qualification.
- Target-episode authored material is never authorized as a forward-generation donor. The corpus is used for distributional/metrological priors and structural audits only.
- Previous same-chat/mock/analog screenplay generation is not evidence that the Candidate Engine executed its intended algorithm.

## DB64 physical verification used for this audit
- Reconstructed DB64 bytes: 313,702,945.
- Reconstructed DB64 SHA256: `19f3c446a73408045d02d4d99e168251dca42da3bfa00abaff1d8f9159d7ea46`.
- ZIP integrity: PASS.
- 61-work 9-contract audit status: `PASS_61_61_A2_PENDING`.
- Source-grounded 61-work census: 1,160 episodes, 10,853 extracted sequences, 73,639 scene cards.

## Human-authored structural census
Using the 1,160 episode plans whose sequence references and scene-budget hints are source-grounded:
- planned sequence count: mean 9.67, median 9, P10 6, P90 14, min 2, max 29;
- episode scene budget: mean 63.49, median 62, P10 46, P90 81.1, min 6, max 182;
- scene budget per sequence: mean 6.57, median 7, P10 3, P90 10, min 1, max 25.

These are distributional observations, not fixed quotas. Broadcast mode may use a minimum-depth guard, but generation must remain obligation-driven and variable.

## Existing EpisodePlan compression finding
`EpisodeSynopsisPlan.v0.3-r1` is a reverse-engineered planning artifact, not direct evidence of how human writers consciously plan. Its compression behavior is nevertheless diagnostic:
- episode_axis count distribution: 1 axis 178 episodes; 2 axes 269; 3 axes 685; 4 axes 25; 5 axes 3;
- 390/1,160 episodes (33.6%) allocate at least 75% of sequences to one axis;
- 178/1,160 episodes (15.3%) allocate 100% of sequences to one axis;
- 1,006/1,160 episodes record one or more deferred obligations, but sequence allocation uses `DEFERRED` as owner in 0 episodes.

Therefore the current planning artifact can record debt while still failing to structurally preserve debt pressure in the sequence architecture.

## R53 Main-Path implementation audit
Direct source inspection found the following hard flattening mechanisms in `literary_os_runtime/episode_scene_spine.py`:
1. `infer_rwork_sequence_count_prior()` defaults to a supported range of 3..12 and computes a normal Candidate prior capped at 9 when no caller-frozen reference prior is supplied.
2. `allocate_plot_lines()` assigns each sequence one dominant line among a very small set: MAIN / RELATION / SUBPLOT_SOCIAL.
3. `plan_thick_sequences()` assigns one `owner` and one `counterparty` per sequence and defaults ownership largely by primary/secondary/opposition rotation.
4. Every sequence receives the same base obligation set ACTION / INFO / RELATION / TURN / EXIT, with SOCIAL added only to selected functions.
5. `realize_boundary_driven_scenes()` hard-codes ordinary sequences to 2 scenes and SOCIAL-heavy sequences to 3 scenes.
6. Relationship obligations are not generative inputs to sequence formation; `_relationship_obligation_floor()` only checks whether owner/counterparty pairs happen to appear and can require caller-provided repair overrides.

This is a structural cause of thin and repetitive episode architecture, not merely a prose-renderer problem.

## DB64 consumption audit
Search of the R53 runtime source found:
- no runtime reference to `DB64`;
- no runtime reference to `research_support`;
- no consumption of DB64 `episode_plan/current` as a planning prior;
- no consumption of DB64 `thick_sequence` or `runtime_scene_projection` as learned structural priors;
- `prior_episode_plan` appears only in the entity-life-state guard path and does not drive Candidate episode/sequence/scene architecture.

Search of the SYNC-R53 Candidate upper overlay likewise found no DB64/research-support consumer. It validates final weaving/scene-plan receipts but does not generate the hierarchy from DB64-learned priors.

## Root cause
The project has a rich analytical corpus and multiple upper-layer research concepts, but the active Candidate Main Path still performs a strong lossy projection:

`rich narrative state -> small ownership model -> few plot-line labels -> one owner/counterparty per sequence -> uniform base obligations -> 2/3-scene deterministic lowering`

The upper-layer quality problem therefore has two independent components:
- CONTRACT LOSS: the planning schema compresses multiple simultaneous narrative obligations into too few axes/owners/lines;
- CONSUMER LOSS: the Candidate Main Path does not consume the latest DB64 research-support priors and does not implement the later multi-obligation/weaving research as its actual generation algorithm.

## Claim correction
The earlier statement that the upper planning layer was sufficiently closed/stable is revoked.

New claim boundary:
`UPPER_LAYER_GENERATIVE_QUALITY = NOT_YET_QUALIFIED`

UL-13 surface tests remain useful research evidence, but they cannot establish whole-showrunner quality when the Episode/Sequence/Scene planner feeding the surface is structurally underpowered.

## Required repair direction
Replace the lossy upper planning spine with an Adaptive Multi-Obligation Showrunner Planner that:
- preserves simultaneous EVENT / THREAD / RELATIONSHIP / CHARACTER / INFORMATION / SOCIAL / PAYOFF obligations;
- distinguishes due-now fulfillment from deferred-pressure preservation;
- permits multiple owners and multiple obligation kinds per sequence;
- lets sequence count and per-sequence scene count emerge from obligation burden;
- uses the DB64 human-authored corpus only as distributional priors/metrology, never as target-content leakage;
- performs reverse reconstruction from Scene -> Sequence -> Episode obligations;
- replans when obligation loss, owner concentration, uniform-grid behavior, or false debt settlement is detected;
- lowers to the existing Canonical Typed IR so the validated downstream renderer/state layers can remain in place.

## Authority impact
No Production, DB, Formal, or physical authority change.

Status token:
`UL14__HUMAN_AUTHORED_CENSUS_COMPLETE__MAIN_PATH_FLATTENING_CONFIRMED__DB64_CONSUMPTION_GAP_CONFIRMED__UPPER_LAYER_QUALIFICATION_REVOKED_PENDING_UL15_REPAIR`