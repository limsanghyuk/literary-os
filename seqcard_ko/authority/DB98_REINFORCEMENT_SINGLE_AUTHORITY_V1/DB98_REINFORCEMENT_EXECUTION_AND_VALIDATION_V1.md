# DB98 Reinforcement Execution and Validation V1

Authority parent: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Version: `1.0.0`  
Status: `SEALED_EXECUTION_CONTRACT_WITH_GLOBAL_ROLLOUT_GATE`  
Effective date: `2026-08-07`

---

## 0. Purpose

This document converts the master authority into a repeatable per-session/per-work procedure. A new session must be able to continue the 98-work reinforcement without reconstructing decisions from chat history.

This is a reinforcement workflow, not a replacement for the active Stage01–04 authority.

---

## 1. Session start gate

Before any write:

1. Read repository-root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`.
2. Read the master authority.
3. Read the exact reinforcement schema registry.
4. Read `DB98_REINFORCEMENT_WORK_INDEX_V1.json`.
5. Read `NEW_SESSION_BOOTSTRAP.md`.
6. Resolve the actually supplied DB root/package.
7. Verify package SHA, active work index SHA, work/episode/SceneCard totals, active core authority pointer, and source-hold state.
8. If any mismatch is unexplained, stop with `BASELINE_DRIFT` or `BASELINE_AUTHORITY_DRIFT`.

Never start from a remembered work count or a previous chat claim.

---

## 2. Global rollout gate

### 2.1 Current state at V1 seal

`FULL_THICK_ROLLOUT_BLOCKED_PENDING_CT07_REPLICATION`.

Allowed before replication PASS:

- baseline synchronization,
- authority synchronization,
- leakage/data-hygiene audits,
- deterministic/nonsemantic normalization with ledger,
- planner-input reassembly prototypes,
- CT-07 replication preregistration and execution,
- thick-negative-control experiment,
- tooling/validator implementation.

Not allowed before replication PASS:

- bulk authored thick-sequence extensions across 98 works,
- claiming a work is reinforced-complete because only legacy EXT6/PHASE02 exists,
- canonical promotion of reinforcement records.

### 2.2 Replication acceptance

The replication set must use two new works and include a mismatched-thick negative control. Thresholds and scoring must be preregistered before generation. The authority does not permit post-result relaxation.

After PASS + developer acceptance, update:

- work index `global_rollout_state`,
- authority pointer `rollout_state`,
- a dated decision record/commit.

Only then may bulk authored thick reinforcement begin.

---

## 3. Work selection order

After global rollout authorization, process works in the exact `authority_order` of `DB98_REINFORCEMENT_WORK_INDEX_V1.json` unless the developer explicitly changes order.

Do not infer order from filename sorting, provider history, or old EXT6 queues.

A selected work must have a per-work checkpoint before semantic authoring begins.

---

## 4. Per-work preparation

For work `W`:

### 4.1 Baseline lock

Record:

- baseline package SHA,
- active work index SHA,
- active core authority ID/path,
- all Stage01–04 file hashes for W,
- source/source-lock hashes,
- existing EXT6/PHASE02 presence,
- existing cast/load/chararc/relarc/edge/payoff inventories,
- known source limitations/holds.

### 4.2 Non-target immutability baseline

Before writes, compute hashes for:

- all W Stage01–04 core files,
- all non-target works if integrating into a full DB,
- authority files,
- source locks.

Reinforcement V1 is append-only except explicit hygiene-ledger changes.

### 4.3 Hygiene scan

Scan W and relevant global records for:

- long/source-like `skin`,
- malformed/noncanonical turn taxonomy,
- degenerate/malformed `value_shift`,
- malformed act `seq_span`,
- episode-arc omission,
- broken FK/member coverage,
- encoding/JSON issues.

Hygiene fixes must be separately ledgered and must not be counted as thick semantic authoring.

---

## 5. Thick Sequence authoring

### 5.1 Unit of work

The semantic authoring unit is one existing sequence, but source understanding is episode-aware and series-aware where required for payoff/information context.

Existing sequence membership is treated as human positive GT unless a separate core correction is authorized.

### 5.2 Read order

For each sequence:

1. Read the sequence's member scenes in original source order.
2. Read immediately necessary adjacent context.
3. Read existing SceneCards/SequenceBlueprint/EpisodeArc as index and prior GT.
4. Read cast/character/relation/payoff/cross-edge records as candidate evidence.
5. Return to source whenever a semantic addition is not directly supported.
6. Author only the five thick additions and evidence refs.

Do not copy an existing summary into a new field merely to fill it.

### 5.3 `cast[]`

Record the characters/groups whose participation matters to the sequence function.

Each item must state:

- canonical/bridged identity,
- desire or function in this sequence,
- participation class,
- evidence.

Presence may be proposed from validated cast sidecars; `desire_or_function` must be semantically authored/verified.

### 5.4 `event`

Write the concrete dramatic event/interaction the sequence realizes.

Reject:

- genre labels,
- episode-wide summaries,
- vague values such as "conflict deepens",
- copied source prose.

The event should allow a downstream planner/renderer to know **what must actually happen**.

### 5.5 `info_shift[]`

Track explicit changes in who knows/believes/conceals/reveals what.

Emotional change is not information shift unless it changes knowledge/belief/access.

If no meaningful information change occurs, an empty array is preferred over invented content. Use `NO_CHANGE_EXPLICIT` only when the absence itself is functionally important and source-supported.

### 5.6 `plant_payoff[]`

First search existing payoff/cross-edge truth.

Prefer stable references to existing records. Create a new planning-use statement only when the sequence-level function is not represented elsewhere.

Never create a payoff solely to satisfy density.

### 5.7 `scene_notes[]`

Cover **every** `member_scene_nos` scene exactly once.

Each scene gets 1–8 functional propositions that state what the scene must accomplish, for example:

- force X to make a specific choice,
- move fact Y from A-only to A+B knowledge,
- plant object Z without exposing its later use,
- reverse the negotiation advantage,
- preserve a false belief while changing the audience's information.

Do not write prose recap. Do not quote dialogue.

---

## 6. Planner-input reassembly

Planner-input records are generated only from information available before the target episode's design boundary.

For episode N:

- N=1: no previous exit state; use series premise/world constraints that are legitimately pre-design inputs.
- N>1: previous episode exit state, unresolved threads, character/relationship states, and already planted payoff state may be used.
- Facts first introduced later than N must not leak into input.

The human EpisodeArc/Thick Sequence records are target outputs, not input features.

A leakage audit is mandatory.

---

## 7. Subplot Allocation GT

Create only when evidence supports a separable supporting line.

Deterministic inputs may estimate scene/time share and active supporting cast. Semantic decisions such as line identity and `cross_main` require authored verification.

A work is not failed merely because a given episode has no separable subplot record.

---

## 8. Boundary contrast generation

Boundary negatives are synthetic, reproducible, and isolated from human GT.

Allowed negative classes:

- EARLY,
- LATE,
- MERGE,
- SPLIT,
- SHIFT_BEFORE,
- SHIFT_AFTER.

Every negative record stores seed, transformation, and validity checks. It may not alter `authored_seq` or human `member_scene_nos`.

---

## 9. Structural validation gates

A work cannot reach `VALIDATED` unless all applicable gates pass.

### G-SCHEMA

- JSON/JSONL parse PASS,
- exact required keyset PASS,
- type/enums PASS,
- no forbidden extra keys.

### G-FK

- work/episode/seq IDs exist,
- `seq_id`, `seq_index`, `member_scene_nos` match human authored_seq,
- all scene-note scene numbers belong to the sequence.

### G-COVERAGE

- one thick extension per targeted sequence,
- `scene_notes` exact member-scene coverage,
- no duplicate/missing scene notes,
- no silent episode omission.

### G-EVIDENCE

- every semantic thick record has evidence,
- source/evidence refs resolve,
- source hashes align with baseline/source lock.

### G-LEAKAGE

- planner inputs contain no future target facts,
- analysis-only/public output contains no unintended source recitation,
- long-string/source similarity scan PASS or explicit internal-only hold.

### G-IMMUTABILITY

- Stage01–04 unchanged unless a separately authorized correction ledger exists,
- non-target works unchanged,
- source/source-lock unchanged.

### G-HYGIENE

- every changed legacy field has ledger entry,
- raw hash is preserved,
- semantic repairs cite source verification.

---

## 10. Semantic quality gates

### G-SPECIFICITY

Reject generic or cross-work interchangeable text in `event`, desires, info shifts, or scene notes.

### G-CHARACTER

- cast list matches actual functional participation,
- no protagonist-only collapse when supporting characters carry the sequence,
- desires/functions distinguish active vs witness/support roles.

### G-INFO

- information states have a clear subject and before/after difference,
- reveal/conceal/mislead semantics match source,
- emotional value shift is not mislabeled as knowledge shift.

### G-PLANT_PAYOFF

- no invented links,
- existing edge/payoff refs used when available,
- callback/plant/payoff timing is correct.

### G-SCENE_FUNCTION

- every scene proposition is actionable/functional,
- the list collectively explains why those scenes belong in the sequence,
- no episode-summary repetition across scenes.

### G-REPETITION

Run cross-sequence and cross-work phrase/skeleton review. Repeated schema phrasing is allowed only where functionally necessary; repeated semantic content is not.

### G-CONSUMER_READINESS

A reviewer/model given the thick sequence record should not need the source just to discover basic active characters, concrete event, central information movement, payoff connection, or per-scene function.

This gate is qualitative and must be independently audited.

---

## 11. Work checkpoint states

Use only these states:

1. `WAITING_GLOBAL_ROLLOUT_GATE`
2. `READY`
3. `IN_PROGRESS`
4. `AUTHORED`
5. `VALIDATED`
6. `INTEGRATED`
7. `FRESH_EXTRACT_PASS`
8. `HOLD_SOURCE`
9. `HOLD_AUTHORITY_DRIFT`
10. `HOLD_SEMANTIC_FAILURE`

State transitions must be backed by files/hashes, not chat claims.

---

## 12. Integration and database gates

After a work reaches `VALIDATED`:

1. append reinforcement sidecars/ledgers/checkpoints,
2. update work index,
3. update reinforcement manifest/pointer if global state changed,
4. rerun active core DB validators,
5. rerun reinforcement structural/semantic validators,
6. perform non-target hash comparison,
7. package full DB if required,
8. fresh-extract into a new path,
9. rerun parse/FK/hash/coverage gates from extraction,
10. only then set `FRESH_EXTRACT_PASS`.

A ZIP that was not fresh-extracted and revalidated is not a final developer handoff.

---

## 13. Work completion report minimum

For each completed work report:

- work id / episodes / sequences / scenes,
- baseline SHA and authority IDs,
- hygiene changes count and ledger path,
- thick records count,
- cast/info/plant-payoff/scene-note coverage,
- planner-input records count,
- subplot records count,
- boundary negative count,
- structural gates,
- semantic gates,
- non-target immutability,
- fresh extraction result,
- warnings/holds,
- next authority-order work.

Do not report EXT6/PHASE02 counts as reinforcement completion unless explicitly consumed and validated in the reinforcement contract.

---

## 14. Failure handling

### Source failure

Set `HOLD_SOURCE`. Do not infer missing source dialogue/facts.

### Authority drift

Set `HOLD_AUTHORITY_DRIFT`. Reconcile core/reinforcement pointers before continuing.

### Semantic gate failure

Set `HOLD_SEMANTIC_FAILURE`. Re-read source and reauthor only failed semantic portions; do not auto-patch meaning.

### Validator/tool failure

Fix tooling/contract separately; never alter data meaning merely to satisfy a broken validator.

---

## 15. Immediate next task at V1 seal

Before bulk 98-work thick authoring:

`CT07_REPLICATION_WITH_THICK_NEGATIVE_CONTROL`.

Until this gate passes, the correct action for a new session is **not** to resume the old `38사기동대 EXT6 → PHASE02` queue as if nothing changed. The new session must follow the master authority and current rollout state.
