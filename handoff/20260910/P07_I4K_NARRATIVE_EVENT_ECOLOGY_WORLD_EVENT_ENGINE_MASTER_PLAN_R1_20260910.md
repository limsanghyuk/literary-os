# P07-I4K Narrative Event Ecology / World Event Engine — Research Master Plan R1

Date: 2026-09-10
Classification: DEVELOPMENT / PREFORMAL / NEW MAJOR RESEARCH TRACK
Adoption state: `ADOPTED_AS_NEXT_MAJOR_RESEARCH_TRACK__PHASE0_DESIGN_AND_EXTERNAL_RESEARCH_ALLOWED__CAUSAL_EXECUTION_REQUIRES_HEALTHY_RUNTIME_AND_FRESH_PREREG`

## 1. PURPOSE

P07-I4K elevates Literary OS from a system that primarily **plans, realizes, preserves and repairs narrative state** into a higher-order system that can **discover, generate, simulate, select and integrate new event possibilities** from the interaction of characters, relationships, institutions, environments and real-world mechanisms.

The target is not a generic idea generator and not a prompt that produces “20 plot ideas.”

The target capability is:

> Given the current Series / Episode / Character / Relationship / Group / Thread / World state, generate multiple causally plausible new events from different perspectives, estimate how those events propagate through the social system, and select events that create strong narrative pressure without violating existing authority, continuity, character truth or long-horizon sustainability.

Working system name:
`Narrative Event Ecology Engine (서사 사건 생태 엔진)`

Higher-level product direction:
`Narrative Showrunner Engine (서사 쇼러너 엔진)`

---

## 2. WHY THIS TRACK IS NEEDED

Current Literary OS already has important lower and middle layers:
- Series → Episode → Sequence → Scene hierarchy;
- Character State;
- Relationship State;
- Ensemble / Social Ecology;
- Thread / Payoff / Information management;
- Sequence Function;
- Scene Realization;
- Negative / Mismatch;
- State Carry;
- Responsible-Ancestor bidirectional repair;
- Authority / provenance / preregistration / regression / package governance.

These capabilities answer:
- what is true now;
- what must be preserved;
- what each narrative layer must accomplish;
- how a chosen event should be realized;
- where to backpropagate when a realization fails.

The remaining higher-order gap is:

> **What new thing should happen next, and why should that event emerge from these people and this world rather than from generic plot convenience?**

I4K is designed to close that gap.

---

## 3. CORE PRINCIPLE — SEARCH REALITY MECHANISMS, NOT STORY PLOTS

External Search / Retrieval(외부 검색)은 “재미있는 드라마 사건”이나 기존 작품의 줄거리를 수집하는 용도로 사용하지 않는다.

Primary external-search purpose:
`Reality Mechanism Mining (현실 작동원리 채굴)`

Examples of reality mechanisms:
- scarce resources / allocation conflict;
- institutional delay;
- information asymmetry;
- authority mismatch;
- procedural deadline;
- responsibility transfer;
- reputation contagion;
- labor scheduling conflict;
- maintenance failure;
- insurance / contract boundary;
- family obligation conflict;
- legal / administrative constraint;
- social-media amplification;
- geographic / transportation friction;
- weather / environmental disruption;
- professional ethics conflict;
- hidden cost shifted to another stakeholder;
- cascading consequence from a small operational mistake.

External facts must be transformed into abstract Event Mechanisms before they become story candidates.

Do not directly copy external anecdotes or plot sequences into literary output.

---

## 4. PROPOSED HIGH-LEVEL ARCHITECTURE

### Layer K1 — World Reality Retrieval (현실세계 검색층)

Input:
- current world / occupation / institution / location / social context;
- current episode pressure;
- current unresolved threads;
- active characters / groups.

Output:
- sourced real-world mechanisms;
- rules / constraints / typical failure modes;
- stakeholder maps;
- uncertainty / source confidence;
- source-cutoff and retrieval receipts.

