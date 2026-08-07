# DB98 Reinforcement — New Session Bootstrap

Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Active Thick authority: `DB98_THICK_SEQUENCE_AUTHORING_AUTHORITY_V1`  
Active schema: `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1`  
Status: `POST_CT07R_FULL_THICK_ROLLOUT_AUTHORIZED`

---

## 1. Mandatory read order

A new session continuing DB98 reinforcement must read in this order:

1. repository root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
2. `DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md`
3. active `AUTHORITY_CORRECTION_*` named by the root pointer
4. `THICK_SEQUENCE_AUTHORING_AUTHORITY_V1.md`
5. `schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json`
6. `THICK_SEQUENCE_AUTHORING_EXECUTION_V1.md`
7. `THICK_SEQUENCE_AUTHORING_CHECKLIST_V1.json`
8. `docs/tracks/confirmatory/CT07R_CURRENT_STATUS.json`
9. `docs/tracks/confirmatory/CT-07R_2026-08-07_result.md`
10. `DB98_REINFORCEMENT_WORK_INDEX_V1.json`
11. `THICK_SEQUENCE_NEW_SESSION_BOOTSTRAP_V1.md`
12. this file if broader reinforcement context is needed

Then read the active Stage01–04 core authority/pointer declared by the **actual supplied DB package**.

Do not reconstruct the method from old chats, old EXT6/PHASE02 queues, or provider history.

---

## 2. Current global state

CT-07R is complete and adjudicated:

`PASS_NOT_STRONG_REPLICATION`

Developer acceptance is recorded in:

`THICK_SEQUENCE_ROLLOUT_ACCEPTANCE_20260807.md`

Current rollout state for the authorized scope:

`FULL_THICK_ROLLOUT_AUTHORIZED`

The next authoritative action is:

`SELECT_FIRST_ELIGIBLE_AUTHORITY_ORDER_WORK_AND_BEGIN_THICK_SEQUENCE_AUTHORING_PER_ACTIVE_AUTHORITY`

If `DB98_REINFORCEMENT_WORK_INDEX_V1.json` still contains historical global gate fields from sealing time, the root pointer/current status/rollout acceptance override those **global** fields. Per-work progress still comes from Work Index + checkpoints.

---

## 3. What is authorized

For the existing DB98, author an append-only Thick Sequence extension for each eligible existing human `seq_id` with five **separate** semantic fields:

- `cast[]`
- `event`
- `info_shift[]`
- `plant_payoff[]`
- `scene_notes[]`

Bundle the new layer with:

- R5 `PlannerInputRecord`
- R8 `RuntimeSceneProjection`

The model must directly read and understand original source before authoring semantic additions.

---

## 4. What remains protected

Do not:

- modify or replace canonical 9-key SceneCard;
- change human `authored_seq.member_scene_nos`;
- delete thin `authored_seq`;
- rewrite Stage01–04 merely to fit reinforcement;
- fuse the five Thick fields;
- automatically promote reinforcement to canonical core;
- finalize `ThickEpisodeExtension` before Episode→Sequence diagnostic.

---

## 5. Current empirical interpretation

CT-07R headline:

- `A=0.167`
- `B=3.267`
- `T=2.700`
- `TN=0.167`
- `r_T=0.817`
- `D_N=+2.533`
- work-level `r_T=0.755 / 0.886`
- judge agreement `95.3%`

Prespecified relation split:

- within-scene `r_T=0.567`
- placement/neighbor-relation `r_T=1.386`

Post-hoc original five score categories:

- character `0.542`
- goal `0.625`
- conflict `0.500`
- info `1.429`
- link `1.462`

Required reading:

- the strongest measured Thick advantage is information movement and linkage/placement;
- SceneCard remains stronger for within-scene information in this experiment;
- the five-category split is **not** a field-level ablation because all five Thick fields were supplied together;
- all five fields remain required and separable until ablation measures field contribution;
- CT-07 `r=1.63` did not replicate and must not be used as the DB98 rollout effect estimate.

Approval-ground summary phrase:

> 상향 편향된 조건에서도 음성대조와 분리된 성립.

---

## 6. First work start procedure

1. resolve the actual DB package/root;
2. verify baseline package/index SHA and active core authority;
3. verify target source/SourceLock and Stage01–04 hashes;
4. load latest target checkpoint if present;
5. if new, choose first eligible work from exact `authority_order`;
6. record baseline lock/checkpoint;
7. follow `THICK_SEQUENCE_AUTHORING_EXECUTION_V1.md`.

Unexplained baseline/authority/source/sequence drift → `HOLD_AUTHORITY_DRIFT` or `HOLD_SOURCE` before semantic writing.

---

## 7. Episode/work cadence

- process consecutive blocks of up to 8 episodes;
- before sequence authoring, read each entire episode source in four consecutive quarters;
- author sequences in existing `seq_index` order;
- light audit after every episode;
- strong audit after every block;
- checkpoint every block and before session change;
- whole-work integration + fresh-extract validation before `FRESH_EXTRACT_PASS`.

Existing analysis files are indexes/evidence candidates, not substitutes for direct source reading.

---

## 8. Mandatory semantic emphasis

For every sequence reason through:

`INBOUND → SEQUENCE TRANSFORMATION → OUTBOUND`

Ask what enters from the previous scene/sequence, what concrete event and information change occurs, what link/plant/payoff remains active, and what is handed to the next scene/sequence.

Do not turn Thick authoring into longer recap prose.

---

## 9. Separate research still open

The authorized rollout does not answer:

1. minimum field set — requires field ablation;
2. Episode→Sequence generation quality — never measured, requires separate diagnostic;
3. robustness under the alternate GPT padding-style CT-07R amendment — requires new renders;
4. CT-03 style/irregularity follow-up.

These do not block the current five-field separable Thick Sequence rollout.

---

## 10. Holds and release hygiene

Known retained source hold remains:

- `최강칠우` — `RETAINED_AUTHORIZED_SOURCE_HOLD`.

Repository release hygiene remains separate and urgent: original-script files reportedly exist in public history under `docs/sessions/**/original_extracted/`. Containment/removal decisions do not change Thick semantic authority, but public distribution should not proceed without leakage review.

---

## 11. Completion truth

A work is reinforced-complete only when checkpoint/work state reaches `FRESH_EXTRACT_PASS` with supporting hashes after:

`SOURCE READ → THICK AUTHORING → EPISODE/BLOCK AUDIT → R5/R8 WIRING → SEMANTIC/SOURCE VALIDATION → IMMUTABILITY → INTEGRATION → FRESH EXTRACTION REVALIDATION`.

Chat claims, experiment PASS, schema-only PASS, or legacy EXT6/PHASE02 completion are not per-work reinforcement completion.
