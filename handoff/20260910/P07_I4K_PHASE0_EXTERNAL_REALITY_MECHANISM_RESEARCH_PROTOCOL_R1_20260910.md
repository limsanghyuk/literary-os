# P07-I4K Phase 0 — External Reality Mechanism Research Protocol R1

Date: 2026-09-10
Classification: DEVELOPMENT / PREFORMAL / RESEARCH DESIGN
Status: `READY_FOR_EXTERNAL_RESEARCH__NO_CAUSAL_ENGINE_OUTPUTS`

## 1. Objective

Build a sourced, reusable library of real-world **mechanisms** that can create narrative pressure without importing ready-made plots.

The unit of research is not “an interesting story.”
The unit is a mechanism such as:
- resource scarcity;
- delayed approval;
- responsibility transfer;
- hidden information;
- conflicting professional obligations;
- scheduling collision;
- public reputation cascade;
- repair/maintenance failure;
- regulatory constraint;
- payment / insurance boundary;
- geographic friction;
- social-group exclusion;
- unexpected beneficiary / cost bearer;
- institutional incentive mismatch.

## 2. Phase 0 Questions

1. Which real-world domains produce the richest reusable event mechanisms?
2. Which mechanisms reliably create multi-stakeholder consequences rather than a single-protagonist problem?
3. Which mechanisms naturally expose character values and relationship asymmetries?
4. Which mechanisms create long-horizon threads instead of one-scene incidents?
5. Which external mechanisms become generic or melodramatically convenient when transferred to fiction?
6. How can external evidence be routed into planning without provenance leakage changing provider-facing semantics?
7. What retrieval breadth produces novelty without overloading the planner?

## 3. Research Domains

Minimum Phase 0 domain families:
- family / caregiving;
- workplace / labor / scheduling;
- education;
- medicine / care delivery;
- local administration;
- law / contracts / regulation;
- housing / property / maintenance;
- small business / commerce;
- finance / payment / insurance;
- transport / logistics;
- media / reputation / social media;
- community / neighborhood / civic groups;
- technology / communications;
- environment / weather / infrastructure;
- hobbies / clubs / sports / volunteer organizations.

Phase 0 must sample multiple domains. Do not build the taxonomy from a single profession.

## 4. Source Hierarchy

Use source type according to claim type.

### Rules / procedures
Prefer official, regulatory, institutional or professional documentation.

### Real workflows / failure modes
Prefer professional manuals, institutional guidance, trade or technical sources, and multiple independent reports.

### Social experience / community behavior
Community discussions may be used for mechanism discovery, but should be marked anecdotal and not treated as authoritative fact without corroboration where factual accuracy matters.

### Time-sensitive practice
Use recent sources and preserve retrieval date / source date.

### Historical settings
Use sources appropriate to the target period; do not silently project current rules backwards.

## 5. Retrieval Packet Contract

Every external research item should preserve:

```text
retrieval_packet_id
planning_domain
query_intent
source_title
source_url_or_reference
source_type
publication_date_if_available
retrieval_date
jurisdiction_or_region_if_relevant
mechanism_claim
mechanism_scope
confidence
known_exceptions
non_inference_boundary
candidate_event_primitive
provenance_hash_or_receipt_when_available
```

## 6. Mechanism Abstraction Rule

Required transformation:

`External fact / workflow`
→ `Causal mechanism`
→ `Stakeholder structure`
→ `Event Primitive`
→ `Narrative candidate`

Example pattern:

A professional process has a delayed approval window.

Do NOT store:
“Character X's permit is delayed, so X fights City Hall.”

Store:
- mechanism: institutional delay;
- trigger: incomplete/contested approval;
- blocked resource: access / license / payment / action;
- beneficiaries: status quo / competing claimant;
- harmed party: applicant / dependent stakeholders;
- time pressure: deadline / event / contract;
- escalation: appeal / workaround / publicity / relationship conflict;
- reversal: delay reveals hidden dependency or prior omission.

## 7. Anti-Copy / Originality Boundary

