# Literary OS — Literary Narrative Operating Engine Master Blueprint R1
Date: 2026-09-07
Classification: DESIGN / PREFORMAL / NO EXPERIMENT OUTPUTS
Status: PROPOSED_MASTER_DEVELOPMENT_DIRECTION

## 0. Mission
Literary OS is not a database viewer, next-scene predictor, synopsis generator, or prompt template system.

The target is a **Literary Narrative Operating Engine** that:
1. reverse-engineers how completed dramas are structured from series -> episode -> sequence -> scene;
2. stores that reverse-engineered craft knowledge with source/provenance boundaries;
3. retrieves only the relevant structural knowledge for the current writing problem;
4. converts current story state into episode/sequence/scene plans;
5. assigns causal ownership across protagonists, opposition, supporting characters, relationships, and social groups;
6. lowers plans into scenes and literary surface realization;
7. detects lower-layer failures and sends them back to the responsible upper layer for re-planning;
8. proves which database values were actually consumed through receipts/traces;
9. preserves scientific claim boundaries and physical package authority after every task unit.

The database is therefore a **reverse-engineered craft-knowledge substrate**, not merely an archive.

## 1. Research thesis already supported by project lineage
The historical database/reinforcement authorities state that the objective was never to add decorative layers. The purpose is to make the corpus `PLANNER_TRAINABLE + RUNTIME_CONSUMABLE`, and CT-06H/CT-07 showed that deeper structural representation restored top-down generation signal while thin representations lost it.

The canonical reinforcement chain already identified:
`SourceLock -> Stage01 SceneCard -> Stage02 SequenceBlueprint/EpisodeArc -> Stage03 CharacterArc/RelationshipArc/PayoffCandidate -> Stage04 CrossEpisodeEdge/FullSeriesArc -> CANONICAL THICK -> PlannerInput(R5) -> RuntimeSceneProjection(R8)`.

The key current engineering problem is not absence of all knowledge. It is **incomplete consumer wiring**.

## 2. Current knowledge assets and their intended meaning
### 2.1 Source/Evidence Authority
- SourceLock / original script source
- Source hashes / evidence refs
- Scene membership / episode boundaries

Purpose: prevent invented retrospective truth and future leakage.

### 2.2 Reverse-engineered descriptive/design GT
- Stage01 SceneCard
- Stage02 SequenceBlueprint
- EpisodeArc
- Stage03 CharacterArc
- RelationshipArc
- PayoffCandidate / LocalEdge
- Stage04 CrossEpisodeEdge / FullSeriesArc
- CANONICAL THICK: `cast`, `event`, `info_shift`, `plant_payoff`, `scene_notes`

Purpose: record what narrative work each layer performed in completed dramas.

### 2.3 Operational/Derived planning state
- R5 PlannerInput: previous exit state, character states, relationship states, unresolved payoff threads, active causal threads, subplot/character debt, world constraints
- R8 RuntimeSceneProjection: scene-consumable projection of THICK + R5
- EntityRegistry / CastPresence / CharacterLoad / coverage ledgers where available

Purpose: convert historical analysis into a state packet the engine can actually use.

### 2.4 Retrieval/index layer
- Functional DB59 retrieval / Frozen Retrieval Index
- Future multi-view indexes

Purpose: select relevant craft exemplars/structures. The index is never a new truth authority.

### 2.5 Prospective generative artifacts
- Series Plan
- Episode Allocation
- Episode Plan/Synopsis
- Ensemble/Ecology Plan
- Sequence Plan
- Scene Plan
- Surface realization

Purpose: create a new work. These must not be confused with retrospective GT.

## 3. Current gap taxonomy
Every schema/layer must be classified by all four dimensions:
1. `EXISTS?`
2. `COVERAGE?`
3. `SEMANTIC_QUALITY/PROVENANCE?`
4. `CONSUMED_BY_ACTIVE_RUNTIME?`

A field is not complete because it exists.

