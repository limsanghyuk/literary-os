# Closed Narrative Operating Loop -> Broadcast Episode Development Plan R1

Date: 2026-09-07
Classification: DEVELOPMENT ARCHITECTURE / PREFORMAL / NO FORMAL COUNT DELTA
Status: DESIGN FROZEN FOR IMPLEMENTATION ORDER

## 0. Purpose

The next development phase is no longer to prove isolated module existence. The purpose is to integrate the already-developed research components into one provenance-bound, DB-grounded, provider-backed, bidirectionally refinable Literary Narrative Operating Engine that can produce a full broadcast-scale episode and carry its state into the next episode.

Target operating principle:

> structurally understand why completed dramas were designed as they were, retrieve the most relevant craft knowledge for the current story state and planning question, transform that knowledge into a new narrative, diagnose lower-layer failure, route it to the minimum responsible ancestor, re-lower, and commit only accepted state.

Current physical authority remains the P07-A RFV2 5-Part/9-Package set. A later P07-B working repair fixed runtime/batch retrieval donor drift and passed 186/186 regression, but must be physically resealed before new code is promoted.

## 1. Canonical Target Architecture

```text
ORIGINAL BRIEF / CURRENT STORY
        |
        v
NARRATIVE STATE KERNEL
        |
        v
SERIES / WRITER-ROOM ARCHITECTURE
        |
        v
EPISODE ALLOCATION
        |
        v
EPISODE PLAN
        |
        v
PLANNING QUESTION ROUTER
        |
        v
NARRATIVE KNOWLEDGE BUS
  - Macro Architecture Retrieval
  - Character State Retrieval
  - Relationship State Retrieval
  - Ensemble / Social Ecology Retrieval
  - Thread / Payoff / Information Retrieval
  - Sequence Function Retrieval
  - Negative / Mismatch Retrieval
        |
        v
NARRATIVE ARCHITECTURE PACKET
        |
        v
ENSEMBLE ECOLOGY PLAN
        |
        v
CANDIDATE PORTFOLIO
        |
        v
SAFETY / CRITIC / SELECTOR
        |
        v
SEQUENCE PLAN
        |
        v
SCENE PLAN
        |
        v
LLM SURFACE REALIZATION
        |
        v
CRAFT / CONTINUITY / ECOLOGY / THREAD DIAGNOSTICS
        |
        v
BIDIRECTIONAL RESPONSIBLE-ANCESTOR ROUTER
        |
        +--> minimum-stage LLM replan
        |          |
        |          v
        +------ RE-LOWERING
                   |
                   v
        ACCEPT / REJECT GATE
                   |
                   v
        CANONICAL STATE COMMIT / CARRY
                   |
                   v
              NEXT EPISODE
```

This is the single target main path. Existing subloops may remain as test harnesses, but production-candidate semantics must pass through this canonical route.

## 2. Architectural Doctrine

### 2.1 DB consumption means right knowledge at the right decision point

Do not dump all DB fields into every prompt. `ALL DATA ALWAYS` is prohibited. The target is: every useful reverse-engineered layer is available to the correct consumer when its decision requires it.

### 2.2 Consumer-first reinforcement

For every DB layer:
1. define the consumer decision;
2. define the minimal evidence contract;
3. use existing canonical data first;
4. measure coverage and provenance;
5. only then reinforce missing data;
6. prove causal adoption before expanding rollout.

### 2.3 Provenance-bound semantics

Every retrieved semantic item entering an LLM planning stage must identify its source layer, work/episode/sequence identity, source cutoff eligibility, semantic hash, selection reason, and confidence/diagnostic metadata. Diagnostic scores must not be mixed into literary payload text.

### 2.4 Fail-close and abstention

When evidence is weak or ambiguous, use `UNKNOWN`, `NO_RETRIEVAL`, or `HOLD`; do not invent a donor, group, relationship, or plot owner to keep the pipeline moving.

### 2.5 Python literary prose generation = 0

Python/deterministic tooling may validate, select, route, materialize packets, compare hashes, measure coverage, or serialize. Broadcast literary surface must come from the approved LLM provider path.

## 3. New Core Interfaces

### 3.1 NarrativeStateKernel

Purpose: one canonical current-story state before planning an episode.

Required domains:
- series_position
- previous_episode_exit_state
- character_states
- relationship_states
- active_threads
- unresolved_payoffs
- subplot_debt
- character_debt
- ensemble_usage_state
- group/social-ecology evidence
- world_constraints
- remaining_episode_budget
- accepted_previous_state_hash