Search domains may include:
- occupation / workplace;
- family / caregiving;
- law / regulation;
- medicine / education;
- commerce / finance;
- local government / public administration;
- housing / infrastructure;
- transportation;
- technology;
- media / social media;
- regional custom / culture;
- clubs / hobbies / sports;
- social services;
- disaster / weather / environment;
- community organizations;
- labor and scheduling;
- everyday logistics.

### Layer K2 — Event Primitive Extractor (사건 원형 추출기)

Convert sourced mechanisms into reusable primitives instead of storing plot.

Minimum Event Primitive fields:
- `primitive_id`
- `mechanism_type`
- `trigger`
- `affected_resource`
- `stakeholders`
- `institutional_rule`
- `hidden_information`
- `time_pressure`
- `social_cost`
- `economic_cost`
- `who_notices_first`
- `who_benefits`
- `who_pays_cost`
- `who_can_block`
- `possible_escalations`
- `possible_reversals`
- `uncertainty`
- `source_receipts`

### Layer K3 — Perspective Expander (다중시점 확장기)

For each event primitive, separately model perspectives of:
- protagonist;
- counterpart / antagonist;
- family;
- friend / colleague;
- subordinate / superior;
- institution;
- affected third party;
- beneficiary;
- harmed party;
- community / group;
- media / public opinion when relevant;
- regulator / administrator when relevant.

Goal:
One event must not have only one narrative meaning.

### Layer K4 — Character / Relationship Event Generator (인물·관계 사건 생성기)

Generate events from internal state even without external search.

Internal sources:
- desire;
- fear;
- hidden information;
- false belief;
- promise / debt;
- jealousy;
- loyalty conflict;
- shame;
- ambition;
- dependency;
- unresolved apology;
- status competition;
- moral disagreement;
- relationship asymmetry.

### Layer K5 — Social / Institutional Event Generator (사회·제도 사건 생성기)

Generate external pressures from:
- workplace processes;
- institutional rules;
- market conditions;
- public systems;
- community behavior;
- collective decisions;
- resource limitations;
- third-party interests.

### Layer K6 — Environmental / Chance Event Generator (환경·우연 사건 생성기)

Generate bounded non-deus-ex-machina disturbances:
- weather;
- equipment failure;
- transportation disruption;
- accidental encounter;
- lost / delayed object;
- scheduling collision;
- physical-space constraint.

Chance events must create pressure; they must not conveniently solve protected narrative problems.

### Layer K7 — Event Ecology Simulator (사건 생태 시뮬레이터)

Take an Event Candidate and simulate propagation through Character / Relationship / Group / Institution state.

For each candidate estimate:
- first-order consequence;
- second-order consequence;
- who changes behavior;
- who gains / loses information;
- which relationship becomes pressured;
- which existing thread is activated;
- whether a new thread is justified;
- whether ensemble participation expands or collapses;
- temporal plausibility;
- required setup cost;
- overclosure risk;
- future episode potential;
- protected-state violations.

### Layer K8 — Narrative Event Selector (서사 사건 선택기)

Rank event candidates not by spectacle but by narrative value.

Candidate dimensions:
- character causality;
- relationship pressure;
- multi-perspective richness;
- ensemble activation;
- social-world plausibility;
- novelty / non-generic specificity;
- thread utility;
- episode architecture fit;
- future sustainability;
- cost of setup;
- risk of coincidence / convenience;
- risk of protagonist overconcentration;
- risk of over-resolution;
- authority / continuity safety.

### Layer K9 — Responsible-Ancestor Integration (책임 상위계층 편입)

Selected events must enter the existing hierarchy at the correct level:
Series → Episode → Sequence → Scene.

If a Scene realization exposes a bad event premise, repair must backpropagate to the Event Candidate / Episode design rather than repeatedly polishing the Scene.

---

## 5. FOUR EVENT ORIGINS — REQUIRED DIVERSITY

Every event-candidate pool should deliberately cover four origins:

1. `INTERNAL_CHARACTER_EVENT`
   - generated by desire, fear, decision, mistake, secrecy, ambition, belief.

