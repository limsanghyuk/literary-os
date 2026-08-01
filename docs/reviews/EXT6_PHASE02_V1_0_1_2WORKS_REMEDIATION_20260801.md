# EXT6 Phase02 V1.0.1 — Two-Work Remediation Report

- Date: 2026-08-01
- Works: `내이름은김삼순`, `내여자친구는구미호`
- Status: **PASS_CANDIDATE_REMEDIATED**
- Stage01~04 changed: **false**
- Existing authored DesignSeed meaning changed: **false**
- Rollout authorized: **false**
- Canonical promotion authorized: **false**
- SEED-D: `PENDING_AUTHORIZED_COHORT`

## Corrected defects

1. CharacterLoad now excludes `REFERENCED_ONLY` from presence and counts focal scenes only when `focality == PRIMARY`.
2. `center_count` is recomputed over all distinct season SceneCards with threshold `season_scene_share >= 0.20`.
3. `compatible_work_ids` excludes the current work and uses the corrected 0 / 1–9 / 10–29 / 30+ bands.
4. BLIND and FULL_READ admissibility and alternative structures are independently authored.
5. `observed_value`, prediction match, mode accuracy, and leakage are recomputed by the executable gate.
6. Corpus index is mandatory; absence is HOLD rather than PASS.
7. V1.0 reports remain history and V1.0.1 is the only active execution authority.

## Recomputed results

| Work | CharacterLoad | center_count | BLIND | FULL_READ | leakage |
|---|---:|---:|---:|---:|---:|
| 내이름은김삼순 | 341 | 2 | 1.0 | 0.8 | -0.20 |
| 내여자친구는구미호 | 285 | 2 | 1.0 | 0.8 | -0.20 |

`-0.20` is one indicator step out of five, not a precise effect size. The two-work result cannot authorize SEED-D promotion.

## Active execution chain

```text
EXT6 Phase02 authority V1.0.1
→ exact schema registry V1.0.1
→ Phase01 exact derived gate
→ Phase02 deterministic seed gate V1.0.1
→ metadata/checksum atomic seal
→ fresh extraction rerun
```

Required files:

- `docs/standards/EXT6_V1_2_PHASE02_DESIGNSEED_SINGLE_AUTHORITY_V1_0_1.md`
- `docs/standards/EXT6_LAYER_GATE_EXECUTION_MATRIX_V1_0_1.md`
- `seqcard_ko/ext6_schema/EXT6_PHASE02_DESIGNSEED_EXACT_SCHEMA_REGISTRY_V1_0_1.json`
- `seqcard_ko/ext6_schema/PHASE02_INDICATOR_DERIVATION_RULES_V1_0_1.json`
- `seqcard_ko/_ext6_tools/ext6_phase01_derived_gate.py`
- `seqcard_ko/_ext6_tools/ext6_seed_gate_v1_0_1.py`
- `seqcard_ko/ext6_schema/EXT6_PHASE_AUTHORITY_POINTER.json`

## Gate requirements

A required gate that was not executed is `UNVERIFIED`, never PASS. The Phase02 gate must reject self-inclusion, wrong observed values, contaminated CharacterLoad, and invalid corpus indexes. All new works must use this chain before packaging.
