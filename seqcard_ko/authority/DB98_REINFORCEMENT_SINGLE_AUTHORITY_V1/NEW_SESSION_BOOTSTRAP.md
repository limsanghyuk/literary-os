# DB98 Reinforcement — New Session Bootstrap

Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Method version: `1.0.0`  
Active schema version: `1.0.1`  
Active correction: `AUTHORITY_CORRECTION_V1_0_1`  
Status: `READ_FIRST_AFTER_ROOT_POINTER`

## 1. Mandatory read order

A new session continuing DB98 reinforcement must read exactly in this order:

1. repository root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
2. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md`
3. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/AUTHORITY_CORRECTION_V1_0_1.md`
4. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json`
5. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/SCHEMA_CHANGELOG.md`
6. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_EXECUTION_AND_VALIDATION_V1.md`
7. `docs/tracks/confirmatory/CT07R_CURRENT_STATUS.json`
8. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_WORK_INDEX_V1.json`
9. this file

Then read the active Stage01–04 core authority/pointer declared by the actual working DB package.

Do **not** reconstruct the method from old chats, V1–V10 history, provider manuals, or old EXT6/PHASE02 queues.

The old schema `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1.json` is historical after hotfix 1.0.1. If the sealed master text still names the old schema path, the root pointer + `AUTHORITY_CORRECTION_V1_0_1.md` govern that schema-path conflict.

---

## 2. Research lineage only when needed

- `docs/tracks/confirmatory/CT-06H_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT-07_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_db98_reinforcement_replication_prereg.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1.md`
- `docs/tracks/confirmatory/CT07R_RENDER_PAYLOAD_CONTRACT_V1.json`
- `docs/design/DESIGN-MACRO-PLANNING-SUPPLEMENT-v1.1.md`
- `docs/sessions/2026-08-07_session_summary_home.md`

Frozen evidence:
- CT-06H thin top-down `r=0.211` — not established.
- CT-07 thick top-down `r_L2G=0.807` — two-work pilot established.
- CT-07 thick direct render `r=1.63` vs human SceneCard anchor `1.00`.
- CT-07 L3 ceiling `4.90/5`.

Do not use these numbers to bypass CT-07R replication.

---

## 3. First state check

`CT07R_CURRENT_STATUS.json` is the current **global gate-state override**. Its gate fields supersede stale gate fields in `DB98_REINFORCEMENT_WORK_INDEX_V1.json`; per-work progress still comes from Work Index/checkpoints.

As of this bootstrap revision:

`FULL_THICK_ROLLOUT_BLOCKED_PENDING_CT07_REPLICATION`

and the next semantic-gate action is:

`CT07R_INDEPENDENT_KEY_SEAL_THEN_SANITIZED_BLIND_RENDER_AND_SCORE`

Do not begin bulk thick semantic authoring while blocked.

Allowed before the gate: baseline synchronization, hygiene/leakage audit, deterministic planner-input reassembly, deterministic boundary-negative tooling, validator work, and CT-07R measurement preparation/execution.

### CT-07R critical measurement rules

- correct semantic packets are sealed historical artifacts, not renderer prompts;
- renderer uses sanitized neutral target-shaped payloads only;
- TN must not be labeled foreign/mismatched/negative and must not expose donor episode/seq/provenance metadata;
- target-function key must be authored and SHA-sealed by an independent author blind to thick packets;
- renderer is blind to target-function key and arm meaning;
- judge is blind to arm identity;
- no independent key / render / score means `NOT_MEASURED`, never PASS.

---

## 4. After replication PASS

Only after:

1. preregistered CT-07R replication PASS under v1.0 + amendment v1.1,
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
