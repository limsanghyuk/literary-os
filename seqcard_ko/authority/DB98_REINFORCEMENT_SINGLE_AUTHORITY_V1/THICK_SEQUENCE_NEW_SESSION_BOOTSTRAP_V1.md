# DB98 Thick Sequence — New Session Bootstrap V1

Document ID: `DB98_THICK_SEQUENCE_NEW_SESSION_BOOTSTRAP_V1`  
Authority: `DB98_THICK_SEQUENCE_AUTHORING_AUTHORITY_V1`  
Status: `READ_BEFORE_ANY_THICK_AUTHORING`

## 1. What this session is doing

You are reinforcing an existing 98-work Korean drama analysis database with a new append-only Thick Sequence layer.

You are **not** redoing Stage01–04 and you are **not** replacing SceneCard.

Target semantic fields per existing human sequence:

- `cast[]`
- `event`
- `info_shift[]`
- `plant_payoff[]`
- `scene_notes[]`

The model must directly read the original drama source before authoring these fields.

All new reinforcement artifacts are stored under:

`seqcard_ko/reinforcement_v1/`

according to `THICK_SEQUENCE_STORAGE_LAYOUT_V1.md`.

---

## 2. Read these files first, in order

1. repository root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
2. `DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md`
3. active `AUTHORITY_CORRECTION_*` named by the root pointer
4. `THICK_SEQUENCE_AUTHORING_AUTHORITY_V1.md`
5. `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json`
6. `THICK_SEQUENCE_AUTHORING_EXECUTION_V1.md`
7. `THICK_SEQUENCE_AUTHORING_CHECKLIST_V1.json`
8. `THICK_SEQUENCE_STORAGE_LAYOUT_V1.md`
9. `DB98_REINFORCEMENT_WORK_INDEX_POST_CT07R_OVERLAY_V1.json`
10. `CT07R_CURRENT_STATUS.json`
11. `CT-07R_2026-08-07_result.md`
12. `DB98_REINFORCEMENT_WORK_INDEX_V1.json`
13. this file

Then read the active Stage01–04 authority/pointer inside the actual supplied DB.

Do not reconstruct rules from old chats.

---

## 3. Current authority state

Developer acceptance is recorded in:

`THICK_SEQUENCE_ROLLOUT_ACCEPTANCE_20260807.md`

Current execution state:

`FULL_THICK_ROLLOUT_AUTHORIZED`

The base Work Index may still contain historical pre-replication global gate fields. Do not rewrite that sealed baseline merely to change global state. Apply:

`root pointer → post-CT07R Work Index overlay → CT07R_CURRENT_STATUS`

for global state, while per-work progress still comes from:

`base Work Index + latest valid work checkpoint`.

---

## 4. Current experimental truth

CT-07R result: `PASS_NOT_STRONG_REPLICATION`.

Overall:

- `r_T = 0.817`
- `D_N = +2.533`
- work-level `r_T = 0.755 / 0.886`
- judge agreement `95.3%`

Important decomposition:

- within-scene `r_T = 0.567`
- placement/neighbor-relation `r_T = 1.386`

Post-hoc five score categories:

- character `0.542`
- goal `0.625`
- conflict `0.500`
- info `1.429`
- link `1.462`

Interpretation:

- rollout is authorized;
- the strongest measured value is information movement and cross-scene/cross-sequence linkage;
- SceneCard remains valuable for within-scene function;
- category decomposition is **not** field ablation;
- all five Thick fields remain required and separable.

Never say CT-07 `r=1.63` replicated. It did not.

---

## 5. First action in a new session

1. Resolve the actual DB package/root.
2. Verify baseline package/index/authority/source hashes.
3. Read the current work checkpoint if one exists.
4. If resuming, follow checkpoint `next_action`.
5. If starting new, choose the first eligible work in `authority_order`.
6. Create baseline lock/checkpoint before semantic writing.
7. Create/use only the `seqcard_ko/reinforcement_v1/` subtree for new artifacts.

If any baseline/authority/source/sequence drift is unexplained, stop with a hold.

---

## 6. How to analyze one episode

1. Read existing EpisodeArc/Sequence/SceneCard and sidecars only for orientation.
2. Read the entire original episode source in order, using four consecutive quarters for attention management.
3. Understand all human sequences and their boundaries.
4. Re-read each target sequence's member scenes plus immediate boundary context.
5. Author Thick Sequence records in `seq_index` order.
6. Save them to `reinforcement_v1/thick_sequence/<work_id>/` using the storage contract.
7. After all sequences, perform the episode light audit.
8. Materialize/validate R5 PlannerInput and R8 RuntimeSceneProjection.
9. Save progress/checkpoint.

Do not author a sequence from SceneCards alone.

---

## 7. How to think about one sequence

Use this mental model:

`INBOUND → EVENT / CHARACTER ACTION / INFORMATION CHANGE / LINK → OUTBOUND`

Before writing:

- what enters from the previous scene/sequence?
- who wants or does what here?
- what concrete event happens?
- who learns, recalls, infers, conceals, misreads, confirms, or loses access to what?
- what plant/payoff/callback/link is active?
- what does each scene have to accomplish?
- what must be handed to the next scene/sequence?

Then serialize only the exact allowed schema fields.

---

## 8. Quality priorities

Highest priority:

1. source fidelity;
2. sequence specificity;
3. information-state precision;
4. cross-scene/cross-sequence link precision;
5. concrete event;
6. character function;
7. functional per-scene propositions;
8. non-repetition.

Do not confuse “more text” with “better Thick design.”

---

## 9. Mandatory block cadence

- process up to 8 episodes per block;
- read every episode fully before its sequence authoring;
- light audit after every episode;
- strong audit after every block;
- checkpoint after every block and whenever a session may end.

---

## 10. Mandatory companion layers

Do not create a dead sidecar.

For the same work/episode, maintain:

- R5 `PlannerInputRecord` without future leakage;
- R8 `RuntimeSceneProjection` so runtime can consume Thick information.

These may be deterministically assembled where the meaning is already authored.

---

## 11. Never do these

- modify canonical 9-key SceneCard;
- change existing human `member_scene_nos`;
- delete thin `authored_seq`;
- write Thick data into existing core directories instead of `reinforcement_v1/`;
- fuse the five Thick fields;
- invent a payoff/information shift to fill an empty field;
- copy long source dialogue/action;
- use Python to invent semantic meaning;
- treat category scores as proof a field is unnecessary;
- finalize ThickEpisodeExtension before Episode→Sequence diagnostic;
- claim completion before fresh-extract validation.

---

## 12. Resume truth

The authoritative resume location is the latest valid work checkpoint plus root/overlay/current status, not chat history.

If the checkpoint says a block or episode is incomplete, re-verify hashes and resume that exact unit. Do not silently skip forward.
