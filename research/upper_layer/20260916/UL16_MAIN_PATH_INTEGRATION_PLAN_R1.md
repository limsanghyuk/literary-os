# UL-16 Candidate Main-Path Integration Plan R1

Date: 2026-09-16
Status: READY_FOR_IMPLEMENTATION__NO_PHYSICAL_AUTHORITY_CHANGE
Parents: UL-14 gap audit; UL-15 preregistration; UL-15 prototype receipt.

## Objective
Integrate the Adaptive Multi-Obligation Planner into the real Candidate authoring path without discarding validated downstream components.

## Preserve unchanged where possible
- source-safe ingestion;
- Narrative State Kernel / current-state compilation;
- whole-story / series architecture components that survive integration audit;
- source-cutoff and entity-life-state guards;
- Canonical Typed IR V2;
- provider-backed renderer/judge interface;
- state commit/carry and replanning integrity;
- existing physical/custody governance.

## Replace or bypass in Candidate mode
Current lossy chain:
`compile_episode_synopsis_architecture -> compile_detailed_episode_synopsis -> infer_rwork_sequence_count_prior -> allocate_plot_lines -> plan_thick_sequences -> realize_boundary_driven_scenes`

Candidate UL-16 chain:
`compile_active_obligation_portfolio -> schedule_due_and_preserve_defer -> build_adaptive_sequence_graph -> build_adaptive_scene_graph -> reverse_reconstruction_gate -> canonical_adapter -> Canonical Typed IR V2`

The legacy chain remains available only as Production control / regression ablation until qualification.

## Integration components
### I1 Active Obligation Compiler
Input sources must come from current cutoff-safe state, not target future source:
- current committed event/event pressure;
- open thread/debt state;
- current relationship states and required relationship moves;
- current character-state pressures and choices;
- information asymmetry / knowledge-state obligations;
- social ecology / group ownership / institutional pressure;
- eligible plant/payoff obligations;
- terminal/finale obligations when applicable.

Output: one typed portfolio with IDs, owners, dependencies, pressure, due/defer status, and provenance.

### I2 DB64 Prior Consumer
DB64 is not a semantic donor for hidden targets. It contributes only frozen priors/metrology such as sequence/scene distributions, weaving prevalence, owner diversity ranges, and structural anti-pattern detectors.

Required receipt fields:
- DB64 authority/hash;
- prior profile hash;
- target episode source opened = false;
- post-cutoff reference count = 0.

### I3 Adaptive Sequence Graph
Each sequence may carry multiple owners and multiple obligation kinds. Edges may represent causal, relational, information, social, payoff/debt, or justified functional/thematic relations. Independent strands must remain independent if merging weakens meaning.

Required fields per sequence:
- obligation_ids;
- owner_ids;
- dependency_refs;
- deferred_pressure_ids;
- entry state/pressure;
- state_delta_required;
- exit pressure;
- downstream consumers;
- weave reason;
- removal-counterfactual necessity.

### I4 Adaptive Scene Graph
Each scene must be a state-changing transaction, not an obligation bucket split by fixed count.

Required fields:
- pre_state_ref;
- transaction obligation(s);
- participants / owners;
- objective and obstacle;
- visible action / physicalization requirement;
- information delta;
- relationship delta;
- social/group delta where applicable;
- turn/pressure change;
- exit state;
- downstream consumer ref;
- deferred pressure touched but not falsely settled;
- merge/split necessity test.

### I5 Reverse Reconstruction Gate
Before rendering:
- all due obligations recoverable from sequence graph;
- all due obligations recoverable from scene graph;
- deferred debt preserved and not falsely fulfilled;
- owner/relationship/social ecology strands traceable;
- no scene without downstream/exit consumer;
- no uniform grid artifact unless explicitly justified.

Gate failure triggers replanning; renderer compensation is forbidden.

### I6 Canonical Adapter
Lower the adaptive graph into existing SequenceIR/SceneIR contracts. UL-15 prototype proved zero-error compatibility with the current R53 Canonical Typed IR V2 validator.

## Validation ladder
Stage 0 — software/unit tests.
Stage 1 — deterministic synthetic ensemble tests.
Stage 2 — source-cutoff-safe historical replay across diverse DB64 works without using target content as donor.
Stage 3 — fresh counterfactual continuation / unseen synthetic episode generation.
Stage 4 — blind structural evaluation of Episode/Sequence/Scene plans before prose rendering.
Stage 5 — provider-backed full screenplay generation >= broadcast minimum depth, followed by blind two-stage plan/surface evaluation.
Stage 6 — state commit/carry + replanning regression.
Stage 7 — clean new SYNC physicalization and 12-step custody gate.

## Structural anti-regression gates
The Candidate implementation must fail closed on:
- hard 2/3 scene-per-sequence rule;
- exact 10x5 or other global grid target;
- due obligation loss;
- deferred false fulfillment;
- lost relationship obligations;
- lost social/group obligations;
- owner concentration >75% in a genuinely multi-owner input without explicit justification;
- uniform per-sequence scene counts across >=5 sequences without evidence;
- target episode source leakage;
- mock/analog execution being labeled Live Provider evidence.

## Research sequence after integration
1. implement I1-I6;
2. run unit/regression suite;
3. compare legacy control vs adaptive treatment on the same frozen cutoff-safe packets;
4. inspect architecture before surface generation;
5. only after structural PASS render full broadcast surfaces;
6. external blind evaluation;
7. fresh-context live Provider qualification;
8. physical successor build and custody closure.

## Authority boundary
SYNC-R53 remains the physical root. ENG:R47 remains Production. DB59 remains runtime DB authority. DB64 remains research-support candidate. Formal total remains 137 / latest R138 / R140 0/0/0.

Status token:
`UL16__MAIN_PATH_INTEGRATION_READY__REPLACE_LOSSY_EPISODE_SEQUENCE_SCENE_SPINE_ONLY__PRESERVE_CANONICAL_IR_RENDERER_STATE_CARRY__STRUCTURAL_GATES_BEFORE_SURFACE`