2. `RELATIONSHIP_EVENT`
   - generated by promise, information asymmetry, obligation, jealousy, trust, debt, status shift.

3. `SOCIAL_INSTITUTIONAL_EVENT`
   - generated by workplace, law, school, hospital, market, administration, community, media, organization.

4. `ENVIRONMENTAL_CHANCE_EVENT`
   - generated by environment, logistics, weather, failure, timing or chance, with strict anti-convenience rules.

A strong episode should normally combine more than one origin rather than use only an external incident.

---

## 6. EVENT CANDIDATE CONTRACT R1

Proposed minimum contract:

```text
event_candidate_id
source_origin
reality_mechanism_id(s)
current_state_dependencies
trigger
initiator
first_noticer
stakeholder_map
character_desires_activated
relationship_pressures
resource_or_rule_constraint
information_asymmetry
physical_world_consequence
social_consequence
institutional_consequence
possible_escalation_chain
possible_reversal
threads_activated
new_thread_justification
protected_states
responsible_ancestor
sequence_opportunities
scene_opportunities
future_episode_potential
overclosure_risk
coincidence_risk
genericity_risk
source_receipts
claim_confidence
```

No event may be admitted solely because it is surprising.

---

## 7. RELATION TO EXISTING 8 RETRIEVAL VIEWS

I4K should not create a competing database ontology. It should consume and enrich the existing views:

- Macro Architecture → determines long-horizon event need;
- Character State → constrains character-caused events;
- Relationship State → creates interpersonal pressure;
- Ensemble / Social Ecology → identifies affected / excluded / empowered groups;
- Thread / Payoff / Information → checks activation / carry / closure;
- Sequence Function → assigns selected events to episode functions;
- Scene Realization → lowers event into playable scenes;
- Negative / Mismatch → rejects generic, convenient, continuity-breaking or socially implausible events.

I4K Event Primitives are a new planning resource, not a replacement for these views.

---

## 8. RELATION TO 9 CONTRACTS

I4K must obey the existing Consumer / Governance logic:

- C1 Decision / Transformation: an event primitive must change an actual planning decision;
- C2 Scope / Granularity: distinguish Series/Arc/Episode/Sequence/Scene/Character/Relationship/Group event scope;
- C3 Temporal / State: entry, trigger, delta, exit, unresolved carry and next constraint must remain distinct;
- C4 Provenance / Derivation: distinguish sourced reality facts, derived mechanism, generated event candidate and runtime projection;
- C5 Epistemic Status: support SUPPORTED / PARTIAL / UNKNOWN / CONFLICTED rather than fabricate certainty;
- A1 Routing: only relevant mechanisms reach the planning question;
- A2 Causal Adoption: selected mechanisms must measurably change event planning, while irrelevant unselected retrieval must not change provider-facing semantics;
- G1 Authority / Source Cutoff / Version: bind research sources and candidate versions;
- G2 Diagnostic / Responsible-Ancestor Repair: route failed event realization back to the smallest responsible upstream decision.

DB64 A2 provenance-invariance HOLD is directly relevant: I4K must not repeat the mistake of injecting global retrieval provenance into provider-facing semantic payloads.

---

## 9. EXTERNAL SEARCH GOVERNANCE

### 9.1 Search is evidence, not authority over story
External sources explain mechanisms and constraints. They do not dictate plot.

### 9.2 Source classes
Prefer:
- official / regulatory / institutional documents for rules;
- reputable professional / technical sources for workflow;
- multiple sources for contested social behavior;
- recent sources where practice is time-sensitive;
- historical sources when period setting requires them.

Community reports may be used for candidate mechanism discovery, but must not silently become factual authority.

### 9.3 Search packet
Each retrieval packet should preserve:
- query intent;
- source URL / title / date;
- retrieval date;
- extracted mechanism claim;
- confidence;
- scope;
- what must NOT be inferred;
- abstraction into Event Primitive.

