# DB98 Thick Sequence Storage Layout V1

Document ID: `DB98_THICK_SEQUENCE_STORAGE_LAYOUT_V1`  
Authority: `DB98_THICK_SEQUENCE_AUTHORING_AUTHORITY_V1`  
Status: `ACTIVE_STORAGE_CONTRACT`

## 0. Purpose

The active exact schema defines record shape but the DB also needs one deterministic physical layout. New sessions must not invent different folders or filenames.

All new DB98 reinforcement V1 artifacts are stored under a new append-only namespace:

`seqcard_ko/reinforcement_v1/`

This keeps Stage01–04 and existing human-authored core directories untouched.

---

## 1. Canonical reinforcement tree

```text
seqcard_ko/
  reinforcement_v1/
    thick_sequence/
      <work_id>/
        <work_id>_<EP>.thick_sequence.jsonl
    planner_input/
      <work_id>/
        <work_id>_<EP>.planner_input.json
    runtime_scene_projection/
      <work_id>/
        <work_id>_<EP>.runtime_scene_projection.jsonl
    checkpoints/
      <work_id>/
        work_state.json
        history/
          <timestamp>.checkpoint.json
    validation/
      <work_id>/
        episode/
          <work_id>_<EP>.light_audit.json
        block/
          block_<START_EP>_<END_EP>.strong_audit.json
        work/
          final_validation.json
          non_target_immutability.json
          fresh_extract_validation.json
    ledgers/
      <work_id>/
        hygiene.jsonl
        semantic_corrections.jsonl
    manifests/
      <work_id>/
        reinforcement_manifest.json
```

`<EP>` is zero-padded to at least two digits (`01`, `02`, ...). Preserve the exact canonical `work_id` used by the active DB.

---

## 2. Thick Sequence files

Path:

`seqcard_ko/reinforcement_v1/thick_sequence/<work_id>/<work_id>_<EP>.thick_sequence.jsonl`

Rules:

- UTF-8 without BOM;
- JSONL, one record per existing human `seq_id` in the episode;
- record schema exactly `DB98_THICK_SEQUENCE_EXTENSION_V1`;
- records sorted by `seq_index` ascending;
- no duplicate `seq_id`;
- no episode silently omitted;
- existing `member_scene_nos` must match `seqcard_ko/authored_seq` exactly;
- no extra metadata keys outside the active schema.

Do not store experimental CT-07R packets in this directory. Experimental evidence remains under `docs/tracks/confirmatory/`.

---

## 3. PlannerInput files

Path:

`seqcard_ko/reinforcement_v1/planner_input/<work_id>/<work_id>_<EP>.planner_input.json`

Rules:

- one `DB98_PLANNER_INPUT_RECORD_V1` object per episode;
- only information legitimately available at the episode planning boundary;
- target EpisodeArc/Thick Sequence references remain target refs, not leaked inputs;
- future-information leakage is a hard validation failure.

---

## 4. Runtime projection files

Path:

`seqcard_ko/reinforcement_v1/runtime_scene_projection/<work_id>/<work_id>_<EP>.runtime_scene_projection.jsonl`

Rules:

- one `DB98_RUNTIME_SCENE_PROJECTION_V1` record per projected scene;
- sorted by `scene_no`;
- generated/materialized from valid core + reinforcement records;
- does not mutate canonical SceneCard;
- every runtime record preserves source refs and parent `seq_id`.

---

## 5. Checkpoints

Current state:

`seqcard_ko/reinforcement_v1/checkpoints/<work_id>/work_state.json`

Append-only history:

`seqcard_ko/reinforcement_v1/checkpoints/<work_id>/history/<timestamp>.checkpoint.json`

Before replacing `work_state.json`, copy the previous valid checkpoint into `history/` unchanged.

Checkpoint is the authoritative resume location for per-work progress.

---

## 6. Validation artifacts

### Episode light audit

`validation/<work_id>/episode/<work_id>_<EP>.light_audit.json`

### Up-to-8-episode strong block audit

`validation/<work_id>/block/block_<START_EP>_<END_EP>.strong_audit.json`

### Work final validation

`validation/<work_id>/work/final_validation.json`

### Non-target immutability

`validation/<work_id>/work/non_target_immutability.json`

### Fresh extraction validation

`validation/<work_id>/work/fresh_extract_validation.json`

Validation outputs are evidence; they must never rewrite semantic meaning automatically.

---

## 7. Ledgers

Hygiene changes:

`ledgers/<work_id>/hygiene.jsonl`

Semantic reinforcement corrections after initial authorship:

`ledgers/<work_id>/semantic_corrections.jsonl`

Every semantic correction must record old/new artifact hash, affected record/field, reason, source reread status, operator/model, and timestamp. Do not silently mutate already integrated semantic records.

---

## 8. Per-work manifest

Path:

`manifests/<work_id>/reinforcement_manifest.json`

At minimum record:

- authority IDs and schema version;
- baseline package/index hashes;
- target work source/core hashes;
- episode count;
- sequence count;
- Thick file paths/hashes;
- PlannerInput paths/hashes;
- RuntimeProjection paths/hashes;
- checkpoint hash;
- validation artifact hashes;
- holds/warnings;
- work completion state.

---

## 9. Core-directory protection

Reinforcement authoring must not add new Thick fields directly into:

- `seqcard_ko/authored/`
- `seqcard_ko/authored_seq/`
- `seqcard_ko/authored_arc/`
- `seqcard_ko/authored_chararc/`
- `seqcard_ko/authored_relarc/`
- `seqcard_ko/authored_edges/`
- `seqcard_ko/source_lock/`
- `seqcard_ko/original_extracted/`

Any correction to those areas requires the appropriate separate core/hygiene authority and ledger.

---

## 10. Packaging rule

When integrating into a full DB package:

1. add only the new `reinforcement_v1/` subtree plus separately authorized ledgers/corrections;
2. verify protected-core hashes;
3. run whole-DB validation;
4. build package;
5. fresh-extract to a new path;
6. rerun parse/FK/hash/coverage/immutability checks;
7. only then mark `FRESH_EXTRACT_PASS`.
