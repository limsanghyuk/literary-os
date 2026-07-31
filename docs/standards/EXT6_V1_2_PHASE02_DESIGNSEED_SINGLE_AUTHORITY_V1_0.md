# EXT6 V1.2 Phase02 DesignSeed Single Authority V1.0

- Authority ID: `EXT6-V1.2-PHASE02-DESIGNSEED-AUTHORITY-V1.0`
- Status: **AUTHORIZED_PILOT_ONLY**
- Authorization: user direction, 2026-07-31 21:22 KST
- Parent authority: `SEQCARD-EXT6-PHASE1-CONTRACT-v1` (FROZEN)
- Supersedes: no existing Phase01/V1.2 record or schema
- Core Stage01~04 changed: **false**
- Existing EXT6 V1.2 sidecars changed: **false**
- Canonical promotion allowed: **false** until SEED-D `PROMOTE` and separate user approval

## 1. Decision

DesignSeed is admitted as the first official Phase02 extension of EXT6 V1.2. It is not inserted into SceneCard, SequenceBlueprint, EpisodeArc, CharacterArc, RelationshipArc, edge, payoff, or FullSeriesArc records. It is a separate sidecar family.

This authority converts the prior DesignSeed draft into an executable pilot contract. It intentionally does **not** authorize a 90-work rollout. The only authorized scope is the preregistered 10-work pilot and its deterministic validation/evaluation outputs.

## 2. Invariants

1. Stage01~04 remain byte-identical.
2. Existing EXT6 V1.2 records remain byte-identical.
3. Phase02 files use only `advisory_` or `derived_` authority classes.
4. No Phase02 record may write to canonical memory, Stage03 arcs, Stage04 edges/payoffs, or source files.
5. Python may validate, compare, hash, derive registered indicators, and package. Python may not author judged seed semantics.
6. `EP01_02_BLIND` must be authored and sealed before `FULL_READ` for the same work.
7. A missing source or missing boundary manifest is a HOLD, never a PASS.
8. Agreement between providers measures contract stability, not truth.
9. All thresholds are preregistered and immutable until SEED-D completes.
10. An ineffective layer is rejected rather than normalized into success.

## 3. Contract family

### 3.1 DesignSeedRecord — 14 keys

Path: `seqcard_ko/advisory_seed/<work>.<mode>.seed.json`
Grain: `(work_id, derivation_mode)`

Exact keys:

```text
work_id
derivation_mode
read_span
evidenced_initial_configuration
evidenced_world_constraints
evidenced_opening_disturbance
judged_logline
judged_central_lack
judged_governing_question
judged_central_opposition_axis
judged_ending_direction
judged_cost_structure
contract_version
by
```

EVIDENCED block:

- `evidenced_initial_configuration`: list of exact objects `{character_key, initial_position, initial_relation_axis, evidence_ref}`.
- `evidenced_world_constraints`: list of exact objects `{rule, scope, evidence_ref}`.
- `evidenced_opening_disturbance`: exact object `{summary, scene_no, evidence_ref}`.
- Every `evidence_ref` uses `EPnn-Snn Lnn <short quote>` and must resolve inside `read_span`.

JUDGED block:

- `judged_logline`: one sentence; no proper names, episode numbers, scene numbers, or terminal-event disclosure.
- `judged_central_lack`: one abstract dramatic lack.
- `judged_governing_question`: a season-bearing yes/no question.
- `judged_central_opposition_axis`: opposition expressed as forces/values, not named characters.
- `judged_ending_direction`: one registered enum.
- `judged_cost_structure`: exact object `{cost_type, cost_bearer, cost_summary}`.
- JUDGED fields must not contain `evidence_ref` wrappers or downstream citations.

### 3.2 SeedAdmissibilityRecord — 7 keys

Path: `seqcard_ko/advisory_seed_admissibility/<work>.<mode>.adm.json`
Grain: `(work_id, derivation_mode)`

```text
work_id
derivation_mode
compatible_work_ids
compatibility_count
alternative_structures
specificity_violations
verdict
```

- `compatible_work_ids` is evaluated against the frozen corpus index.
- `alternative_structures` contains at least three exact objects `{sketch, divergence_point}`.
- `specificity_violations` contains exact objects `{field, token, violation_type}` and must be empty for acceptance.

Preregistered compatibility bands:

```text
count = 1       -> TOO_SPECIFIC
2..10           -> ADMISSIBLE
11..30          -> REVIEW
>=31            -> TOO_VAGUE
```

### 3.3 SeedStructurePredictionRecord — 9 keys

Path: `seqcard_ko/derived_seed_prediction/<work>.pred.jsonl`
Grain: `(work_id, derivation_mode, indicator)`

```text
work_id
derivation_mode
indicator
predicted_value
observed_value
observation_source
match
corpus_prior
by
```

Exactly five indicators are allowed:

1. `center_count`
2. `opposition_persistence`
3. `conflict_persist`
4. `ending_direction`
5. `cost_realized`

These rows are deterministic evaluation outputs and must use `by=derived_deterministic`.

### 3.4 SeedContaminationRecord — 8 keys

Path: `seqcard_ko/derived_seed_contamination/<work>.contam.json`
Grain: `work_id`