Gap classes:
- `ABSENT_SCHEMA`
- `PRESENT_PARTIAL_COVERAGE`
- `PRESENT_NOT_CONSUMED`
- `CONSUMED_WITHOUT_CAUSAL_PROOF`
- `DERIVED_ONLY_NOT_CANONICAL`
- `LEAKAGE_RISK`
- `SEMANTIC_NOISE_OR_TEMPLATE_RISK`
- `STALE_RUNTIME_PROJECTION`

Mandatory adoption doctrine:
`Value changes -> Consumer receives -> selected semantic payload changes -> LLM provider input changes -> downstream behavior/trace changes -> receipt proves propagation`.

## 4. Architectural principle: consumer-first reinforcement
Do NOT attempt to make every DB layer perfect before engine development.

Instead:
1. define the consumer contract for a real planning decision;
2. identify which existing DB fields can satisfy it;
3. connect and causally validate those fields;
4. only then reinforce missing/low-quality coverage;
5. promote new schema only after consumer utility is demonstrated.

This prevents unused sidecars and decorative schema growth.

## 5. Target runtime architecture

```text
SOURCE / CURRENT STORY STATE
        |
        v
Narrative State Kernel
        |
        v
Planning Question Router
        |
        +-------------------------+
        |                         |
        v                         v
Narrative Knowledge Bus      Constraint / Safety Bus
        |                         |
        v                         |
Multi-view Retrieval             |
        |                         |
        v                         |
NarrativeArchitecturePacket <----+
        |
        v
Series / Episode Planner
        |
        v
Ensemble-Ecology & Event-Ownership Planner
        |
        v
Sequence Planner
        |
        v
Scene Planner
        |
        v
LLM Surface Realizer
        |
        v
Quality / Continuity / Voice / Thread Monitors
        |
        v
Responsible-Ancestor Refinement Router
        |
        +------ back to the responsible upper layer ------>
```

Python/runtime owns routing, state, retrieval, validation, receipts, fail-close, commit/rollback, and refinement control. Literary prose remains provider/LLM work: `PYTHON_LITERARY_SURFACE_BYTES = 0`.

## 6. Narrative State Kernel
The kernel represents the story at a planning boundary, not the finished target episode.

Minimum state:
- previous episode exit state
- current character states
- relationship states
- unresolved payoff/callback threads
- active causal threads
- subplot debt
- character debt
- remaining episode count
- world/source constraints
- entity/group availability
- current allocation history

R5 PlannerInput is the historical foundation of this kernel and must be extended only through evidence-safe views, not future-answer leakage.

## 7. Narrative Knowledge Bus: multi-view retrieval instead of one global search
One retrieval query cannot represent every writing problem.

The router chooses one or more views according to the planning question.

### V1 — Macro Architecture View
Sources:
- FullSeriesArc
- EpisodeArc
- Episode Allocation / synopsis planning data
- sequence topology

Use for:
- episode function
- escalation/relief placement
- remaining-run allocation
- macro turn timing

### V2 — Character State View
Sources:
- CharacterArc
- CharacterLoad
- CastPresence
- THICK `cast.desire_or_function/participation`

Use for:
- who must act now
- unresolved character pressure
- underused/overused character balance
- character-specific causal agency

### V3 — Relationship State View
Sources:
- RelationshipArc
- current R5 relationship state
- related THICK cast/event/info-shift records

Use for:
- relationship progression/regression
- conflict/bond timing
- relational consequences

### V4 — Ensemble / Social Ecology Evidence View
Sources:
- character co-presence
- RelationshipArc graph
- CastPresence / CharacterLoad
- THICK participation roles
- Episode axis ownership
- entity/organization evidence when available

Use for:
- protagonist/opposition/support group balance
- social pressure/resource/information routes
- event ownership candidates
- group focus allocation

This view is initially DERIVED, not canonical truth.

### V5 — Thread / Payoff / Information View
Sources:
- THICK plant_payoff
- PayoffCandidate
- CrossEpisodeEdge
- ThreadState
- info_shift

Use for:
- what must remain open
- what may be escalated
- what is eligible for callback/payoff
- information asymmetry