Inputs should derive from R5/CharacterArc/RelationshipArc/ThreadState/accepted generated state as applicable.

### 3.2 PlanningQuestionRouter

Purpose: determine which knowledge views are needed for the current planning decision.

Input:
- planning_stage
- current_state
- unresolved_decisions
- target_axis
- candidate risk flags

Output:
- question_type[]
- required_views[]
- optional_views[]
- excluded_views[]
- max_evidence_budget per view
- source-cutoff contract

Question classes:
- macro_progression
- episode_function
- character_choice
- relationship_movement
- ensemble_allocation
- group_pressure
- event_ownership
- thread_payoff
- information_asymmetry
- sequence_function
- scene_realization
- negative_pattern_avoidance

### 3.3 NarrativeKnowledgeBus

Purpose: common access layer over reverse-engineered DB knowledge.

Initial adapters:
1. MacroArchitectureView: FullSeriesArc / EpisodeArc / allocation examples
2. CharacterStateView: CharacterArc / THICK cast / CharacterLoad / CastPresence / R5
3. RelationshipStateView: RelationshipArc / R5 relation state
4. EnsembleEcologyView: THICK participation / CharacterLoad / CastPresence / Relationship evidence / episode axis
5. ThreadPayoffInfoView: ThreadState / CrossEpisodeEdge / PayoffCandidate / THICK plant_payoff / info_shift
6. SequenceFunctionView: SequenceBlueprint / THICK / Boundary / Scene membership
7. NegativeMismatchView: mismatch arms / negative boundaries / invalid consumption examples

### 3.4 NarrativeArchitecturePacket (NAP)

This is the only DB-derived packet allowed to enter upper planning stages.

Required sections:
- planning_question
- current_state_summary
- macro_constraints
- selected_character_evidence
- selected_relationship_evidence
- ensemble_ecology_evidence
- thread_payoff_info_evidence
- sequence_function_exemplars
- negative_constraints
- provenance_ledger
- retrieval_diagnostics
- abstentions / unknowns

Hard rules:
- bounded evidence count;
- no raw source dump;
- no future-target leakage;
- no duplicate semantic truth systems;
- no unproven Social Ecology fact promoted to canonical truth.

## 4. Social Ecology / Event Ownership Design

### 4.1 SocialEcologyEvidenceView first, canonical schema later

Do not immediately rewrite DB59. Build a derived evidence-safe view from existing data.

Candidate evidence sources:
- CharacterArc
- RelationshipArc
- THICK cast/participation
- CastPresence
- CharacterLoad
- EntityRegistry where available
- Episode axis / sequence ownership

Output:
- group_candidates
- membership_candidates
- group_relation_candidates
- pressure_channels
- resource/information asymmetry
- event_ownership_candidates
- provenance per claim
- confidence / UNKNOWN state

Only evidence-supported entries enter the NAP.

### 4.2 ENSEMBLE_ECOLOGY_PLAN becomes a mandatory main-path stage

Insert between EPISODE_PLAN and CANDIDATE_PORTFOLIO / SEQUENCE_PLAN.

Required outputs:
- active_groups
- active_characters
- relationship_axes_to_move
- event_ownership
- counterparty ownership
- support/comic/deferred axes when justified
- protagonist concentration risk
- underused-character risk
- must_move_characters
- must_not_collapse_to_protagonist_only
- downstream sequence obligations

## 5. Candidate Portfolio / Selector Integration

Candidate generation must happen before sequence commitment, not as a detached side loop.

For each episode plan, generate 3-5 candidate episode realizations that differ in meaningful architecture, for example:
- event owner
- relationship movement
- ensemble distribution
- information-release timing
- thread payoff timing
- sequence order / midpoint turn

Selector inputs:
- NAP evidence
- ecology plan
- long-horizon state
- safety/temporal eligibility
- novelty grounding
- structural/craft risk estimate

Selector must choose one commit candidate and preserve runner-up reasoning for future memory only when eligibility rules allow.

## 6. Broadcast Episode Production Protocol

Target development output is one synthetic full broadcast episode from source-safe prior context.

### 6.1 Episode scale target

Development target range:
- 9-12 sequences
- approximately 45-60 scenes
- approximately 35,000-45,000 Korean characters for a full broadcast-scale script
- full scene heading/action/dialogue/reaction/subtext surface

These are production-scale development targets, not evaluation answers to an actual hidden episode.

### 6.2 Production stages

#### E0 State Lock
Freeze current NarrativeStateKernel, source cutoff, DB authority, engine version, provider configuration, and output budget.

