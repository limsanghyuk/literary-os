# EXT6 V1.2 Phase02 DesignSeed Single Authority V1.0.1

- Authority ID: `EXT6-V1.2-PHASE02-DESIGNSEED-AUTHORITY-V1.0.1`
- Status: **AUTHORIZED_PILOT_ONLY_CORRECTED**
- Date: 2026-08-01
- Supersedes for active execution: `V1.0`
- Stage01~04 changed: **false**
- Existing authored DesignSeed meaning changed: **false**
- Canonical promotion allowed: **false**

## Correction scope

V1.0 correctly defined the sidecar separation, blind-before-full order, evidence boundaries, and no-canonical-promotion policy. V1.0.1 corrects only derivation, admissibility, and executable gate semantics identified by the two-work independent review.

1. CharacterLoad present modes are `ONSCREEN`, `VOICE_ONLY`, `PHONE_OR_REMOTE`, `ARCHIVAL_OR_MEMORY`; `REFERENCED_ONLY` is excluded.
2. Focal count uses `focality == PRIMARY` only.
3. `center_count` uses all distinct season SceneCards as denominator and distinct valid-present scene keys per character as numerator; threshold is `>=0.20`.
4. `compatible_work_ids` excludes the current work. Bands are 0 / 1–9 / 10–29 / 30+.
5. BLIND and FULL_READ admissibility sets and alternative structures are independently authored.
6. The gate recomputes center count, opposition persistence, conflict persistence, prediction match, accuracy, and leakage. Terminal ending/cost observations require a hash-bound evidence audit.
7. `--corpus-index` is mandatory. Missing or unreadable corpus index is HOLD, never PASS.
8. Five indicators imply a 0.20 accuracy step. Two works cannot decide SEED-D. `PENDING_AUTHORIZED_COHORT` remains active.

## Mandatory execution

```text
Phase01 authored/cast/load gate
→ blind SEED-A/B/C seal
→ full-read SEED-A/B/C seal
→ indicator evidence audit
→ deterministic SEED-D evaluation
→ metadata/checksum atomic seal
→ fresh extraction rerun
```

The authored seed records remain advisory. No rollout or canonical promotion is authorized.