### V6 — Sequence Function View
Sources:
- CANONICAL THICK
- SequenceBlueprint
- boundary data
- scene functional propositions

Use for:
- how an episode goal should be decomposed into sequence functions
- ordering and transition
- mismatch avoidance

### V7 — Scene Realization View
Sources:
- R8 RuntimeSceneProjection
- SceneCard
- character/relationship current state
- sequence function

Use for:
- direct scene writing constraints
- action/dialogue/subtext realization

### V8 — Negative / Mismatch View
Sources:
- deterministic boundary negatives
- mismatched blueprints/retrieval controls
- known failure exemplars

Use for:
- discriminator/critic training
- rejection of structurally plausible but context-wrong plans

## 8. NarrativeArchitecturePacket (NAP)
The Knowledge Bus must not dump the database into the prompt. It composes a bounded packet.

Proposed top-level contract:
- `planning_question`
- `source_cutoff`
- `current_state`
- `macro_architecture_refs`
- `character_state_refs`
- `relationship_state_refs`
- `ensemble_ecology_view`
- `thread_payoff_info_refs`
- `sequence_function_refs`
- `negative_constraints`
- `selected_exemplars[]`
- `selection_reason[]`
- `provenance[]`
- `diagnostics` (kept separate from literary conditioning)

Rules:
- every semantic item has source/provenance;
- unknown stays unknown;
- selection diagnostics never leak as literary content;
- bounded per-view budget;
- irrelevant DB mutation must not change the packet;
- selected evidence mutation must change the relevant packet field;
- no actual target/post-cutoff source.

## 9. Social Ecology design
Current code contains Social Ecology / event-ownership concepts, but DB59 does not yet contain a complete canonical SocialEcologyGraph for all works.

Do not invent one as canonical truth.

Create a provisional `SocialEcologyEvidenceView`:
- `groups[]`
  - `group_id`
  - `label`
  - `evidence_type`
  - `evidence_refs[]`
- `memberships[]`
  - `character_id`
  - `group_id`
  - `confidence_class`
  - `evidence_refs[]`
- `group_relations[]`
  - `from_group`
  - `to_group`
  - `relation_function`
  - `evidence_refs[]`
- `event_ownership_candidates[]`
  - `event/axis_ref`
  - `owner_character_or_group`
  - `ownership_basis`
  - `evidence_refs[]`
- `unknowns[]`

Inference policy:
- deterministic/explicit evidence -> derived value allowed;
- ambiguous semantic membership -> LLM proposal with evidence, not canonical promotion;
- no evidence -> `UNKNOWN`;
- future/post-cutoff information prohibited.

After utility and human audit, consider a new canonical schema version. Do not promote first and search for utility later.

## 10. Planner hierarchy
### P0 Series/Long-range planner
Outputs:
- series/arc objective
- long-range tension allocation
- major group/relationship trajectories
- remaining-run constraints

### P1 Episode allocation/planner
Consumes:
- Narrative State Kernel
- Macro/Character/Relationship/Thread views
Outputs:
- episode function
- episode conflict axis
- subplot allocation
- open/close/defer decisions

### P2 Ensemble-Ecology/Event-Ownership planner
Consumes:
- episode plan
- Character/Relationship/Ensemble views
Outputs:
- active groups
- character/group event ownership
- relationship axes
- supporting-cast allocation
- must-move / must-not-collapse-to-protagonist-only constraints

This stage should sit **after Episode Plan and before Sequence Plan**.

### P3 Sequence planner
Consumes:
- episode plan
- ensemble/ecology/event ownership
- Sequence Function View
Outputs:
- ordered sequence functions
- cast/ownership per sequence
- event/info/payoff intent
- scene budgets/boundaries

### P4 Scene planner
Consumes:
- sequence plan
- R8-like runtime projection
- current character/relationship state
Outputs:
- scene function
- action/interaction goal
- subtext/information obligation
- transition obligation

### P5 Surface realizer
LLM writes actual screenplay surface under fixed contracts.