#### E1 Series/Writer-room Check
Resolve this episode's long-range function, non-negotiable series constraints, active threads, and remaining episode pressure.

#### E2 Episode Architecture
Produce detailed episode synopsis/architecture: opening state, acts/major movements, midpoint, reversals, climax, exit state, thread operations, relationship operations.

#### E3 Knowledge Routing / NAP
PlanningQuestionRouter selects views. NarrativeKnowledgeBus retrieves bounded evidence. NAP is sealed.

#### E4 Ensemble Ecology / Event Ownership
Decide who acts, who opposes, who bears consequence, which relationships move, and which groups apply pressure.

#### E5 Candidate Portfolio / Selector
Generate 3-5 episode architecture candidates; select one under frozen rules.

#### E6 Sequence Plan
Lower selected episode architecture into 9-12 sequences. Every sequence must have:
- goal/function
- active cast and participation
- event
- information movement
- relationship movement where relevant
- thread/payoff operation where relevant
- value shift / turn
- sequence exit obligation
- scene budget

#### E7 Scene Plan
Lower each sequence into scene-level contracts. Every scene must identify:
- scene function
- POV/focality
- participating characters
- conflict / pressure
- ordered beats
- information action
- relationship action
- physical/subtext target
- entry/exit state

#### E8 Surface Realization
Provider-backed LLM renders scenes. Rendering is performed in bounded batches while preserving global episode state and sequence obligations.

Recommended development batch size: 5-8 scenes per provider call or equivalent chunking, with scene-by-scene contract hashes preserved.

#### E9 Local Diagnostics
After every rendered sequence, evaluate:
- semantic contract fidelity
- scene functional fulfillment
- causal continuity
- character voice consistency
- relationship delta plausibility
- exposition load
- subtext / physicalization
- repetition/template risk
- pacing / line economy
- ensemble concentration
- thread state accuracy

#### E10 Responsible-Ancestor Routing
Do not rewrite the whole episode by default.

Routing examples:
- bad wording only -> SURFACE
- scene cannot realize its objective -> SCENE_PLAN
- sequence lacks turn/causal force -> SEQUENCE_PLAN
- character/event ownership wrong -> ENSEMBLE_ECOLOGY_PLAN
- episode function/timing wrong -> EPISODE_PLAN
- series trajectory conflict -> SERIES_ARCHITECTURE

#### E11 Replan / Re-lower
Replan only the minimum responsible ancestor, then deterministically identify and regenerate all dependent descendants.

#### E12 Global Episode Audit
After all sequences pass local gates, evaluate the full episode as one work.

#### E13 State Commit / Carry
Only an accepted episode updates canonical narrative state. Commit:
- character state deltas
- relationship state deltas
- thread/payoff state
- ensemble usage state
- group/social-ecology state changes
- world-state changes
- new debts/open obligations
- episode exit state
- state hash

Then generate the next episode's NarrativeStateKernel.

## 7. Bounded Bidirectional Refinement Policy

The loop must be powerful but bounded.

Development default:
- max 2 repair attempts at the same responsible layer per defect class;
- max 1 escalation to a higher ancestor unless a new diagnostic demonstrates that the lower repair was structurally blocked;
- max 3 global episode repair cycles before `HOLD_REDESIGN_REQUIRED`;
- preserve every failed attempt and its diagnostics;
- no threshold/prompt/rubric tuning after observing comparative craft results within a preregistered run.

## 8. Broadcast-Scale Quality Gates

### Structural gates
- source cutoff/leakage = 0
- episode function fulfilled
- sequence count/scene budget within frozen target unless justified
- sequence causal chain intact
- no unsupported invention violating current story state
- time/space continuity coherent

### Character/relationship gates
- character goals/actions consistent with state
- relationship movement earned
- no protagonist-only collapse where ensemble plan requires distributed ownership
- supporting characters have consequential action rather than decorative presence

### Thread gates
- active/open/paid/closed states coherent
- no premature over-closure
- payoff timing supported
- unresolved obligations carried forward

### Surface craft gates
- dialogue naturalness
- voice differentiation
- subtext/physicalization
- pacing/line economy
- repetition/template resistance
- exposition control

### Global episode gates
- opening-to-exit trajectory coherent
- act/sequence escalation perceptible
- midpoint/climax function supported
- ensemble balance intentional
- relationship and plot axes cross rather than run as disconnected summaries
- broadcast-length surface complete

## 9. Development Work Packages

