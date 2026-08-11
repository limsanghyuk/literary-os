# work_state / manifest / selfcheck / audit evidence 계약 V1

문서 ID: `WORK_STATE_MANIFEST_SELFCHECK_CONTRACT_V1_20260811`

## 1. 역할 분리

### work_state
현재 진행 상태와 재개 포인터.

### manifest
현재 활성 산출물의 inventory/hash/authority/quality/provenance/downstream 사실.

### selfcheck
저작 직후의 구조+의미 자체점검. 독립 감사와 동일한 것이 아니다.

### independent audit
원본을 다시 열어 저작 산출물의 의미와 출처를 독립 확인한 증거.

### validation report
결정론적으로 검사 가능한 schema/FK/hash/coverage/parity/future-leak 결과.

## 2. work_state 최소 필드 의미

active package가 이미 exact work_state schema를 갖고 있으면 그것을 우선한다. 그렇지 않은 신규 handoff에서는 최소한 다음 사실을 담는다.

```json
{
  "schema": "<active work_state schema>",
  "work_id": "...",
  "authority_id": "...",
  "work_state": "...",
  "last_completed_episode": 0,
  "last_completed_block": null,
  "stage_status": {},
  "thick_status": "...",
  "planner_runtime_status": "...",
  "exact_schema_status": "...",
  "provenance_status": "...",
  "semantic_audit_status": "...",
  "non_target_immutability_status": "...",
  "holds": [],
  "next_action": "...",
  "updated_at": "..."
}
```

핵심은 `next_action`이 정확해야 한다는 것이다.

## 3. manifest 최소 역할

- exact schema id
- authority id
- episode/record counts
- artifact hashes
- provenance counts/errors
- quality metrics + interpretation
- downstream R5/R8 state/hashes
- baseline preservation
- promotion/supersession lineage

## 4. episode selfcheck

구조:

- parse
- exact keys
- IDs/FK
- scene/sequence coverage
- source refs

의미:

- generic text 여부
- source fidelity
- cast function specificity
- info before/after
- payoff/link direction
- sequence handoff
- scene note placement function

## 5. block strong audit

- source/provenance distribution drift
- semantic grain drift
- cross-episode threads
- character/relationship continuity
- repeated boilerplate
- Stage01~04 immutability
- R5 future leakage + debt carry-over
- R8 exact parity

## 6. final work audit

완료 전 최소 증거:

1. exact schema validation
2. source/provenance validation
3. semantic quality audit
4. THICK quality/diversity diagnostics
5. PlannerInput validation
6. Runtime parity/coverage validation
7. non-target immutability
8. manifest/hash integrity
9. ZIP integrity
10. fresh extraction validation

## 7. 상태 추천

- `AUTHORING_IN_PROGRESS`
- `EPISODE_CHECKPOINT_LOCKED`
- `BLOCK_CHECKPOINT_LOCKED`
- `HOLD_SOURCE`
- `HOLD_AUTHORITY_DRIFT`
- `HOLD_SEMANTIC_FAILURE`
- `REGEN_REQUIRED`
- `PASS_CANDIDATE_READY_FOR_REVIEW`
- `CANONICAL` (active authority/user approval이 요구할 때만)
- `FRESH_EXTRACT_PASS`

프로젝트의 active package가 다른 enum을 이미 강제하면 그 enum을 사용한다.
