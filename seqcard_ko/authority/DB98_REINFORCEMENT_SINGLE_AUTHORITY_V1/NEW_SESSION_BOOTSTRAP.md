# DB98 Reinforcement — New Session Bootstrap

Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Status: `READ_FIRST_AFTER_ROOT_POINTER`

## 1. Mandatory read order

A new session continuing DB98 reinforcement must read exactly in this order:

1. repository root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
2. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md`
3. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1.json`
4. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_EXECUTION_AND_VALIDATION_V1.md`
5. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_WORK_INDEX_V1.json`
6. this file

Then read the active Stage01–04 core authority/pointer declared by the actual working DB package.

Do **not** start by reconstructing the method from old chats, V1–V10 history, provider manuals, or old EXT6/PHASE02 queues.

---

## 2. Research lineage only when needed

The reinforcement rationale is already frozen in the master authority. If auditing the research evidence, read:

- `docs/tracks/confirmatory/CT-06H_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT-07_2026-08-07_result.md`
- `docs/design/DESIGN-MACRO-PLANNING-SUPPLEMENT-v1.1.md`
- `docs/sessions/2026-08-07_session_summary_home.md`

Key frozen numbers:

- CT-06H thin top-down `r=0.211` — not established.
- CT-07 thick top-down `r_L2G=0.807` — established in two-work pilot.
- CT-07 thick direct render `r=1.63` vs human SceneCard anchor `1.00`.
- CT-07 L3 ceiling `4.90/5`.

Do not reinterpret these numbers to bypass the replication gate.

---

## 3. First state check

Read `DB98_REINFORCEMENT_WORK_INDEX_V1.json` and answer internally:

- What is `global_rollout_state`?
- What is `next_authoritative_action`?
- What is the baseline candidate package/SHA?
- Does the actual supplied DB match it?
- What active core authority does the supplied DB declare?
- Is there a newer explicitly authorized reinforcement authority?

If the global state is still:

`FULL_THICK_ROLLOUT_BLOCKED_PENDING_CT07_REPLICATION`

then **do not begin bulk work reinforcement**.

The next work is the CT-07 replication + mismatched-thick negative control, not legacy `38사기동대 EXT6 → PHASE02` continuation.

---

## 4. After replication PASS

Only after:

1. preregistered replication PASS,
2. mismatched-thick negative control included,
3. developer acceptance,
4. work index and root pointer updated to `FULL_THICK_ROLLOUT_AUTHORIZED`,

may the session select the first `READY` work from `authority_order`.

Then load only that target's:

- source/source lock,
- Stage01–04 files,
- existing cast/load/character/relation/payoff/edge files,
- reinforcement checkpoint if any.

Do not pre-read another work's semantic reinforcement output when independent authorship/evaluation requires isolation.

---

## 5. Per-work operating summary

For a selected work:

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

Stage01–04 are protected. V1 reinforcement is append-only except explicitly ledgered hygiene/correction work.

---

## 6. Meaning/tool boundary

### Model/source authoring required

- character desire/function,
- concrete sequence event,
- information movement meaning,
- plant/payoff planning use,
- per-scene functional propositions,
- subplot narrative identity/crossing.

### Deterministic tools allowed

- hashes/inventory,
- ID/FK/member coverage,
- cast-presence proposals from validated sidecars,
- counts/shares/spans,
- planner-input state reassembly,
- synthetic boundary transforms,
- schema/parse/encoding/hash validation,
- packaging/fresh extraction.

Python/tooling must not invent literary meaning.

---

## 7. Holds

- Source defect → `HOLD_SOURCE`
- Core/reinforcement authority mismatch → `HOLD_AUTHORITY_DRIFT`
- Semantic validation failure → `HOLD_SEMANTIC_FAILURE`

Known retained baseline hold at seal time:

- `최강칠우` — `RETAINED_AUTHORIZED_SOURCE_HOLD`

Do not silently clear it.

---

## 8. Completion truth

A work is complete only when the work index/checkpoint says `FRESH_EXTRACT_PASS` and the supporting files/hashes exist.

Chat statements such as “done”, old EXT6 completion, old PHASE02 completion, or schema-only PASS are not completion evidence for this reinforcement authority.

---

## 9. If the chat context is near its limit

Before changing sessions:

1. save all current artifacts,
2. update per-work checkpoint,
3. update work index if state changed,
4. record artifact SHA256s and next action,
5. do not rely on a prose chat handoff alone.

The next session must be able to continue from the hub authority + checkpoint without needing the previous conversation.