### WP0 — Physical Synchronization
Before new integration code, reseal the already-passed P07-B canonical retrieval parity repair into the 5 Parts/9 Packages. This prevents another working-state/physical-authority divergence.

### WP1 — Integration Spine
Create one orchestrator that owns the canonical target route and removes the split between hierarchical semantic planning and the closed-loop selector/state path.

Exit gate: one test-double run traverses every stage in order with trace continuity.

### WP2 — Knowledge Bus / NAP
Implement PlanningQuestionRouter, view adapters, NarrativeArchitecturePacket, provenance ledger, and bounded retrieval budget.

Exit gate: selected/unselected mutation proves view-specific causal adoption without cross-view contamination.

### WP3 — Ensemble Ecology / Ownership
Implement SocialEcologyEvidenceView and insert ENSEMBLE_ECOLOGY_PLAN into main path.

Exit gate: relationship/participation/load mutations change relevant ecology/ownership output; irrelevant mutations do not.

### WP4 — Portfolio / Selector Main-path Integration
Insert candidate portfolio and selector before sequence commitment.

Exit gate: candidate differences are architecture-level, selected candidate alone drives downstream sequence plan, and selector decision is traceable.

### WP5 — Bidirectional Repair Loop
Connect diagnostics -> responsible ancestor -> replan -> re-lowering -> re-render.

Exit gate: injected scene/sequence/episode defects route to the minimum correct ancestor and regenerate only descendants.

### WP6 — State Commit / Multi-episode Carry
Integrate accepted episode commit with the next episode kernel.

Exit gate: EP N accepted state changes EP N+1 planning input; rejected attempts do not mutate canonical state.

### WP7 — Broadcast-scale Surface Production
Use provider-backed LLM path to produce 45-60 scene / 35k-45k character full episode under the integrated loop.

Exit gate: complete episode, no Python prose, full trace/receipt chain, all local/global gates executed.

### WP8 — Internal Development Comparison
Use one fixed synthetic development story and compare staged capability only after the integrated mechanics are frozen.

Recommended arms:
- F0 current physical baseline
- F1 + Narrative Knowledge Bus / multi-view DB
- F2 + Ensemble Ecology / Event Ownership
- F3 + Portfolio/Selector integrated
- F4 + Bidirectional Refinement closed loop

Purpose: development diagnosis, not formal claim.

### WP9 — Physical Reseal
After each meaningful code/science unit, propagate changed state into 5 Parts/9 Packages and reseal Manifest/Trust Root. No next scientific stage before physical closure.

## 10. Scientific Sequence After Architecture Completion

Only after WP0-WP9 mechanics are closed:
1. P07-B2 Narrative Architecture DB Adoption mechanical pretest.
2. P07-B3 craft pretest: functional-only retrieval vs +character/relationship vs +ensemble/ecology vs +thread/payoff.
3. Supersede RFV3 R1 before outputs if the new architecture materially changes causal arms.
4. Recommended RFV3-R2 arms:
   - A Summary-only
   - B Pre-repair / no retrieval
   - C Functional retrieval
   - D Full Narrative Architecture DB consumption
   - E D + Bidirectional Refinement
5. CP1 current-authority Live integration.
6. Official R-F paired Live.
7. R-G freeze / formal readiness.
8. Fresh formal sample / revised R140 prereg / G0.
9. Formal R140 Production Qualification.

## 11. Immediate Implementation Order

The next implementation should proceed in this exact order:

1. physically reseal P07-B donor-parity repair;
2. create the single canonical orchestrator skeleton;
3. implement PlanningQuestionRouter;
4. implement NarrativeKnowledgeBus adapters and NAP;
5. wire ENSEMBLE_ECOLOGY_PLAN;
6. wire CandidatePortfolio/Selector;
7. wire diagnostics -> BidirectionalRefinement -> re-lowering;
8. wire accepted episode -> canonical state commit -> next kernel;
9. run a full test-double integrated episode;
10. run a provider-backed development episode at full broadcast scale;
11. diagnose and repair under bounded-loop policy;
12. reseal 5 Parts/9 Packages;
13. then begin causal craft pretests.

## 12. Position Statement

The target is no longer a collection of successful literary modules. The next milestone is a single operating system for narrative production: one state kernel, one DB-grounded knowledge bus, one planning hierarchy, one ensemble/ownership controller, one candidate-selection path, one provider surface path, one diagnostic/refinement loop, and one canonical state commit/carry mechanism capable of producing and improving a full broadcast episode without losing provenance or future-information discipline.
