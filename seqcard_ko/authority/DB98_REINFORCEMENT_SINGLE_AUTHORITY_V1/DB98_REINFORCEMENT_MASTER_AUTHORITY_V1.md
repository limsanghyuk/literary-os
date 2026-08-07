# DB98 Reinforcement Master Authority V1

Authority ID: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Version: `1.0.0`  
Effective date: `2026-08-07`  
Status: `SEALED_METHOD_AUTHORITY_WITH_ROLLOUT_GATE`  
Scope: existing Korean drama DB98 only (`98 works / 1,814 episodes / 114,371 SceneCards`)  
Created under developer instruction: seal the reinforcement reason, method, schema, validation, progress state, and new-session continuation contract.

---

## 0. Authority boundary and precedence

This authority governs **reinforcement of the existing 98-work analysis database**. It does **not** replace the active Stage01–04 drama-analysis authority.

Precedence:

1. Original source / SourceLock / canonical source map.
2. Active `DRAMA_ANALYSIS_SINGLE_AUTHORITY_*` for Stage01–04 meaning, exact core schemas, source reading, audit, checkpoint, and release.
3. **This document** for DB98 reinforcement purpose, scope, rollout gates, and semantic-extension policy.
4. `schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1.json` for reinforcement record shape.
5. `DB98_REINFORCEMENT_EXECUTION_AND_VALIDATION_V1.md` for execution and gates.
6. `DB98_REINFORCEMENT_WORK_INDEX_V1.json` for current corpus/progress state.

If the active DB package declares a newer core authority than the repository copy, do not guess. Stop with `BASELINE_AUTHORITY_DRIFT` until the core authority pointer and package are reconciled.

**Core Stage01–04 schemas are immutable under this authority.** A Stage01–04 meaning correction requires its own core-authority correction/reauthor run and ledger; it must never be smuggled in as reinforcement.

No automatic canonical promotion is allowed.

---

## 1. Why reinforcement exists

The objective is **not to add more dramas or more decorative analysis layers**. The 98-work corpus is already large enough for the current research question. The objective is to convert a strong descriptive corpus into a database that Literary OS can consume for **top-down planning, generation, discrimination, retrieval, and learning**.

### 1.1 What is already strong

The corpus already contains, at broad coverage:

- full-series arcs,
- episode arcs,
- sequence blueprints,
- SceneCards,
- character arcs,
- relationship arcs,
- local/cross-episode causal edges,
- payoff candidates,
- source locks and audits.

Therefore the problem is not absence of structure output. The problem is that some of the information required to **generate the lower layer from the upper layer** is either missing from the upper-layer contract, stored in sidecars that the planner does not consume, or compressed away.

### 1.2 Confirmatory evidence that fixes the reason for reinforcement

This authority permanently records the following experiment lineage as the technical reason for the work.

#### CT-01 — SceneCard has real signal

Human SceneCard information improves scene generation relative to no/incorrect design. Therefore the scene layer is retained as human GT and evaluation reference.

#### CT-02 — current sequence layer has little incremental value above complete SceneCards

Measured `Δ(B′−A′)=+0.250`, below the preregistered `+0.5` threshold. The current sequence representation did not add enough steering once child SceneCards were already supplied.

#### CT-06H — thin top-down encoding fails

For current thin sequence encoding → generated SceneCard → render:

- `A = 0.000`
- human SceneCard `B = 1.425`
- generated-from-thin `B″ = 0.300`
- mismatched `N″ = 0.000`
- `r = (B″−A)/(B−A) = 0.211`

Preregistered `r <= 0.30` => **NOT ESTABLISHED**. `conflict` and `information` transfer were zero. The failure is scoped to the **current thin encoding**, not to the concept of top-down planning or sequences.

#### CT-07 — deeper design restores top-down signal

A thicker sequence design added the missing planning information:

- `cast[]`
- `event`
- `info_shift`
- `plant_payoff[]`
- `scene_notes[]`

Measured in one 70-render blind batch:

- no design `A = 0.000`
- thin GPT-5 `r = 0.14`
- thin Gemini `r = 0.07`
- **thick → generated card → render `L2-G = 1.150`, `r = 0.807`**
- human SceneCard `B = 1.425`, `r = 1.00`
- **thick direct render `L2-D = 2.325`, `r = 1.63`**
- maximum functional-proposition design `L3 = 4.900`, `r = 3.44`

Decomposition:

- design-depth effect: `+0.74` (dominant),
- generator effect: `−0.07` (small),
- compression/generation loss between thick design and generated SceneCard: `+0.83`.

Therefore the reinforcement thesis is:

