# UL-15 Adaptive Multi-Obligation Planner Preregistration R1

Date: 2026-09-16
Status: PREREGISTERED__IMPLEMENTATION_PROTOTYPE_ALLOWED__NO_PRODUCTION_CLAIM
Parent evidence: UL-14 Human-Authored Hierarchical Architecture Census & Gap Audit R1

## Census correction note
The frozen prior's sequence total is **11,213**, not 10,853. The earlier value was a transcription/metadata error discovered by consistency audit against the stored A0 structural-representability result and the episode-plan aggregate. Distribution quantiles used by the planner were unchanged. UL-16 R2 binds the corrected prior profile hash.

## Purpose
Repair the Candidate Showrunner upper planning spine so that rich narrative state is not collapsed into a small fixed set of axes, single-owner sequences, and deterministic 2/3-scene lowering.

## Hypothesis
An Adaptive Multi-Obligation Planner that explicitly preserves simultaneous narrative obligations and uses DB64 only as distributional/metrological prior will produce structurally richer, less uniform, more recoverable Episode -> Sequence -> Scene architecture while remaining compatible with the existing Canonical Typed IR and downstream Provider renderer/state layers.

## Research questions
1. Can due-now obligations be fully lowered into Sequence and Scene plans without dropping CHARACTER / RELATIONSHIP / INFORMATION / SOCIAL / PAYOFF strands?
2. Can deferred obligations remain present as pressure/residue without being falsely marked fulfilled?
3. Can multiple owners and multiple obligation kinds coexist inside a sequence when causally/relationally justified?
4. Can sequence count and per-sequence scene count remain variable rather than being forced to a 10x5 or 2/3-scene grid?
5. Can the repaired planner lower into the current Canonical Typed IR V2 with zero validation errors?
6. Does reverse reconstruction from Scene -> Sequence -> Episode recover the planned obligations?

## Frozen input classes
The planner accepts source-cutoff-safe current narrative state only. It normalizes seven obligation classes:
- EVENT
- THREAD
- RELATIONSHIP
- CHARACTER
- INFORMATION
- SOCIAL
- PAYOFF

Target-episode source material is forbidden as a semantic donor in forward-generation experiments.

## DB64 use boundary
DB64 R108 61-work corpus may provide only:
- structural distributions;
- metrology targets;
- validator calibration;
- schema examples;
- non-target holdout learning evidence under source-cutoff rules.

It must not provide the hidden target episode's actual future event/scene content.

Frozen distributional prior from UL-14:
- 61 works / 1,160 episodes;
- **11,213 source-grounded/planned sequence records**;
- 73,639 source-grounded scene cards;
- episode sequence count: P10 6 / median 9 / P90 14 / observed 2..29;
- episode scene budget: P10 46 / median 62 / P90 81.1 / observed 6..182;
- sequence scene budget: P10 3 / median 7 / P90 10 / observed 1..25.

These are priors, not exact quotas.

## Treatment design
### T1 Obligation Portfolio
Compile all currently active obligations without reducing them to 2-3 episode axes.

### T2 Due/Defer separation
- due/nondeferrable obligations must be structurally scheduled;
- deferrable obligations may be touched as pressure/residue but must not be falsely settled;
- terminal deferred ledger must preserve untouched debt.

### T3 Adaptive Sequence Architecture
- dependency-aware and pressure-aware ordering;
- multi-owner sequence allowed;
- multi-kind sequence allowed;
- weaving only when justified by shared owner, dependency, event, relationship, group, or explicit functional relation;
- independent obligations remain independent when weaving would flatten meaning;
- broadcast mode uses a depth floor informed by corpus median, never an exact count.

### T4 Adaptive Scene Architecture
- per-sequence scene count derived from obligation burden, owner count, kind count, dependency burden, pressure, and deferred pressure;
- no hard 2/3-scene rule;
- broadcast mode uses a source-grounded minimum depth guard, not a fixed scene target;
- each scene must declare state-delta requirement, physicalization requirement, exit pressure, and downstream consumer.

### T5 Reverse reconstruction / backpropagation
The output must permit reconstruction of:
- due obligation coverage from sequences;
- due obligation coverage from scenes;
- deferred debt preservation;
- sequence-to-scene state continuity.
Failure triggers replanning rather than renderer compensation.

### T6 Canonical compatibility
Treatment output is lowered through an adapter into the existing R53 Canonical Typed IR V2. Existing canonical validator must PASS with zero errors before any provider rendering experiment.

## Control
Control is the current R53 upper planning path:
`compile_episode_synopsis_architecture -> infer_rwork_sequence_count_prior -> allocate_plot_lines -> plan_thick_sequences -> realize_boundary_driven_scenes`.

No claim that ENG:R47 is a literary-quality gold standard. It is only the current production/control implementation.

## Primary structural gates
All must PASS before surface generation:
1. due obligation loss = 0;
2. deferred false fulfillment = 0;
3. lost deferred debt = 0;
4. Canonical IR validation errors = 0;
5. broadcast mode sequence count >= 9 unless an explicit short-form mode is frozen before generation;
6. broadcast mode scene count >= DB64 P10 depth guard 46 unless a different runtime target is preregistered;
7. uniform identical scene count across every sequence is disallowed when >=5 sequences unless evidence justifies it;
8. with >=3 available owners, >75% owner concentration requires an explicit story-state justification;
9. at least 25% of sequences should be multi-owner or multi-kind in a rich-ensemble qualification packet unless the input state itself is demonstrably single-strand;
10. every scene has a downstream consumer or explicit episode-exit consumer.

The diversity thresholds are diagnostic floors, not literary quality scores.

## Secondary evaluation
After structural gates:
- plan-to-surface fidelity;
- reverse reconstruction by blind judges;
- ensemble and relationship pressure;
- event diversity;
- scene necessity/removal counterfactual;
- non-expository physicalization;
- whole-episode architecture quality.

## Provider gate
A same-chat analog or mock generation cannot qualify UL-15. Live qualification requires fresh isolated provider calls with receipts under the existing UL-11/UL-12 isolation rules.

## Promotion boundary
UL-15 prototype/test PASS does not modify Production ENG:R47, Candidate physical authority, DB59, Formal count, or SYNC-R53. A new physical successor can only be built after implementation and regression closure, followed by the full 12-step custody gate.

Status token:
`UL15__PREREGISTERED__CENSUS_CORRECTED_11213__ADAPTIVE_MULTI_OBLIGATION_PLANNER__DUE_DEFER_SEPARATION__VARIABLE_SEQUENCE_SCENE_ARCHITECTURE__REVERSE_RECONSTRUCTION__CANONICAL_IR_COMPATIBILITY_REQUIRED`