Forbidden:
- copying the sequence of an identifiable real anecdote;
- converting a news article directly into a fictional scene chain;
- reproducing distinctive dialogue / description;
- treating another drama's plot as an Event Primitive.

Allowed:
- abstracting general social, legal, professional, logistical or material causality;
- combining mechanisms from different domains;
- transforming mechanisms through current Character / Relationship state;
- creating novel consequences not present in the source.

## 8. Event Primitive Taxonomy — Initial Candidate Families

Phase 0 should test and revise this initial list:

### RESOURCE
- scarcity;
- allocation;
- dependency;
- shared resource conflict;
- hidden cost transfer.

### TIME
- deadline;
- delay;
- queue;
- schedule collision;
- timing asymmetry;
- irreversible window.

### INFORMATION
- asymmetric knowledge;
- stale record;
- missing record;
- ambiguous evidence;
- disclosure duty;
- confidential information;
- rumor / reputation propagation.

### AUTHORITY
- unclear jurisdiction;
- role mismatch;
- delegated responsibility;
- approval dependency;
- conflicting rules;
- discretionary exception.

### RELATIONSHIP / SOCIAL
- obligation mismatch;
- unequal sacrifice;
- status loss;
- loyalty conflict;
- public/private identity gap;
- group exclusion;
- coalition shift.

### MATERIAL / ENVIRONMENT
- equipment degradation;
- maintenance backlog;
- spatial constraint;
- transport failure;
- weather disruption;
- supply interruption.

### ECONOMIC
- payment delay;
- sunk cost;
- insurance boundary;
- contract penalty;
- incentive mismatch;
- asymmetric bargaining power.

### ETHICAL / PROFESSIONAL
- duty conflict;
- consent boundary;
- confidentiality conflict;
- care vs procedure;
- personal relationship vs professional obligation.

## 9. Multi-Perspective Expansion Protocol

For each mechanism, generate perspective slots before plot selection:
- initiator;
- first noticer;
- direct beneficiary;
- direct harmed party;
- indirect harmed party;
- authority holder;
- person who can block;
- person with hidden information;
- outsider / witness;
- group / institution;
- future stakeholder.

Record how the same event changes meaning for each slot.

Reject an Event Primitive as weak if it only produces one meaningful perspective unless the experiment explicitly tests single-perspective events.

## 10. Connection to Current Literary OS State

Before a mechanism becomes an Event Candidate, query:
- Character State;
- Relationship State;
- Ensemble / Social Ecology;
- Thread / Payoff / Information;
- current Episode need;
- Macro Architecture constraint;
- protected states;
- Source Cutoff / Authority.

The mechanism should be transformed by the existing story state.
The story state should not be distorted merely to fit a retrieved mechanism.

## 11. Phase 0 Deliverables

Required durable outputs before I4K-1 preregistration:
1. external research bibliography / receipt ledger;
2. Reality Mechanism Taxonomy R1;
3. Event Primitive Contract R1;
4. Perspective Expansion Contract R1;
5. Event Candidate Contract R1;
6. Negative / Mismatch event taxonomy;
7. source / anti-copy governance;
8. retrieval routing rules;
9. event evaluation rubric;
10. proposed I4K-1 exact preregistration.

## 12. Phase 0 Exit Gate

Phase 0 may advance to I4K-1 only if:
- multiple domains are represented;
- source receipts are complete enough to audit mechanism claims;
- fact vs abstraction vs generated candidate are explicitly separated;
- no copied plot is required for the mechanism library to function;
- Event Primitive schema maps cleanly to Character / Relationship / Thread / Ensemble state;
- A2 design separates selected semantic payload from global audit provenance;
- evaluation rubric can distinguish causal event richness from spectacle / surprise;
- exact I4K-1 hypotheses and thresholds are frozen before any I4K-1 generation.

## 13. Runtime Boundary

Current container execution remains blocked by repeated `TransportTimeoutError` at minimal-process level.

Phase 0 source study and Hub design may continue without generating causal engine outputs.

Do not claim I4K effect, create experimental Control/Treatment, or change physical package authority until a healthy runtime and a fresh preregistered causal experiment exist.