## 11. Bidirectional refinement
Forward lowering alone is insufficient.

Monitor failures and route each one to a responsible ancestor:
- dialogue/voice failure -> Scene/Surface layer
- scene lacks causal function -> Scene Plan / Sequence Plan
- sequence imbalance -> Sequence / Ensemble plan
- supporting cast disappears -> Ensemble/Ecology plan
- relationship jump -> Relationship/Episode layer
- payoff timing error -> Thread/Episode layer
- episode has wrong macro function -> Episode/Series layer

Refinement must produce a trace:
`failure -> responsible ancestor -> revised upper artifact -> re-lowering -> changed descendant`.

No trace = no claim of bidirectional treatment.

## 12. Database improvement program
### Tier 1 — Consume what already exists
Highest priority:
- CharacterArc
- RelationshipArc
- THICK cast/participation
- R5 character/relationship/thread/debt state
- Thread/Payoff/Info
- available EXT6 CharacterLoad/CastPresence

Goal: eliminate `PRESENT_NOT_CONSUMED` before adding new schema.

### Tier 2 — Build evidence-safe derived operational views
- SocialEcologyEvidenceView
- EventOwnershipView
- EnsembleAllocationView
- NarrativeArchitecturePacket

Goal: make heterogeneous DB layers operationally usable without rewriting canonical source-derived layers.

### Tier 3 — Coverage reinforcement driven by consumer need
For every view, create a matrix:
`Schema x Work x Episode x Coverage x Quality x Provenance x Consumer`.

Prioritize missing data only when:
- the active consumer needs it;
- coverage is the limiting factor;
- source-safe reinforcement is possible;
- an experiment can measure incremental utility.

### Tier 4 — Canonical schema promotion
Only promote a derived view to canonical schema after:
- consumer utility demonstrated;
- semantic audit passed;
- leakage policy passed;
- reproducibility/provenance complete;
- developer accepts migration.

## 13. Consumption Ledger
Every planning run should emit a machine-readable ledger:
- requested planning question
- views queried
- candidate records
- selected records
- selected semantic hashes
- excluded/irrelevant records
- provider-input hash
- downstream artifact hash
- causal mutation test IDs
- source cutoff

This makes “the DB was actually used” auditable.

## 14. Experiment roadmap
### Phase A — close current P07-B repair physically
The current DB-connection pretest found `retrieve_many()` vs runtime `retrieve()` donor drift and repaired it by making runtime retrieval canonical. Before any new scientific generation:
- rerun exact regression from repaired bytes;
- propagate the repair + Attempt-1 HOLD + Attempt-2 PASS into 5 Parts / 9 Packages;
- new Manifest/Trust Root;
- physically close P07-B.

### Phase B — P07-B2 Narrative Architecture DB Adoption (mechanical pretest)
No craft scoring first.

For Character, Relationship, Ensemble/Ecology, Thread/Payoff views prove:
1. source-safe record selected;
2. selected record reaches NarrativeArchitecturePacket;
3. packet reaches the intended planner stage/provider input;
4. selected-record mutation changes only the responsible payload;
5. irrelevant-unselected mutation leaves literary payload unchanged;
6. source cutoff violation = 0;
7. Python prose = 0;
8. no schema/view is claimed consumed without trace.

### Phase C — P07-B3 incremental craft pretest
Use same works/source cutoff/model/settings/budget and blind labels.

Proposed arms:
- A: current functional event retrieval only
- B: A + Character/Relationship state views
- C: B + Ensemble/Social-Ecology/Event-Ownership view
- D: C + Thread/Payoff/Information multi-view packet

Primary question: which DB view actually improves craft quality without fidelity regression?

Do not assume “more DB is better”. An arm can fail because added context is irrelevant/noisy.

### Phase D — RFV3 preregistration revision before any outputs
Current RFV3 R1 has zero outputs. If P07-B2/B3 changes what “current repaired candidate” means, supersede R1 transparently before generation.