> The primary bottleneck exposed by CT-06H/CT-07 is insufficient design depth and lossy cross-layer representation, not lack of corpus size. DB98 reinforcement must reconnect people, concrete events, information movement, plant/payoff logic, and per-scene functional propositions to the planning layer.

### 1.3 CT-07 limitation that remains binding

CT-07 used two works. `r_L2G=0.807` passed, both works passed individually, but the `s7`-excluded sensitivity was `0.692`, and a mismatched **thick** negative-control arm was not included.

Therefore:

- CT-07 is sufficient to authorize this **method authority and replication work**.
- CT-07 is **not yet sufficient to authorize blind 98-work thick authoring rollout**.
- Full rollout requires the global gate in §8.

This restriction is part of the authority and may not be relaxed after seeing rollout data.

---

## 2. Target end state

The 98 works should become not merely `ANALYSIS_COMPLETE`, but:

`ANALYSIS_COMPLETE + LEAKAGE_SAFE + PLANNER_TRAINABLE + RUNTIME_CONSUMABLE + DISCRIMINATOR_READY + HELDOUT_USABLE`.

The intended planning chain is:

```text
Series state
  → Episode planning input
  → Human EpisodeArc output
  → Thick Sequence planning representation
  → [direct render candidate OR revised scene-functional representation]
  → generation
  → comparison with human GT
  → positive/negative preference and discriminator data
```

The reinforcement is a **cross-layer wiring and planning-GT project**.

---

## 3. What will be reinforced

### R0 — Baseline and authority synchronization

Freeze one baseline by package name/SHA, active core authority pointer, work index, manifest, and source-lock inventory before semantic writes.

Operational baseline candidate known at sealing time:

- package: `DB98_STAGE04_98WORKS_EXT6_35_PHASE02_35_GPT_ONEPERCENT_20260807.zip`
- package SHA-256: `99875cfb914cf96b0ee6eab91e6bbe3bb6b13006bbff8e3920c426e5a90274f1`
- works: `98`
- episodes: `1,814`
- SceneCards: `114,371`
- legacy EXT6 complete: `35`
- legacy PHASE02 complete: `35`

A future session must re-verify this candidate against the actually supplied working package before mutation. If a newer authorized DB exists, update the reinforcement work index by explicit migration; never silently change baseline.

### R1 — Data hygiene (98 works, does not count as semantic progress)

Hygiene is mandatory but **must not be counted as new literary judgment**.

Targets include:

- `skin` semantic inconsistency / long source-like recitation,
- `turn_type` free-text taxonomy noise,
- nonstandard `turn_class`,
- degenerate `value_shift` (`from == to`, genre labels, malformed/string values),
- malformed `act_structure[].seq_span`,
- episode-arc field omissions where repair is deterministic or source-verifiable,
- FK/ID/count/index/encoding drift,
- house/company/provider snapshot synchronization.

Rules:

- preserve raw historical value in ledger before normalization,
- deterministic repairs only for truly deterministic defects,
- semantic repair requires source reread and authored correction,
- never erase original source from SourceLock storage,
- public/analysis-only bundles must be checked by **content**, not extension/path alone, for source recitation.

### R2 — Thick Sequence Extension (primary authored reinforcement)

Do not overwrite existing `authored_seq` in V1. Store an append-only reinforcement extension keyed by `seq_id`; a runtime/materialized view may merge thin + extension.

Five CT-07-motivated semantic additions:

1. `cast[]` — who is active, what each wants/does in this sequence.
2. `event` — concrete event/interaction that the sequence must realize.
3. `info_shift[]` — who learns, conceals, loses, reveals, or misreads what information.
4. `plant_payoff[]` — planting, payoff, callback, reveal linkage; reuse existing CrossEpisodeEdge/PayoffCandidate where valid rather than duplicating a second truth system.
5. `scene_notes[]` — per-member-scene **functional propositions**, not prose summary; what must be accomplished in each scene.

The exact extension schema is defined in the schema registry.

### R3 — Character-to-planning connection

The corpus already has character analysis but the planning layer does not consume it consistently. Reinforcement connects:

`CastPresence / CharacterLoad / CharacterArc / RelationshipArc → Thick Sequence cast[] / runtime character-state projection`.

Rules:

- presence can be mechanically proposed from validated cast sidecars where coverage exists,
- desire/function/relationship consequence are semantic and require model authorship/source verification,
- missing EXT6 is not itself a reason to recreate an unused sidecar; collect the information in the consumer-facing reinforcement contract when authorized.

### R4 — Plant/payoff and information-flow connection

Do not create a redundant payoff universe. Prefer references to existing:

- `CrossEpisodeEdge`,
- `PayoffCandidate`,
- candidate disposition,
- source evidence.

New authored content is only the **planning use** of those facts at a sequence/scene boundary when that use is not already represented.