### 9.4 Anti-copy boundary
Do not copy identifiable story plots, unique anecdotal sequences, or copyrighted dramatic expression into candidate generation.

The desired output is generalized social / institutional / material causality.

---

## 10. RESEARCH QUESTIONS

### RQ1 — Event Diversity
Can an Event Ecology Engine produce more causally distinct, perspective-diverse event candidates than a strong foundation model asked directly for episode ideas?

### RQ2 — Character / Relationship Causality
Do selected events arise more often from existing character and relationship state rather than arbitrary external intrusion?

### RQ3 — Social-World Richness
Does Reality Mechanism Mining improve institutional plausibility, stakeholder richness and social ecology without making dialogue expository?

### RQ4 — Ensemble Distribution
Does multi-perspective event simulation reduce protagonist overconcentration and activate more meaningful ensemble roles?

### RQ5 — Long-Horizon Utility
Do Event Ecology candidates produce stronger unresolved carry and future episode potential without premature payoff closure?

### RQ6 — Genericity
Does primitive-based mechanism abstraction reduce generic “accident / misunderstanding / surprise visitor” plotting compared with direct idea generation?

### RQ7 — Search Value
Does external reality retrieval add measurable value beyond internal Character / Relationship event generation, and in which domains?

### RQ8 — Model Scaling Robustness
When the foundation model becomes stronger, does I4K still add value through state governance, perspective coverage, source grounding and selection discipline rather than low-level prose repair?

---

## 11. PROPOSED EXPERIMENT PROGRAM

### I4K-0 — External Research / Architecture Qualification
Classification: Knowledge / Design only.

Goals:
- survey agent-world simulation, narrative planning, social simulation and retrieval-grounded event generation;
- build Reality Mechanism taxonomy;
- freeze Event Primitive Contract R1;
- define external-search provenance rules;
- define anti-copy / source-cutoff rules;
- define event evaluation rubric.

No engine promotion claim.

### I4K-1 — Event Candidate Generation Effect
Fresh synthetic world, no whole-episode rendering required initially.

Control:
Strong model receives current Literary OS state and request for event candidates, without Event Ecology layers.

Treatment:
Same model/state receives structured Event Ecology pipeline:
Reality Mechanism → Event Primitive → Perspective Expansion → Event Simulation → Selection.

Candidate pool target:
minimum 30 candidates per arm before selection.

Primary dimensions:
- causal fit to current state;
- multi-perspective richness;
- institutional / social plausibility;
- non-generic specificity;
- ensemble activation;
- future sustainability;
- coincidence/convenience risk.

### I4K-2 — Search Ablation
Arms:
- internal state only;
- external reality mechanisms only;
- combined internal + external.

Purpose:
measure whether external search adds real narrative value and where it harms originality or coherence.

### I4K-3 — Event-to-Sequence Causal Adoption
Take selected event candidates and lower them into Sequence Plans.

Test:
selected Event Primitive mutation must alter downstream plan;
irrelevant unselected retrieval must not alter provider-facing semantic plan.

This directly incorporates the A2 invariance lesson from DB64.

### I4K-4 — Whole-Episode Prospective Validation
Only after I4K-1/2/3 pass.

Generate fresh whole episodes under fixed episode goals:
- Control: existing Literary OS without Event Ecology;
- Treatment: Literary OS + qualified Event Ecology.

Evaluate:
- event originality;
- causal inevitability after the fact;
- relationship pressure;
- ensemble/social texture;
- character consistency;
- thread sustainability;
- temporal plausibility;
- scene playability;
- whole-episode craft;
- over-resolution;
- long-horizon trajectory.

### I4K-5 — Human / Independent Gate
Fresh blind human evaluation if available.
No Production or Formal promotion before this stage and all required regression / package gates.

---

## 12. FIRST EXPERIMENT PASS / FAIL DESIGN DIRECTION

Exact numerical thresholds must be preregistered only after Phase 0 calibration and before seeing I4K-1 outputs.

