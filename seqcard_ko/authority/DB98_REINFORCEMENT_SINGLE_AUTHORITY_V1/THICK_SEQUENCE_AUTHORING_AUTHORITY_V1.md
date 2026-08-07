# DB98 Thick Sequence Authoring Authority V1

Authority ID: `DB98_THICK_SEQUENCE_AUTHORING_AUTHORITY_V1`  
Parent authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Effective date: 2026-08-07  
Status: `ACTIVE_POST_CT07R_ROLLOUT_AUTHORITY`  
Scope: existing DB98 only (`98 works / 1,814 episodes / 114,371 canonical SceneCards`)

---

## 0. Purpose

This document is the post-CT-07R authority for **source-grounded Thick Sequence reinforcement of the existing DB98**.

A new session must be able to read the repository authority set, select the next work, directly read the original drama source, author the new sequence layer, validate it, checkpoint it, and resume later **without reconstructing decisions from chat history**.

This authority does **not** replace Stage01–04, canonical SceneCard, human `authored_seq`, EpisodeArc, CharacterArc, RelationshipArc, CrossEpisodeEdge, or PayoffCandidate. It adds a consumer-facing planning layer keyed to the existing human sequence boundary.

---

## 1. Precedence and protection

Apply authorities in this order for DB98 Thick Sequence work:

