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
8. `docs/tracks/confirmatory/CT-07R_2026-08-07_result.md`
9. `docs/handoff/2026-08-07_HANDOFF_CT07R_thick_replication.md`
10. `seqcard_ko/authority/DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1/DB98_REINFORCEMENT_WORK_INDEX_V1.json`
11. this file

Then read the active Stage01–04 core authority/pointer declared by the actual working DB package.

Do **not** reconstruct the method from old chats, V1–V10 history, provider manuals, or old EXT6/PHASE02 queues.

The old schema `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1.json` is historical after hotfix 1.0.1. `AUTHORITY_CORRECTION_V1_0_1.md` is also historical after V1.0.2; current interpretation comes from root pointer + Master + `AUTHORITY_CORRECTION_V1_0_2.md` + current CT-07R status/result.

---

## 2. Research lineage only when needed

- `docs/tracks/confirmatory/CT-06H_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT-07_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_db98_reinforcement_replication_prereg.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1_1.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_02_neutral_context_and_equalized_control.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_amendment_02_as_executed_normalization.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_execution_method.md`
- `docs/tracks/confirmatory/CT-07R_2026-08-07_result.md`
- `docs/tracks/confirmatory/CT07R_RENDER_PAYLOAD_CONTRACT_V1_0_2.json`
- `docs/design/DESIGN-MACRO-PLANNING-SUPPLEMENT-v1.1.md`
- `docs/handoff/2026-08-07_HANDOFF_CT07R_thick_replication.md`

Frozen CT-07 evidence must be read with absolute score and normalized `r` separated:

- CT-06H thin top-down `r=0.211` — not established.
- CT-07 human SceneCard `B=1.425`, `r=1.00`.
- CT-07 thick → generated SceneCard → render `L2-G=1.150`, `r=0.807`.
- CT-07 thick direct render `L2-D=2.325`, `r=1.63`.
- CT-07 L3 `4.900`, `r=3.44`.

CT-07R replication result:

- decision: `PASS_NOT_STRONG_REPLICATION`;
- overall `A=0.167`, `B=3.267`, `T=2.700`, `TN=0.167`;
- `B-A=3.100`, `r_T=0.817`, `D_N=+2.533`;
- work-level `r_T=0.755 / 0.886`;
- leave-one-out `r_T=0.727..0.905`;
- scorer agreement `95.3%`;
- category decomposition: within-scene `r_T=0.567`, placement/neighbor-relation `r_T=1.386`.

Required interpretation: **effect existence/sign replicated, effect magnitude did not** (`CT-07 1.63` must not be quoted as the replicated effect size). Headline `0.817` is a blend; the strongest measured contribution is placement/neighbor relation, not thicker scene-internal prose.

Approval-ground summary phrase:

> 상향 편향된 조건에서도 음성대조와 분리된 성립.

---

## 3. First state check

`CT07R_CURRENT_STATUS.json` is the current **global gate-state override**. Its gate fields supersede stale global gate fields in `DB98_REINFORCEMENT_WORK_INDEX_V1.json`; per-work progress still comes from Work Index/checkpoints.

Current global state:

`FULL_THICK_ROLLOUT_UNBLOCKED_WITH_THREE_CONDITIONS`

Current next action:

`DEVELOPER_ACCEPTANCE_THEN_98_WORK_THICK_AUTHORING_WITH_SEPARABLE_FIELDS_AND_PLACEMENT_RELATION_EMPHASIS`

### What is authorized after developer acceptance

- 98-work Thick Sequence **sidecar** authoring under active schema V1.0.1;
- fields must remain separable: `cast[]`, `event`, `info_shift[]`, `plant_payoff[]`, `scene_notes[]`;
- authoring emphasis must be sequence/scene **placement and neighbor-relation function**, not verbose scene-internal recap;
- R5 `PlannerInputRecord` and R8 `RuntimeSceneProjection` wiring must be bundled with authoring.

### What is NOT authorized by CT-07R

- replacing or deleting human SceneCard;
- claiming a minimum thick-field spec before ablation;
- claiming episode→sequence design is validated (it has never been measured);
- quoting CT-07 `r=1.63` as the replicated effect size;
- fusing the five thick fields into one prose blob;
- deleting historical thin `authored_seq` as a consequence of this result.

### Remaining research items that do not block the approved sidecar rollout

- field ablation to derive minimum field specification;
- episode→sequence rung diagnostic;
- robustness rerun under the GPT padding-style amendment-02 rule (fresh render set required);
- CT-03 style/re-irregularity experiment.

---

## 4. Per-work operating summary after acceptance

```text
baseline lock/reverify
→ hygiene scan/ledger
→ source-grounded Thick Sequence extension
   cast[] / event / info_shift[] / plant_payoff[] / scene_notes[]
   with placement/neighbor-relation emphasis
→ character/info/payoff connection audit
→ R5 PlannerInputRecord wiring/reassembly
→ R8 RuntimeSceneProjection wiring
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

## 5. Meaning/tool boundary

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
- schema/parse/encoding/hash validation,
- packaging/fresh extraction.

Python/tooling must not invent literary meaning.

---

## 6. Experiment reproducibility

The hub contains the CT-07R hub-safe artifacts and recomputation script. Recompute the adjudicated result with:

```bash
python docs/tracks/confirmatory/artifacts/ct07r/CT07R_analyze.py --run docs/tracks/confirmatory/artifacts/ct07r
```

Expected headline output: PASS, `r_T=0.817`, `D_N=+2.533`, S2 `0.727..0.905`, category decomposition `0.567 / 1.386`, agreement `95.3%`.

Canonical key files containing source evidence are not in the public hub; only SHA seals and hub-safe derivatives are present. Do not reconstruct canonical keys from chat/memory.

---

## 7. Holds and urgent release hygiene

Known retained source hold:
- `최강칠우` — `RETAINED_AUTHORIZED_SOURCE_HOLD`.

Urgent repository hygiene inherited from handoff:
- `docs/sessions/**/original_extracted/` reportedly contains 130 original-script files (8.6MB / 197,776 lines) in public history from commit `362c6f7`;
- recommended immediate containment: make repository private before any further public distribution;
- history rewrite/removal is a separate destructive repository operation and requires explicit developer decision;
- analysis-only `skin` hygiene remains an independent R1 task.

---

## 8. Completion truth

A work is reinforced-complete only when its checkpoint/work state reaches `FRESH_EXTRACT_PASS` with supporting hashes. Experiment PASS, extension JSON existence, schema-only PASS, or old EXT6/PHASE02 completion are not per-work reinforcement completion.

---

## 9. Session-limit handoff

Before changing sessions:
1. save artifacts;
2. update checkpoint;
3. update current gate status/work index when state changes;
4. record SHA256 and exact next action;
5. do not rely on prose chat handoff alone.
