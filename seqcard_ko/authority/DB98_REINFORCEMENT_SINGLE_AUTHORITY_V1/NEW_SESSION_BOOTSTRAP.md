# DB98 Reinforcement — New Session Bootstrap

Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Method version: `1.0.0`  
Active schema version: `1.0.1`  
Active correction: `AUTHORITY_CORRECTION_V1_0_2`  
Status: `READ_FIRST_AFTER_ROOT_POINTER`

## 1. Mandatory read order

A new session continuing DB98 reinforcement must read exactly in this order:

1. repository root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
2. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md`
3. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/AUTHORITY_CORRECTION_V1_0_2.md`
4. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json`
5. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/SCHEMA_CHANGELOG.md`
6. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_EXECUTION_AND_VALIDATION_V1.md`
7. `docs/tracks/confirmatory/CT07R_CURRENT_STATUS.json`
8. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_WORK_INDEX_V1.json`
9. this file

Then read the active Stage01–04 core authority/pointer declared by the actual working DB package.

Do **not** reconstruct the method from old chats, V1–V10 history, provider manuals, or old EXT6/PHASE02 queues.

The old schema `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1.json` is historical after hotfix 1.0.1. `AUTHORITY_CORRECTION_V1_0_1.md` is also historical after V1.0.2; current interpretation comes from the root pointer + Master + `AUTHORITY_CORRECTION_V1_0_2.md`.

---

## 2. Research lineage only when needed

- `docs/tracks/confirmatory/CT-06H_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT-07_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_db98_reinforcement_replication_prereg.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1_1.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_02_neutral_context_and_equalized_control.md`
- `docs/tracks/confirmatory/CT07R_RENDER_PAYLOAD_CONTRACT_V1_0_2.json`
- `docs/design/DESIGN-MACRO-PLANNING-SUPPLEMENT-v1.1.md`
- `docs/sessions/2026-08-07_session_summary_home.md`

Frozen CT-07 evidence must be read with absolute score and normalized `r` separated:

- CT-06H thin top-down `r=0.211` — not established.
- CT-07 human SceneCard `B=1.425`, `r=1.00`.
- CT-07 thick → generated SceneCard → render `L2-G=1.150`, `r=0.807`.
- CT-07 thick direct render `L2-D=2.325`, `r=1.63`.
- CT-07 L3 `4.900`, `r=3.44`.
- absolute L2-D → L2-G loss: `1.175`; normalized-r loss approximately `0.823`.

Never write the ambiguous shorthand “SceneCard compression = 0.807” without identifying L2-G and the normalized-r scale.

Do not use CT-07 numbers to bypass CT-07R replication.

---

## 3. First state check

`CT07R_CURRENT_STATUS.json` is the current **global gate-state override**. Its gate fields supersede stale gate fields in `DB98_REINFORCEMENT_WORK_INDEX_V1.json`; per-work progress still comes from Work Index/checkpoints.

Current global state remains:

`FULL_THICK_ROLLOUT_BLOCKED_PENDING_CT07_REPLICATION`

Current next action is read from `CT07R_CURRENT_STATUS.json`. At this revision it is:

`INGEST_LOCAL_KEYS_AND_SHORT_ANCHOR_AMENDMENT_THEN_RUN_MATERIALIZER_V1_0_2_AND_40_RENDER_BATCH`

Do not begin bulk thick semantic authoring while blocked.

Allowed before the gate: baseline synchronization, skin/data hygiene, deterministic planner-input reassembly, deterministic boundary-negative tooling, validator work, and CT-07R measurement preparation/execution.

### CT-07R critical measurement rules

- correct semantic packets are sealed historical artifacts, not raw renderer prompts;
- renderer uses V1.0.2 target-shaped payloads only;
- T and TN receive the exact same neutral sentence: `이 설계 맥락은 검증되지 않았을 수 있다.`;
- neither T nor TN may be labeled correct/foreign/mismatched/wrong/negative/donor;
- T and TN must have identical target scene-slot coverage and all slots nonempty;
- TN semantic donor remains the frozen within-work cyclic +1 mapping and may not be rewritten toward target meaning;
- target-function key must be independently authored and hub-SHA-sealed before confirmatory rendering/scoring;
- local-reported key completion is not the same as hub seal;
- renderer is blind to target-function key and arm meaning;
- judge is blind to arm identity;
- no valid independent key / render / score means `NOT_MEASURED`, never PASS.

### Local CT-07R files reported but not yet hub-sealed

The developer reports local completion under:

- `C:\claude\CT07R_run_20260807\keys\` with SHA prefixes `f456a957…`, `16719be5…`;
- `C:\claude\CT07R_run_20260807\CT-07R_amendment_01_short_anchor_sensitivity.md`.

A new session must **not recreate these from chat or memory**. Ingest exact bytes, calculate/verify full SHA256, then update `CT07R_CURRENT_STATUS.json`.

---

## 4. After replication PASS

Only after:

1. preregistered CT-07R replication PASS under v1.0 + all active pre-render amendments including amendment 02,
2. valid thick negative control,
3. developer acceptance,
4. root pointer/current gate status/work index updated to `FULL_THICK_ROLLOUT_AUTHORIZED`,

may a session select the first `READY` work from `authority_order` for full thick authoring.

Then load only that target's source/source lock, Stage01–04, relevant cast/character/relation/payoff/edge files, and reinforcement checkpoint.

---

## 5. Per-work operating summary

```text
baseline lock
→ hygiene scan/ledger
→ source-grounded thick sequence extension
   cast[] / event / info_shift[] / plant_payoff[] / scene_notes[]
→ character/info/payoff connection audit
→ planner-input reassembly
→ subplot GT if supported
→ deterministic boundary negatives
→ structural gates
→ semantic/source gates
→ non-target immutability
→ checkpoint
→ integration
→ whole-DB validation
→ fresh extraction validation
```

Stage01–04 are protected. Reinforcement is append-only except explicitly ledgered hygiene/core-authority corrections.

---

## 6. Meaning/tool boundary

Model/source authoring required:
- character desire/function,
- concrete sequence event,
- information movement meaning,
- plant/payoff planning use,
- scene functional propositions,
- subplot narrative identity/crossing.

Deterministic tools allowed:
- hashes/inventory,
- ID/FK/member coverage,
- validated cast-presence proposals,
- counts/shares/spans,
- planner-input reassembly,
- synthetic boundary transforms,
- sanitized experimental payload materialization,
- schema/parse/encoding/hash validation,
- packaging/fresh extraction.

Python/tooling must not invent literary meaning.

---

## 7. Holds

- Source defect → `HOLD_SOURCE`
- Core/reinforcement authority mismatch → `HOLD_AUTHORITY_DRIFT`
- Semantic validation failure → `HOLD_SEMANTIC_FAILURE`

Known retained hold:
- `최강칠우` — `RETAINED_AUTHORIZED_SOURCE_HOLD`

Do not silently clear it.

---

## 8. Completion truth

A work is reinforced-complete only when the checkpoint/work state says `FRESH_EXTRACT_PASS` and supporting hashes exist. Old EXT6/PHASE02 completion, experiment packets, chat claims, or schema-only PASS are not DB98 reinforcement completion.

---

## 9. Session-limit handoff

Before changing sessions:
1. save artifacts,
2. update checkpoint,
3. update current gate status/work index when state changes,
4. record SHA256 and next action,
5. do not rely on prose chat handoff alone.
