# EXT6 V1.2 / Phase02 V1.0.2 — 뉴하트 완료 검토

- Work: `뉴하트`
- Status: `PASS_CANDIDATE_WITH_BLIND_CONTEXT_DISCLOSURE`
- Existing Stage01~04 modified: **false**
- Canonical promotion: **not authorized**

## Phase01

- Episodes: 23
- SceneCards: 1,238
- EntityBridge entities: 55
- CastPresence records: 3,937
- CharacterLoad records: 545
- Source heading alignment: exact 1,080 / fuzzy ordered 155 / interpolated missing headings 3 / extra source headings 2
- Present/focal contract mismatches: 0

## Phase02 observations

- center_count: 3
- center characters: 이은성, 남혜석, 최강국
- opposition_persistence: HIGH
- center-pair relation coverage: 이은성–남혜석 21/23
- conflict_persist: SEASON_LONG
- ending_direction: ACHIEVE_WITH_COST
- cost_realized: PROFESSIONAL_IDENTITY_FAMILY_LOSS_AND_INSTITUTIONAL_RESPONSIBILITY
- analytical BLIND accuracy: 1.0
- FULL_READ accuracy: 1.0
- analytical leakage_estimate: 0.0

The execution context inspected downstream Stage03/04 material before the BLIND record was sealed. The EP01–02 record is retained as a context-disclosed constrained reconstruction and is excluded from SEED-D cohort statistics. It must not be represented as a pristine blind run.

## Validation

- Pre-ZIP strong gate: 33/33 PASS
- Fresh extraction validators: 32/32 PASS
- Integrated ZIP paths: 25,172/25,172 exact
- Root checksums: 25,155, mismatch 0
- JSON/JSONL parse errors: 0
- Stage01~04 modified: 0
- Unauthorized existing changes: 0
- Validation tree mutation: 0

## Authority limits

- Rollout authorization: false
- Canonical promotion authorization: false
- Cohort status: `PENDING_AUTHORIZED_COHORT`
- Target cohort eligibility: false (`EXCLUDED_CONTEXT_DISCLOSED`)