Noncompensatory hard gates should include:
- continuity violation = 0;
- protected-state critical violation = 0;
- fabricated external rule presented as sourced fact = 0;
- direct copied external anecdotal plot = 0;
- event candidate without causal dependency on current state above permitted exploratory quota = fail;
- selected event with deus-ex-machina resolution = fail;
- source receipt missing for a claimed external mechanism = fail;
- irrelevant retrieval changes provider-facing semantic input in A2 invariance test = fail.

Effect gates should measure improvement over a direct-generation Control rather than absolute aesthetic score alone.

---

## 13. AGENT USE — LIMITED AND PURPOSEFUL

I4K may use temporary simulation agents for major characters / groups, but does not require every named character to become a persistent autonomous agent.

Agent simulation purpose:
- generate independent action preferences;
- expose perspective conflict;
- test event propagation;
- identify second-order consequences;
- detect unexpected but state-consistent interactions.

World / Game-Master-like layer purpose:
- enforce physical and institutional constraints;
- adjudicate consequences;
- prevent impossible or convenient outcomes;
- maintain authoritative state.

The Narrative Showrunner layer remains responsible for choosing which simulated event belongs in the authored series.

---

## 14. MODEL-SCALING STRATEGY

I4K must be designed so stronger foundation models reduce low-level scaffolding rather than obsolete the OS.

Model-responsible:
- proposing actions;
- interpreting character motives;
- generating candidate consequences;
- writing natural prose/dialogue when requested.

Literary-OS-responsible:
- authority;
- state;
- source / provenance;
- retrieval routing;
- candidate diversity requirements;
- perspective coverage;
- causal adoption;
- protected-state constraints;
- selection;
- regression;
- long-horizon continuity;
- experiment governance.

The architectural objective is a thinner but higher-level OS as models improve.

---

## 15. RELATION TO CURRENT I4J

I4J remains the currently preregistered active prospective experiment and is blocked only by unhealthy runtime transport.

I4K does NOT rewrite, cancel or reinterpret I4J.

Allowed now while runtime is unhealthy:
- I4K Phase 0 literature / external research;
- architecture design;
- taxonomy design;
- evaluation-rubric design;
- source-governance design;
- preregistration drafting.

Forbidden until healthy runtime and fresh preregistration:
- causal I4K engine outputs;
- fresh Treatment / Control claims;
- Production promotion;
- Formal count change;
- package-authority promotion.

Recommended sequence:
1. continue I4K-0 design/research in parallel with runtime outage;
2. when runtime becomes healthy, resume and close preregistered I4J J1 first unless governance explicitly changes the order before any I4J fresh output;
3. freeze I4K-1 exact preregistration and run Event Candidate Generation Effect;
4. progress through I4K-2 / I4K-3 / I4K-4 only after preceding gates pass.

---

## 16. PHYSICAL PACKAGE BOUNDARY

This Master Plan is Hub research/governance evidence only.

It does not modify:
- Active Engine C2;
- DB59 bytes;
- Production ENG:R47;
- Formal scored count 137;
- R140 state;
- current Research Sync R2 physical package bytes.

Therefore no new 5-Part / 9-Package physical authority is declared by this document alone.

Any future I4K code/data change that affects package content must follow the user-mandated changed-transport rebuild, audit and developer-delivery rule before physical authority changes.

---

## 17. ADOPTION VERDICT

`P07-I4K NARRATIVE EVENT ECOLOGY / WORLD EVENT ENGINE` is adopted as the next major Literary OS capability-development track.

Research status:
`ADOPTED__PHASE0_EXTERNAL_RESEARCH_AND_DESIGN_READY__CAUSAL_EXPERIMENT_NOT_YET_PREREGISTERED__NO_ENGINE_PROMOTION`

Strategic objective:
Transform Literary OS from a narrative state/control system into a model-agnostic **Narrative Showrunner Operating System** capable of generating and selecting diverse, socially grounded, character-causal events while preserving authority, continuity and long-horizon narrative design.