Recommended RFV3-R2 decomposition:
- A: SUMMARY ONLY
- B: PRE-REPAIR RUNTIME / NO_RETRIEVAL
- C: FUNCTIONAL DB RETRIEVAL (current RFV2)
- D: FULL NARRATIVE-ARCHITECTURE MULTI-VIEW DB CONSUMPTION
- E: D + BIDIRECTIONAL REFINEMENT

Causal contrasts:
- A vs B: runtime information loss
- B vs C: functional retrieval value
- C vs D: narrative-architecture DB consumption value
- D vs E: bidirectional refinement value

### Phase E — CP1 current-authority integration
Recover paired Reference/Engine runner, use same provider/model/settings, prove current DB path in Engine arm, fail closed on key/allow-live/model/hash/errors.

Any CP1 code change must reseal 5 Parts / 9 Packages before Official Live.

### Phase F — Official R-F paired Live
Real provider receipts, equal budgets/settings, Reference vs current Engine.

### Phase G — R-G freeze/formal readiness
- candidate freeze
- fresh formal sample
- revised R140 preregistration
- blind/metrology integrity
- new G0 physical seal

### Phase H — Formal R140
Whole end-to-end production qualification against immutable ENG:R47 Production.

## 15. Evaluation philosophy
The engine is not a predictor of the actual next episode.

Evaluate craft:
- causal/continuity fidelity
- episode architecture
- ensemble/social ecology
- character/relationship consistency
- thread/payoff management
- temporal validity/source discipline
- creativity/authorized novelty
- long-horizon sustainability
- dialogue/scene craft
- voice differentiation
- subtext/physicalization
- pacing/economy
- repetition/template resistance
- overclosure

Actual future episode is not an answer key.

## 16. What the engine is learning
The system should not “copy dramas”. It learns **transformation operators** and structural regularities:
- how series pressure becomes episode function;
- how episode function decomposes into sequence functions;
- how character/relationship state constrains plausible action;
- how ensemble ownership distributes causality;
- how information/plant/payoff moves across scenes and episodes;
- how supporting-cast allocation prevents protagonist-only collapse;
- how a sequence design lowers into scene functions;
- how lower-layer failure identifies the upper layer that must be revised.

Retrieval supplies relevant exemplars/evidence. Planning converts structural meaning to the new story context. Generation remains new literary invention under constraints.

## 17. Physical-authority discipline
The previous failure mode must never recur.

For every completed scientific task unit:
`research/code change -> tests/evidence -> 5 Parts / 9 Packages propagation -> changed=new SHA / unchanged=byte-identical proof -> Manifest/Trust Root -> physical delivery -> pointer alignment -> only then next task`.

No working-state research may run multiple stages ahead of developer-held physical authority.

## 18. Immediate next sequence
1. Physically reseal the current P07-B runtime retrieval parity repair.
2. Create Schema/Consumer/Coverage matrix from current DB59.
3. Preregister P07-B2 Narrative Architecture DB Adoption mechanical pretest.
4. Implement Character/Relationship/Thread views first using existing canonical data.
5. Implement SocialEcologyEvidenceView as derived evidence-safe view, not invented canonical truth.
6. Connect `ENSEMBLE_ECOLOGY_PLAN` between Episode Plan and Sequence Plan.
7. Run mechanical causal adoption gates.
8. Reseal 5 Parts / 9 Packages.
9. Run P07-B3 craft pretest.
10. If justified, supersede zero-output RFV3 R1 with RFV3-R2 and continue to CP1/Live/Formal chain.

## 19. Current design status token
`LITERARY_NARRATIVE_OPERATING_ENGINE_MASTER_BLUEPRINT_R1__CONSUMER_FIRST_DB_REINFORCEMENT__MULTIVIEW_NARRATIVE_KNOWLEDGE_BUS__NARRATIVE_ARCHITECTURE_PACKET__SOCIAL_ECOLOGY_DERIVED_VIEW__HIERARCHICAL_PLANNING__BIDIRECTIONAL_REFINEMENT__P07B2_BEFORE_RFV3`