### R5 — Planner input/output pairs

Existing corpus mostly records design outputs. Reassemble time-causal inputs for episode `N` from states available **before N**:

- previous episode `exit_state`,
- active character states,
- relationship states,
- unresolved payoff/callback threads,
- active causal threads,
- remaining episode count,
- subplot/character debt where derivable,
- world constraints.

Target pair:

`PlannerInputRecord(N) → human EpisodeArc(N) + Thick Sequence plan(N)`.

This is principally **reassembly**, not new free-form analysis.

### R6 — Subplot Allocation GT

Create/derive a consumer-facing allocation record only when evidence supports it:

- `active_supporting[]`,
- `target_sub_share`,
- `cross_main`,
- `group_focus`,
- supporting evidence.

Use cast/load/sequence membership as deterministic inputs; semantic line identity and main-crossing are authored/verified.

### R7 — Boundary positive/negative data

Human `member_scene_nos` and sequence boundaries are positive GT. Create synthetic negative examples for discriminator/planner learning without corrupting human GT:

- early boundary,
- late boundary,
- incorrect merge,
- incorrect split,
- shift-before/shift-after variants.

Negative generation must be deterministic/reproducible and stored separately with transformation provenance.

### R8 — Runtime projection and 2-layer candidate

Do not destructively add fields to canonical 9-key SceneCard under this authority.

Instead expose a runtime projection from existing core + reinforcement:

`SceneCard + Thick Sequence + Character/Relation state + payoff/info refs → RuntimeSceneProjection`.

CT-07 `L2-D r=1.63` makes a two-layer candidate (`EpisodeArc + Thick Sequence → direct render`) a required product experiment, not yet a permanent architecture decision.

---

## 4. What is explicitly NOT authorized

- Adding new drama works as a substitute for reinforcement.
- Full 98-work thick authoring before the global replication gate passes.
- Rewriting Stage01–04 just to make reinforcement fields easier to populate.
- Python/regex/LLM scripts generating literary meaning and marking it authored.
- Copying long source dialogue/action into `event`, `scene_notes`, or other semantic fields.
- Treating schema PASS as proof of utility.
- Treating CT-07 two-work result as universal proof without replication.
- Automatic PHASE02 rollout to all 98 works.
- Automatic canonical promotion of reinforcement sidecars.
- Deleting human SceneCards because `L2-D` beat them in one pilot.
- Deleting old thin `authored_seq`; it remains historical/human boundary GT even if its generation role is superseded.

---

## 5. Source and authorship rules

### 5.1 Model-authored meaning

The language model must directly understand source material when authoring semantic additions. Existing Stage01–04, cast, payoff, and edge data may be used as **indexes and candidate evidence**, not as a substitute for source verification when the new field introduces semantic judgment.

### 5.2 Deterministic tooling

Tools may:

- inventory files and source hashes,
- propose mappings already encoded in validated sidecars,
- calculate counts/shares/spans,
- materialize planner-input records from prior-state data,
- generate boundary negative transformations,
- validate JSON/JSONL/schema/FK/coverage/hash,
- package and fresh-extract.

Tools may not author:

- character desire/function,
- concrete event interpretation,
- information-state meaning,
- plant/payoff semantic use,
- scene functional propositions,
- subplot narrative identity.

### 5.3 Evidence

Every authored thick-sequence extension must be traceable to source and/or already locked canonical evidence. Evidence references belong in the extension record; exact source-copy limits remain governed by the active core authority and release policy.

---

## 6. Per-work execution contract after rollout authorization

For each work in `DB98_REINFORCEMENT_WORK_INDEX_V1.json`, in authority order:

```text
BASELINE VERIFY
→ HYGIENE SCAN/REPAIR LEDGER
→ SOURCE / CORE / SIDECAR INVENTORY
→ THICK SEQUENCE AUTHORING (sequence by sequence, source-grounded)
→ CHARACTER / INFO / PAYOFF CONNECTION AUDIT
→ PLANNER INPUT REASSEMBLY
→ SUBPLOT GT (if supported)
→ BOUNDARY NEGATIVE GENERATION
→ STRUCTURAL VALIDATION
→ SEMANTIC / SOURCE AUDIT
→ NON-TARGET IMMUTABILITY
→ WORK CHECKPOINT
→ INTEGRATE
→ DATABASE VALIDATION
→ FRESH EXTRACTION / HASH / PARSE
```

A work is not complete merely because the extension JSON exists.

Completion state requires the execution/validation document's gates and a locked checkpoint.

---

## 7. Quality doctrine

The reinforcement must optimize for **consumer usefulness**, not field density.

A high-quality record is:

