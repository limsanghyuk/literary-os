# DB98 Thick Sequence Authoring Execution V1

Document ID: `DB98_THICK_SEQUENCE_AUTHORING_EXECUTION_V1`  
Parent: `DB98_THICK_SEQUENCE_AUTHORING_AUTHORITY_V1`  
Status: `ACTIVE_EXECUTION_CONTRACT`  
Effective date: 2026-08-07

---

## 0. Mission

This is the executable procedure for a new session to reinforce DB98 with source-grounded Thick Sequence records.

The session must be able to start from repository authority + the supplied DB, select the next work, read the original source, author and validate the new layer, save checkpoints, and resume later without relying on chat memory.

---

## 1. Mandatory new-session read order

Before touching drama data, read:

1. `/DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
2. `DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md`
3. active `AUTHORITY_CORRECTION_*` named by the root pointer
4. `THICK_SEQUENCE_AUTHORING_AUTHORITY_V1.md`
5. `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json`
6. this document
7. `THICK_SEQUENCE_AUTHORING_CHECKLIST_V1.json`
8. `CT07R_CURRENT_STATUS.json`
9. `CT-07R_2026-08-07_result.md`
10. `DB98_REINFORCEMENT_WORK_INDEX_V1.json`
11. `THICK_SEQUENCE_NEW_SESSION_BOOTSTRAP_V1.md`

Then resolve the **actual supplied DB package/root** and read its active Stage01–04 core authority/pointer.

If the active package is not the frozen baseline candidate, do not guess. Reconcile by explicit migration or stop with `HOLD_AUTHORITY_DRIFT`.

---

## 2. Baseline preflight before every work

Verify and record:

- package name and SHA256;
- active authored work index name and SHA256;
- total works / episodes / SceneCards;
- active Stage01–04 authority;
- target work source inventory and SourceLock hashes;
- target work Stage01–04 hashes;
- target `authored_seq` count and exact memberships;
- existing CharacterArc / RelationshipArc / CastPresence / CharacterLoad / PayoffCandidate / CrossEpisodeEdge inventory;
- known source defects and authorized holds;
- existing reinforcement checkpoint, if any.

Do not semantically write until the baseline lock is recorded.

---

## 3. Work selection and resume rule

### New work

Use the exact `authority_order` in `DB98_REINFORCEMENT_WORK_INDEX_V1.json` unless the developer explicitly changes order.

Choose the first work that is eligible and not already `FRESH_EXTRACT_PASS` or held.

### Resuming a work

If a checkpoint exists, resume from its exact `next_action` only after verifying:

- authority ID/version;
- baseline hashes;
- authored artifact hashes;
- last completed episode/block;
- no unexplained source or core drift.

Never restart from memory or infer progress from file timestamps.

---

## 4. Processing grain and block rule

### Work block

Process a season in consecutive blocks of **up to 8 episodes**.

### Episode source reading

Before authoring any sequence in an episode, read the **entire episode source in original order**. For long source handling, divide the episode into **four consecutive quarters** and read all four in order.

This four-quarter division is a reading/attention procedure only. It does not create new canonical scene or sequence boundaries.

### Sequence unit

After the full episode is understood, author in existing `seq_index` order, one human `seq_id` at a time.

After every episode: light audit.  
After every up-to-8-episode block: strong audit.  
After the whole work: full work/database audit and fresh extraction.

---

## 5. Source reading protocol for each episode

### Step E1 — orientation, not authorship

Read existing:

- EpisodeArc;
- FullSeriesArc where needed;
- existing thin SequenceBlueprint/authored_seq;
- SceneCards;
- relevant character/relation/payoff/cross-edge indexes.

Use them only to locate context and detect possible links. Do not author Thick meaning by copying them.

### Step E2 — direct source read

Read episode source quarter 1 → quarter 2 → quarter 3 → quarter 4.

Track mentally or in noncanonical scratch notes:

- active characters and changing objectives;
- concrete events;
- changes in who knows/believes what;
- misreadings and concealments;
- plants, callbacks, payoffs, causal links;
- sequence-to-sequence handoffs.

### Step E3 — boundary verification

Using human `member_scene_nos`, re-read the last scene before each sequence boundary and the first scene after it where available.

Do **not** change the boundary. The purpose is to understand what crosses it.

### Step E4 — sequence re-read

For the target sequence, re-read all member scenes in order plus only the adjacent context necessary to understand inbound/outbound relation.

For cross-episode payoff or information references, read the necessary source evidence from the relevant earlier/later episode; do not infer solely from sidecar labels.

---

## 6. Sequence authoring procedure

For every existing `seq_id`, create exactly one `DB98_THICK_SEQUENCE_EXTENSION_V1` record under the active exact schema.

Do not add extra keys.

### S1 — establish `INBOUND`

Before filling fields, answer internally:

- What state arrives from the previous scene/sequence?
- Which character objective, pressure, secret, misunderstanding, promise, threat, clue, or unresolved action is active?

This reasoning need not become a new JSON key; it guides the allowed fields.

### S2 — author `cast[]`

Include functionally relevant participants, not a raw cast roll.

For each:

- canonical/bridged `character`;
- sequence-specific `desire_or_function`;
- correct `participation` enum;
- evidence refs.

Check supporting characters and witnesses; do not collapse the sequence into protagonist-only logic.

### S3 — author `event`

Write one concrete dramatic event/interaction that identifies what the sequence actually realizes.

Reject:

- theme labels;
- generic emotional statements;
- whole-episode summaries;
- descriptions interchangeable across dramas;
- copied dialogue/action prose.

### S4 — author `info_shift[]`

For each meaningful shift identify:

- subject;
- before state;
- after state;
- correct mode;
- member scene numbers;
- evidence.

Use the active enum exactly. `RECALL`, `MISINTERPRET`, `INFER`, and `MISLEAD` are distinct.

If there is no meaningful information shift, use an empty array rather than inventing one.

### S5 — author `plant_payoff[]`

Search existing PayoffCandidate / CrossEpisodeEdge truth first.

Record only source-supported sequence planning use:

- PLANT
- PAYOFF
- CALLBACK
- REVEAL
- ESCALATION
- LINK

Reuse existing references where valid. A sequence may legitimately have no plant/payoff entry.

### S6 — author `scene_notes[]`

Cover every `member_scene_nos` scene exactly once.

Each scene receives 1–8 functional propositions. Every proposition must be actionable and source-grounded.

At least one proposition per scene should, when relevant, make clear one of the following:

- what state it receives;
- what concrete choice/action/conflict it advances;
- what information changes or remains falsely believed;
- what link/plant/payoff pressure it carries;
- what it passes to the next scene;
- why its position matters.

Do not force all six into every scene. Do not pad. Do not write recap paragraphs.

### S7 — establish `OUTBOUND`

After the record is drafted, answer internally:

- What is now different from INBOUND?
- What must the next scene/sequence inherit?

If the answer is unclear, re-read the source and revise only supported fields.

---

## 7. Episode light audit

After all sequences of one episode are authored, run:

### Structural

- exact one Thick record per target `seq_id`;
- exact `seq_index` and `member_scene_nos` match;
- all `scene_notes` scenes covered once;
- schema/enums/FKs parse.

### Semantic

- sequence events are not interchangeable summaries;
- info states are coherent from one sequence to the next;
- links/payoffs do not contradict existing truth;
- cast functions match source participation;
- scene notes explain local function and, where relevant, handoff relation;
- no repeated boilerplate skeleton dominates the episode.

### Placement audit

For every adjacent pair `S_n → S_{n+1}` ask:

- What was handed off?
- Is that handoff visible somewhere in the Thick records?
- Does the next sequence consume, resist, delay, misread, or redirect it?

A missing handoff is a semantic review signal, not permission to invent content.

---

## 8. Block strong audit (up to 8 episodes)

After each block:

1. rerun schema/FK/coverage on the block;
2. compare Stage01–04 hashes against prewrite baseline;
3. review cross-episode info continuity;
4. review plant/payoff/link chains;
5. review character functional continuity;
6. scan repetition/template phrases across sequences;
7. scan source-like long recitation / leakage;
8. validate R5 PlannerInput records for future leakage;
9. validate R8 RuntimeSceneProjection coverage and consumption;
10. write/update checkpoint with artifact hashes and exact next action.

Strong audit failure stops advancement to the next block until repaired or held.

---

## 9. R5 PlannerInput wiring — mandatory companion

For every episode N, create or materialize one `DB98_PLANNER_INPUT_RECORD_V1` using only state available at the planning boundary for N.

Inputs may include:

- previous exit state;
- character states;
- relationship states;
- unresolved payoffs;
- active causal threads;
- remaining episode count;
- subplot debt;
- character debt;
- world constraints.

Human EpisodeArc and Thick Sequence are **targets**, not leaked input.

For N=1, previous exit state is null and only legitimate premise/world constraints may be input.

Leakage from later episode facts is a hard failure.

---

## 10. R8 RuntimeSceneProjection wiring — mandatory companion

Materialize runtime projection without altering canonical SceneCard.

For every projected target scene, expose through the active schema:

- characters / POV;
- character and relationship states;
- event context;
- info context;
- plant/payoff context;
- functional propositions;
- source refs.

This layer proves that the new Thick data has an actual consumer path.

A Thick sidecar with no runtime/planner consumption path is **not reinforced-complete**.

---

## 11. Semantic quality gates

### Q1 Source fidelity

Every semantic statement is directly supported by source or a validated canonical reference whose meaning was source-verified.

### Q2 Specificity

Reject generic text that could be pasted into another work.

### Q3 Information precision

Who knows/believes what before/after must be explicit when an info shift is claimed.

### Q4 Link precision

Links/plants/payoffs must have correct direction and timing. Do not turn thematic similarity into causal/payoff linkage.

### Q5 Character precision

`desire_or_function` must be sequence-specific; presence alone is not enough.

### Q6 Conflict precision

Even though CT-07R did not show Thick superiority on conflict scoring, conflict must still be faithfully represented through event/cast/scene function where source requires it. Do not remove fields based on category scores.

### Q7 Placement relation

The sequence must explain what it inherits and what it hands off sufficiently for downstream planning. This is the experimentally strongest use case.

### Q8 Non-repetition

No mass-produced phrases, identical proposition skeletons, or decorative field filling.

---

## 12. Required automated gates

At minimum run:

- JSON/JSONL parse;
- exact keyset/schema;
- enum/type validation;
- work/episode/seq FK;
- sequence membership equality;
- scene-note exact coverage;
- evidence-ref resolution;
- source hash alignment;
- future leakage check for PlannerInput;
- source-like recitation scan;
- Stage01–04 immutability hashes;
- non-target work hashes;
- fresh extraction parse/hash/coverage.

Automation validates structure and deterministically testable relations. It does not replace semantic reading.

---

## 13. Failure handling

### `HOLD_SOURCE`

Use for missing/corrupted/insufficient source. Do not reconstruct missing dialogue or facts.

### `HOLD_AUTHORITY_DRIFT`

Use for unexplained package/index/schema/source-lock/authority/sequence-membership mismatch.

### `HOLD_SEMANTIC_FAILURE`

Use when authored meaning fails source, specificity, info, link, character, or placement audit.

Reauthor only the failed semantic portion after source reread. Never auto-rewrite meaning to satisfy a validator.

---

## 14. Checkpoint requirements

Checkpoint at minimum:

- work_id;
- baseline package/index SHA;
- authority ID;
- global rollout state;
- last completed episode/block;
- Thick artifact hashes;
- R5/R8 artifact hashes;
- structural gate results;
- semantic audit status;
- non-target immutability status;
- holds/warnings;
- exact `next_action`;
- timestamp.

Checkpoint facts, not chat prose, govern resume.

---

## 15. Work completion

A work is complete only after:

1. all eligible episodes/sequences authored;
2. all episode light audits PASS;
3. all block strong audits PASS;
4. R5/R8 wiring validated;
5. semantic/source audit PASS;
6. Stage01–04 and non-target immutability PASS;
7. work index/checkpoint updated;
8. integrated DB validation PASS;
9. package/fresh extraction completed;
10. extraction revalidation PASS.

Then set the work to `FRESH_EXTRACT_PASS` and advance to the next authority-order work.

---

## 16. What not to infer from CT-07R

Do not infer that:

- SceneCard is obsolete;
- character/goal/conflict are unimportant;
- `cast`, `event`, or `scene_notes` should be dropped;
- `info_shift` or `plant_payoff` alone caused the measured gains;
- five fields are the minimum spec;
- Episode→Sequence is validated.

The five-category table is a **score-category decomposition with all five Thick fields present**, not an ablation.

---

## 17. Separate future diagnostic

After/alongside authorized sequence rollout, Episode→Sequence must be tested independently:

`current EpisodeArc/planning input → generate Thick Sequences → compare with human/source-grounded target → measure missing categories → only then design ThickEpisodeExtension`.

Do not freeze an episode-thick schema before that diagnostic.