1. original source / SourceLock / active source map;
2. active Stage01–04 drama-analysis authority for core meaning and protected schemas;
3. repository root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`;
4. `DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md` + active authority correction;
5. **this document** for post-CT07R rollout interpretation and authoring policy;
6. `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json` for exact record shape;
7. `THICK_SEQUENCE_AUTHORING_EXECUTION_V1.md` for execution order and validation;
8. current work checkpoint for resume location.

Protected invariants:

- canonical Stage01–04 files are not rewritten by this authority;
- canonical 9-key SceneCard is not expanded or replaced;
- existing `authored_seq.member_scene_nos` remains human positive GT;
- old thin `authored_seq` is not deleted;
- source/source-lock files are not altered;
- no automatic canonical promotion of reinforcement sidecars.

Unexplained authority, baseline, source, sequence-membership, or hash drift stops execution.

---

## 2. Why rollout is now authorized

CT-07R completed independent blind rendering and three-judge blind scoring on 10 anchors / 2 new works / four arms (A, B, T, TN).

Confirmatory result:

- `A = 0.167`
- human SceneCard `B = 3.267`
- correct Thick Sequence `T = 2.700`
- mismatched Thick Sequence `TN = 0.167`
- `B-A = 3.100`
- `r_T = 0.817`
- `D_N = T-TN = +2.533`
- work-level `r_T = 0.755 / 0.886`
- leave-one-out `r_T = 0.727..0.905`
- 3-judge agreement = `95.3%`
- result = `PASS_NOT_STRONG_REPLICATION`

The effect magnitude from CT-07 (`L2-D r=1.63`) did **not** replicate. Do not use `1.63` as the DB98 rollout effect estimate.

The required rollout interpretation is:

> **상향 편향된 조건에서도 음성대조와 분리된 성립.**

The negative control remained below T overall, per work, and in every later category slice. Therefore the observed steering cannot be explained only by giving the renderer more text.

---

## 3. What the experiment says — and does not say

### 3.1 Prespecified structural decomposition

CT-07R separated:

- within-scene elements: `r_T = 0.567`
- placement / neighbor-relation elements: `r_T = 1.386`

Therefore the measured comparative strength of the Thick Sequence layer is **cross-scene placement and relation**, not replacement of human SceneCard's within-scene function.

### 3.2 Post-hoc original five-category decomposition

The sealed key already contained five categories; after scoring the same judgments were decomposed as:

| category | B | T | r_T | D_N |
|---|---:|---:|---:|---:|
| character | 4.500 | 2.667 | 0.542 | +2.333 |
| goal | 4.000 | 2.500 | 0.625 | +2.500 |
| conflict | 3.000 | 1.500 | 0.500 | +1.000 |
| info | 2.667 | 3.667 | **1.429** | +3.667 |
| link | 2.167 | 3.167 | **1.462** | +3.167 |

This is **post-hoc descriptive analysis, not the confirmatory decision rule**.

It establishes an authoring emphasis: `information movement` and `link / callback / payoff / neighboring-scene relation` deserve explicit attention.

It does **not** establish field-level contribution. All five Thick fields were present together. Therefore it is forbidden to infer:

- `cast` is unnecessary;
- `event` is unnecessary;
- `scene_notes` is unnecessary;
- `info_shift` alone caused the info result;
- `plant_payoff` alone caused the link result.

Only a future field-ablation experiment may establish a minimum field set.

---

## 4. Authorized target layer

For every existing human `seq_id`, author one append-only `DB98_THICK_SEQUENCE_EXTENSION_V1` record with the exact active schema.

The five semantic additions must remain **separable**:

1. `cast[]`
2. `event`
3. `info_shift[]`
4. `plant_payoff[]`
5. `scene_notes[]`

Do not fuse these into one prose block. Separability is mandatory so later ablation can determine which information is actually necessary.

---

## 5. Semantic meaning of the five fields

### `cast[]`

Who functionally participates in this sequence and what each participant wants, does, resists, enables, witnesses, or causes.

Do not merely list everyone visible in the scenes. `desire_or_function` is sequence-specific.

### `event`

The concrete dramatic event or interaction the sequence must realize.

It must answer **what actually happens**, not only theme, mood, genre, value shift, or a vague statement such as “conflict deepens.”

### `info_shift[]`

Explicit movement of knowledge, belief, access, inference, concealment, recall, misinterpretation, confirmation, or public knowledge.

Every item identifies a subject and meaningful before/after state. Emotional change alone is not an information shift.

### `plant_payoff[]`

The planning use of a plant, payoff, callback, reveal, escalation, or link.

Existing CrossEpisodeEdge / PayoffCandidate truth is reused when valid. Do not create a second contradictory payoff universe and do not invent a link to satisfy density.

### `scene_notes[]`

Every member scene receives 1–8 **functional propositions**, not recap prose.

A functional proposition states what the scene must accomplish in the sequence. It may express local action, but authoring must pay special attention to:

- what state enters from the previous scene/sequence;
- what changes here;
- what information or dramatic pressure is passed onward;
- what false belief / unresolved question / plant / causal pressure remains active;
- why this scene belongs at this exact position.

The existing schema is not expanded with new keys for these concepts; express them inside the allowed functional propositions where supported.

---

## 6. Source-first authorship doctrine

The highest-priority rule is:

> **The model directly reads, understands, analyzes, and authors from the original drama source.**

Existing SceneCard, SequenceBlueprint, EpisodeArc, cast, character, relation, payoff, and causal data are indexes, comparison targets, and evidence candidates. They are not substitutes for source understanding when writing new semantic meaning.

Python/tools may inventory, hash, join, project deterministic state, validate schema/FK/coverage, build R5/R8 materializations, package, and fresh-extract. Tools must not invent literary meaning.

If the source is missing, damaged, contradictory, or insufficient to support a new semantic judgment, set a hold. Never fabricate dialogue or facts.

---

## 7. Placement-relation doctrine

The rollout must not become “make each scene summary longer.” CT-07R did not validate that strategy.

For every sequence, the author must understand three states:

`INBOUND → SEQUENCE TRANSFORMATION → OUTBOUND`

Ask:

- What pressure, belief, promise, threat, clue, relationship state, or unresolved action enters this sequence?
- What concrete event changes it?
- Who knows/believes what before and after?
- What is planted, paid off, recalled, concealed, or carried forward?
- What must the next scene/sequence inherit?

This cross-boundary reasoning is mandatory even when the final JSON fields remain the same five-field schema.

---

## 8. Mandatory companion wiring

A work is not considered properly reinforced if Thick Sequence records are authored but no consumer path is prepared.

Rollout therefore bundles:

- **R5 `PlannerInputRecord`** — episode-planning inputs reconstructed only from information available at the episode design boundary;
- **R8 `RuntimeSceneProjection`** — deterministic/runtime projection that exposes Thick Sequence + character/relation state + info/payoff context to the renderer without modifying canonical SceneCard.

The semantic author writes Thick Sequence meaning. Deterministic tooling may assemble R5/R8 once their source records exist.

Do not count “sidecar exists but nothing reads it” as completion.

---

## 9. Explicit non-authorizations

This authority does **not** authorize:

- deleting or replacing human SceneCard;
- deleting thin `authored_seq`;
- modifying human sequence boundaries to fit the new layer;
- claiming the five-field set is minimal;
- fusing the five fields;
- automatic field removal based on the five-category score table;
- claiming CT-07 `r=1.63` replicated;
- finalizing a `ThickEpisodeExtension` schema;
- treating Episode→Sequence generation as validated;
- automatic canonical promotion;
- copying long original dialogue/action into the reinforcement records.

Episode→Sequence is a separate, still-unmeasured invention rung and requires its own diagnostic before an episode-thick schema is frozen.

---

## 10. Completion doctrine

A work reaches reinforcement completion only after:

`SOURCE READ → THICK AUTHORING → EPISODE AUDIT → R5/R8 WIRING → STRUCTURAL VALIDATION → SEMANTIC/SOURCE AUDIT → NON-TARGET IMMUTABILITY → CHECKPOINT → INTEGRATION → FRESH EXTRACTION VALIDATION`

The exact execution is defined by `THICK_SEQUENCE_AUTHORING_EXECUTION_V1.md`.

Legacy EXT6/PHASE02 completion is useful evidence but is not Thick Sequence completion.

---

## 11. Holds

Use:

- `HOLD_SOURCE` — source defect or insufficient source support;
- `HOLD_AUTHORITY_DRIFT` — unexplained authority/baseline/schema/sequence drift;
- `HOLD_SEMANTIC_FAILURE` — authored meaning fails source/quality audit.

Known authorized source holds remain in force. This authority cannot silently clear them.

---

## 12. Future experiments that remain open

1. field ablation to derive the minimum Thick field specification;
2. Episode→Sequence diagnostic and later episode-layer design;
3. robustness rerun under the alternate CT-07R padding/materialization rule if desired;
4. CT-03 style/irregularity follow-up.

These experiments may refine future versions, but they do not block the currently authorized five-field separable DB98 Thick Sequence rollout.
