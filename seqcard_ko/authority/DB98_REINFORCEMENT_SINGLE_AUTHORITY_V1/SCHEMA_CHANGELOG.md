# DB98 Reinforcement Schema Changelog

Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`

## 1.0.1 — 2026-08-07

Status: `ACTIVE_SCHEMA_HOTFIX / NO_EXISTING_THICK_DATA_MIGRATION_REQUIRED`

Supersedes schema registry shape version `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1` only. The method authority remains V1.0.0.

### Trigger

During the first source-grounded CT-07 replication application on `101번째프로포즈`, the V1 `info_shift.mode` enum could not represent three ordinary information-state operations without semantic distortion:

- a previously known fact/experience becoming active again through memory,
- a character forming a wrong interpretation without another actor actively deceiving them,
- a character deriving a conclusion from available evidence without explicit disclosure.

Mapping these to `LEARN` or `MISLEAD` would corrupt meaning.

### Added modes

- `RECALL` — previously known information/experience is narratively reactivated; not new learning.
- `MISINTERPRET` — the subject forms an incorrect interpretation without requiring an active deceiver.
- `INFER` — the subject derives a new conclusion from available evidence without explicit disclosure.

`MISLEAD` remains reserved for active deception by another actor/system.

### Migration

No canonical or rollout thick-sequence records existed under V1 when this defect was found. Therefore data migration count is **0**. The old V1 registry is preserved as historical evidence; all new replication and reinforcement records must use V1.0.1 until explicitly superseded.

### Core impact

None. Stage01–04 schemas, human SceneCards, thin `authored_seq`, EXT6, and PHASE02 are unchanged.