```text
work_id
mode_b_ref
mode_c_ref
field_level_diff
diverged_fields
mode_b_prediction_accuracy
mode_c_prediction_accuracy
leakage_estimate
```

Formula:

```text
leakage_estimate = mode_c_prediction_accuracy - mode_b_prediction_accuracy
```

### 3.5 SeedAuthoringBoundaryManifest — 15 keys

Path: `seqcard_ko/advisory_seed_runs/<work>.<mode>.run.json`
Grain: `(work_id, derivation_mode, run_id)`

```text
work_id
derivation_mode
read_span
run_id
provider
model_id
source_file_refs
source_sha256s
downstream_layers_blocked
downstream_blocklist
cross_provider_outputs_blocked
prior_mode_ref
sealed_at
content_sha256
by
```

This manifest makes anti-circularity claims auditable. `EP01_02_BLIND` requires both block flags to be true and requires the downstream blocklist. `FULL_READ` requires `prior_mode_ref` to point to a sealed blind record.

## 4. Derivation modes

### PLAN_DOCUMENT

Only pre-outcome documents: planning statement, synopsis, character bible, pitch, or equivalent. It is defined but currently unavailable for the corpus unless a source document is actually present and hashed.

### EP01_02_BLIND

Read only episodes 1 and 2. Do not read episode 3+, CharacterArc terminal states, RelationshipArc terminal states, FullSeriesArc, Stage04 payoff disposition, seed records from another provider, or a prior FULL_READ record.

### FULL_READ

Read the full work only after the blind record and run manifest are sealed. It is a contamination-control comparison, not the default training source.

## 5. Gates

### SEED-A — Contract integrity, hard, ERRORS 0

- exact keysets and nested keysets
- enum and type checks
- grain uniqueness
- Bridge and SceneCard FK
- mode/read-span consistency
- compatible work IDs exist
- prediction indicator set exactly five
- content SHA verification

### SEED-B — Evidence integrity, hard, ERRORS 0

- every EVIDENCED item has a valid reference
- reference episode lies in read span
- source line resolves within ±3 lines after normalization
- no placeholder evidence
- JUDGED fields contain no evidence wrapper or source citation
- source hashes in the boundary manifest match the files read

### SEED-C — Anti-circularity, hard, ERRORS 0

- no episode/scene numbers, proper names, or exact terminal events in judged fields
- at least three alternative structures
- specificity violations empty
- admissibility verdict is `ADMISSIBLE`
- blind boundary flags are true
- blind mode is sealed before full-read mode
- no cross-provider output read before seal

### SEED-D — Utility evaluation, advisory decision

Preregistered rule, Bonferroni-corrected alpha 0.01:

```text
3..5 of 5 indicators significantly exceed corpus prior -> PROMOTE
1..2 indicators exceed                              -> REVISE once
0 indicators exceed                                 -> REJECT layer
median leakage_estimate > 0.30                       -> permanently exclude FULL_READ from training
```

`PROMOTE` does not itself make records canonical. A separate user authorization is still required.

## 6. Pilot

Authorized works:

```text
비밀의숲
커피프린스
배가본드
하얀거탑
공주의남자
힐러
구르미그린달빛
강남엄마따라잡기
굿캐스팅
결혼못하는남자
```

Required order:

1. Freeze schema, validator, thresholds, corpus index, and source hashes.
2. Author all ten `EP01_02_BLIND` records without downstream access.
3. Run SEED-A/B/C and seal all passing blind records.
4. Produce admissibility records against the frozen corpus.
5. Author all ten `FULL_READ` comparison records in a separate run.
6. Derive prediction and contamination records without LLM semantic generation.
7. Run SEED-D.
8. Expand only after `PROMOTE` and separate user approval.

## 7. Physical integration with EXT6 V1.2

```text
seqcard_ko/
  advisory_seed/
  advisory_seed_admissibility/
  advisory_seed_runs/
  derived_seed_prediction/
  derived_seed_contamination/
  ext6_schema/EXT6_PHASE02_DESIGNSEED_EXACT_SCHEMA_REGISTRY_V1_0.json
  _ext6_tools/ext6_seed_gate.py
```

The existing V1.2 package remains valid without Phase02 files. A package claiming Phase02 participation must include the boundary manifest and a gate report. Phase02 is therefore backward-compatible and append-only.

## 8. Promotion states

```text
DRAFT                -> historical proposal only
AUTHORIZED_PILOT_ONLY -> this authority
PILOT_PASS_CANDIDATE  -> A/B/C pass for all ten works
PROMOTE_RECOMMENDED   -> SEED-D promote result
CANONICAL_AUTHORIZED  -> separate user authorization required
REJECTED              -> utility failure; no rollout
```

## 9. Prohibitions

- no retroactive claim that a completed-work summary was a pre-writing plan
- no evidence fabrication for judged fields
- no automatic Stage03/04 mutation
- no model/provider result merging before blind seal
- no threshold tuning after observing results
- no 90-work rollout from schema validity alone
- no PASS when source verification was not executed
- no use of FULL_READ seeds as default training records

## 10. Acceptance

This authority is the single execution authority for the Phase02 DesignSeed pilot. The earlier Phase02 design remains historical design evidence. The exact schema registry and gate tool named above are normative execution artifacts.