- source-grounded,
- sequence-specific,
- character-specific,
- explicit about event and information movement,
- linked to existing payoff/causal truth where applicable,
- decomposed into scene functional propositions,
- non-repetitive,
- usable by a planner/renderer without recovering missing semantics from the source.

Forbidden quality gaming:

- filling every sequence with the same cast count,
- inventing a plant/payoff to meet density,
- summarizing the whole episode into every sequence,
- replacing `event` with a genre label,
- making `info_shift` a generic emotional change,
- making `scene_notes` prose recap rather than functional propositions.

---

## 8. Global rollout gate

### 8.1 Gate required before 98-work Thick Sequence rollout

Run a preregistered CT-07 replication set on **two new works** (recommended diversity: one melodrama/romance, one non-melodrama) and include a **mismatched-thick negative control**.

The exact replication preregistration remains an experiment document, but this authority requires at minimum:

- same core functional-fidelity concept,
- correct thick arm,
- mismatched thick negative control,
- work-level reporting,
- sensitivity reporting,
- no threshold relaxation after results.

### 8.2 Authorization states

Before gate:

`METHOD_SEALED / HYGIENE_AND_REASSEMBLY_ALLOWED / FULL_THICK_ROLLOUT_BLOCKED`.

After replication PASS and developer acceptance:

`FULL_THICK_ROLLOUT_AUTHORIZED`.

After replication FAIL:

`FULL_THICK_ROLLOUT_BLOCKED_REDESIGN_REQUIRED`.

The work index must be updated explicitly when the gate state changes.

---

## 9. Legacy EXT6 and PHASE02 policy

### EXT6

Existing 35-work EXT6 is preserved and may supply cast/presence/load evidence. Remaining EXT6 work is **not an independent completion target** unless its information is consumed by this reinforcement contract or another explicitly authorized consumer.

### PHASE02

Existing PHASE02 is preserved as pilot/research data. It is not automatically extended to 98 works under this authority. Further rollout requires a separate utility decision; reinforcement work must not be blocked merely because a work lacks PHASE02.

---

## 10. State and checkpoint rules

Corpus state is maintained in `DB98_REINFORCEMENT_WORK_INDEX_V1.json`.

Per-work states:

- `WAITING_GLOBAL_ROLLOUT_GATE`
- `READY`
- `IN_PROGRESS`
- `AUTHORED`
- `VALIDATED`
- `INTEGRATED`
- `FRESH_EXTRACT_PASS`
- `HOLD_SOURCE`
- `HOLD_AUTHORITY_DRIFT`
- `HOLD_SEMANTIC_FAILURE`

Every work checkpoint records:

- baseline package/index SHA,
- work id,
- last completed stage,
- authored artifact hashes,
- validation status,
- non-target immutability result,
- next action.

Do not infer progress from chat messages.

---

## 11. New-session contract

A new session must **not reconstruct this method from conversation memory**.

Read in this order:

1. repository-root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`,
2. this master authority,
3. exact schema registry,
4. execution/validation authority,
5. work index,
6. `NEW_SESSION_BOOTSTRAP.md`,
7. only then the active core Stage01–04 authority/pointer and the selected work's checkpoint/source state.

For research lineage, read CT-06H and CT-07 result documents only when needed to audit why the method exists. Their numerical conclusions are already frozen here.

If these documents and a chat instruction conflict, stop and ask the developer which authority to supersede; do not silently merge incompatible rules.

---

## 12. Current sealed state at 2026-08-07

- Core DB target: 98 works / 1,814 episodes / 114,371 SceneCards.
- Legacy EXT6 complete in operational baseline candidate: 35 works.
- Legacy PHASE02 complete in operational baseline candidate: 35 works.
- CT-06H: `r=0.211`, thin top-down not established.
- CT-07: `r_L2G=0.807`, thick top-down established in two-work pilot.
- CT-07 direct thick render: `r=1.63` vs human SceneCard anchor `1.00`.
- CT-07 L3 ceiling: `4.90/5`.
- Full 98-work thick rollout: **BLOCKED pending new-two-work replication + mismatched-thick negative control**.
- Allowed immediately: authority/bootstrap work, baseline synchronization, hygiene, deterministic/reassembly preparation, replication experiment preparation/execution.

### Next authoritative action

`CT07_REPLICATION_WITH_THICK_NEGATIVE_CONTROL`.

After its result, update the global rollout state before beginning bulk thick-sequence reinforcement.

---

## 13. Supersession

This authority may be superseded only by a new version that explicitly states:

- predecessor authority ID,
- reason for change,
- changed rules/schemas,
- migration effect on already reinforced works,
- rollout/checkpoint migration.

Historical files are preserved. Silent in-place semantic-rule changes are forbidden.
