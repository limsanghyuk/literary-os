# DB98 Reinforcement Single Authority V1

This directory is the sealed continuation package for reinforcing the existing 98-work Korean-drama analysis database.

## Read order

1. repository-root `DB98_REINFORCEMENT_CURRENT_AUTHORITY_POINTER.json`
2. `DB98_REINFORCEMENT_MASTER_AUTHORITY_V1.md`
3. `schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1.json`
4. `DB98_REINFORCEMENT_EXECUTION_AND_VALIDATION_V1.md`
5. `DB98_REINFORCEMENT_WORK_INDEX_V1.json`
6. `NEW_SESSION_BOOTSTRAP.md`
7. `AUTHORITY_MANIFEST.json`

## Scope

- Existing DB98 only: 98 works / 1,814 episodes / 114,371 SceneCards.
- Does not supersede the active Stage01–04 drama-analysis authority.
- Protects canonical Stage01–04 schemas and meaning.
- Defines reinforcement reason, CT-06H/CT-07 evidence, thick-sequence extension, planner-input reassembly, subplot/boundary data, runtime projection, validation, checkpointing, and continuation.

## Current rollout state

`FULL_THICK_ROLLOUT_BLOCKED_PENDING_CT07_REPLICATION`

Immediate next authoritative action:

`CT07_REPLICATION_WITH_THICK_NEGATIVE_CONTROL`

Bulk 98-work thick authoring begins only after preregistered replication PASS + developer acceptance + explicit update of the root pointer/work index.

## Key research result frozen by this authority

- CT-06H thin top-down: `r=0.211` — not established.
- CT-07 thick top-down: `r_L2G=0.807` — established in two-work pilot.
- CT-07 thick direct render: `r=1.63` relative to human SceneCard anchor `1.00`.
- CT-07 L3 ceiling: `4.90/5`.

The implication is not “delete sequences” or “delete SceneCards”. It is: preserve human GT, replace the thin generation contract with a validated deeper planning representation if replication confirms it.
