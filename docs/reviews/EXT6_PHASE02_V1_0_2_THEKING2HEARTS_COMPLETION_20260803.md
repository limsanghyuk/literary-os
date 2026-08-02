# EXT6 V1.2.1 / Phase02 V1.0.2 — 더킹투하츠 완료 검토

- Work: `더킹투하츠`
- Status: `PASS_CANDIDATE_WITH_BLIND_CONTEXT_DISCLOSURE`
- Existing Stage01~04 modified: **false**
- Canonical promotion: **not authorized**

## Execution-limit containment

The 20 episodes were authored and validated as two Phase01 blocks:

1. EP01–10
2. EP11–20

Phase01, Phase02, regression, packaging, and fresh extraction were executed separately. Completed batches were retained and were not rerun after an execution-limit interruption.

The source uses `S#N` headings and tab-delimited speaker labels. A work-specific parser was used rather than reusing the later-script `씬N` rule from 대장금.

## Phase01 V1.2.1

- Episodes: 20
- SceneCards: 1,110
- EntityBridge entities: 709
- CastPresence records: 3,692
- CharacterLoad records: 1,226
- Empty cast scenes: 18
- Source alignment: ONE_TO_ONE 1,074 / FUZZY_ORDERED 34 / INTERPOLATED_MISSING_HEADING 2
- Enum, source evidence, coverage, registry SHA, and exact CharacterLoad mismatches: 0

## Phase02 observations

- center_count: 3
- center characters: 이재하, 김항아, 은시경
- center shares: 이재하 0.4874 / 김항아 0.3667 / 은시경 0.2243
- opposition_persistence: HIGH
- center-pair direct RelationshipArc coverage: 김항아–이재하 20/20
- conflict_persist: SEASON_LONG
- ending_direction: ACHIEVE_WITH_COST
- cost_realized: `BROTHER_AND_GUARD_LOSS_THRONE_BURDEN_WAR_RISK_AND_RELATIONAL_SACRIFICE`
- analytical BLIND accuracy: 1.0
- FULL_READ accuracy: 1.0
- analytical leakage_estimate: 0.0

The proper-name gate initially rejected the registry role label `장교` in judged prose. The wording was generalized to role-independent structural language without weakening the gate or changing the analysis.

The execution context inspected downstream Stage03/04 material before the BLIND record was sealed. The EP01–02 record is retained as a context-disclosed constrained reconstruction and excluded from SEED-D cohort statistics. It must not be represented as a pristine blind run.

## Validation

- Target Phase01 gate: PASS
- Target Phase02 seal/evaluate: 4/4 PASS
- General + Phase01 + Phase02 regression: 70/70 PASS
- Negative self-tests: 10/10 PASS
- Pre-ZIP strong gate: 84/84 PASS
- Fresh extraction validators: 70/70 PASS
- Integrated ZIP paths: 25,951/25,951 exact
- Root checksums: 25,950, mismatch 0
- JSON/JSONL parse errors: 0
- Stage01~04 modified: 0
- Unauthorized existing changes: 0
- Validation tree mutation: 0
- `pycache` / `.pyc`: 0

## Authority limits

- Rollout authorization: false
- Canonical promotion authorization: false
- Cohort status: `PENDING_AUTHORIZED_COHORT`
- Target cohort eligibility: false (`EXCLUDED_CONTEXT_DISCLOSED`)

## Next alphabetical target

The next unaugmented target after `더킹투하츠` is `도깨비`.
