# Showrunner Engine Development Direction after UL-14 R1

Date: 2026-09-16
Status: **DEVELOPMENT DIRECTION LOCKED / IMPLEMENTATION AND QUALIFICATION PENDING**

## Executive decision

The Candidate must stop evolving as a validator surrounding legacy planning and become a true **closed-loop Showrunner Planner**.

The next core is not another surface renderer. It is an adaptive hierarchy:

`Cutoff-Safe Narrative State -> Obligation Portfolio -> Episode Function & Selection/Defer -> Ensemble/Social Activation -> Episode Weave Graph -> Sequence Transactions -> Scene Transactions -> Surface -> Reverse Reconstruction -> State Commit/Carry -> Responsible-Ancestor Replan`

Surface work remains downstream until the forward hierarchy qualifies.

## Development Phase G0 — Evidence correction

Completed at governance/research level:
- withdraw claim that upper-layer generative quality was stable;
- reclassify previous virtual ChatGPT screenplay runs as MOCK/ANALOG;
- reclassify R53 upper overlay as gates/validators, not a planner-quality proof;
- quarantine `EpisodeSynopsisPlan.v0.3-r1` from Candidate forward generation;
- preserve Production ENG:R47 and physical SYNC-R53 unchanged.

## Phase G1 — State-to-Obligation Adapter

Build a deterministic/provenance-preserving adapter that converts cutoff-safe state into typed obligations without inventing unsupported state.

Inputs may include:
- character state;
- relationship state;
- event/precondition state;
- information access/belief state;
- social/group state where observed;
- world state;
- plants/payoffs;
- long-horizon debts;
- episode/series thematic function.

Every obligation carries evidence refs and uncertainty/provenance.

No LLM-produced obligation enters the portfolio without explicit source/derivation status.

## Phase G2 — Episode Portfolio Selector / Abstention

Replace fixed axis selection with adaptive obligation selection.

Responsibilities:
- choose obligations that belong in the current episode;
- defer lower-pressure obligations with explicit cost/horizon/re-entry condition;
- protect long-horizon debts from accidental premature payoff;
- detect overloaded episodes and abstain/replan rather than flatten them;
- choose episode function and exit-state pressure.

Output count emerges from state. There is no axis quota.

## Phase G3 — Ensemble & Weave Architect

Generate a multi-owner graph rather than parallel isolated lanes.

Responsibilities:
- activate relevant character/relationship/group ecology;
- create causal, relationship, information and justified functional/thematic edges;
- allow subplot disappearance and re-entry;
- require cross-owner consequences where dramatically justified;
- preserve justified independent obligations without forcing artificial intersections.

The goal is not maximal interconnectedness. The goal is **necessary and legible interaction**.

## Phase G4 — Sequence Transaction Architect

Generate variable sequence transactions from the weave graph.

A sequence must answer:
- what is being attempted;
- who owns and co-owns it;
- which obligations collide or cooperate;
- what prerequisite state it consumes;
- what state changes;
- what turn/reveal/choice occurs if justified;
- what pressure it transfers to later sequences.

Sequence count and length are emergent.

## Phase G5 — Scene Transaction Architect

Generate actual forward scene plans before screenplay prose.

A Scene Transaction must specify:
- necessity;
- actors;
- goal and opposition;
- physical action / failed action;
- information transaction;
- relationship transaction;
- pre-state and post-state;
- downstream consumer;
- location/time/prop constraints when meaningful;
- merge/split test;
- subtext/exposition constraints.

This phase must replace the current gap where scene projection exists but forward scene invention remains mostly external/legacy.

## Phase G6 — Responsible-Ancestor Replan Loop

When a Scene cannot be made necessary or a Sequence cannot produce its required state delta, do not patch the screenplay text.

Trace failure upward:
- Scene failure -> Sequence transaction reconsideration;
- Sequence failure -> weave/obligation allocation reconsideration;
- Episode overload/flatness -> portfolio selection/defer reconsideration;
- state contradiction -> source/cutoff projection reconsideration.

Each replan must update hashes and invalidate downstream descendants.

## Phase G7 — A2 causal-adoption qualification

Run UL-16 interventions before literary surface judgment.

Required causal probes:
- relationship power/trust/debt intervention;
- information possession/belief intervention;
- event/precondition intervention;
- payoff urgency/horizon intervention;
- social-group intervention where source support exists.

A state change must alter the appropriate planning decision, not merely appear in a receipt or rewritten prose.

## Phase G8 — Architecture-only blind literary qualification

Evaluate neutral Control/Treatment plans separately at:
1. Episode architecture;
2. Sequence architecture;
3. Scene architecture.

Do not render a 35k+ screenplay merely to discover that the episode plan was poor.

Independent blind judgments seal before mapping reveal.

## Phase G9 — Fresh Provider end-to-end qualification

After architecture qualification, execute with real fresh provider contexts and receipts:

`State -> Episode -> Sequence -> Scene -> Surface >=35k -> Reverse Reconstruction -> State Carry`.

No ChatGPT same-conversation imitation is valid primary evidence.

Provider isolation rules from UL-11/UL-12 remain mandatory.

## Phase G10 — Production-scale physicalization

Only after G1–G9 pass:
- integrate the qualified planner into Candidate Main Path;
- run full nonhistorical regression;
- rebuild a new SYNC successor from the verified R53 root;
- independently pass all 12 physical-custody gates;
- archive/deliver 9/9;
- only then consider Production promotion.

## What may be reused

Preserve and reuse:
- R53 physical baseline;
- P07-I4H Recovery R3 base where not contradicted;
- cutoff-safe projection;
- provenance/hash binding;
- weaving validators;
- terminal closure accounting;
- selector/abstention concepts;
- responsible-ancestor replan concepts;
- UL-11/12 provider isolation;
- UL-13 reverse-reconstruction and blind evaluation machinery;
- DB59 Production baseline;
- DB64 R108 as research-support corpus only.

Do not reuse as Candidate forward core:
- fixed 2–3-axis EpisodeSynopsisPlan assumptions;
- one-owner sequence buckets;
- fixed 10-sequence/50-scene generation targets;
- template surface as a substitute for architecture;
- a validator PASS as evidence that a generator is good.

## Engineering rule

Each layer must expose two separately hashed artifacts:
1. **decision artifact** — what was selected and why;
2. **realization artifact** — how that decision was expanded downward.

A layer is not qualified merely because its output validates. Qualification requires causal consumption by the next layer plus counterfactual sensitivity.

## Current boundary

Completed now:
- defect diagnosis and evidence correction;
- new contract design;
- reference planner + schema + local 5/5 executable preflight;
- causal-adoption/provider preregistration.

Not yet complete:
- actual P07 Main-Path adoption;
- real semantic Provider planner implementation;
- A2 causal-adoption evidence;
- architecture blind results;
- live Provider receipts;
- new SYNC physicalization.

Status token:
`SHOWRUNNER_DIRECTION__VALIDATOR_TO_GENERATOR__ADAPTIVE_MULTI_OBLIGATION__ARCHITECTURE_FIRST__CAUSAL_ADOPTION_BEFORE_SURFACE__PROVIDER_THEN_PHYSICALIZE`