# UL22-A — Multi-Stage Semantic Target Preservation Repair Preregistration R1

Date: 2026-10-04
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Trigger / 발동 원인
UL21 found 14 semantic-target preservation failures in every variant while current internal adaptive validation and Canonical IR validation still passed.

Historical UL16 R3 contract required concrete Relationship / Information / Social deltas to survive into every transacting scene.
Current R58+ multi-stage logic intentionally substitutes generic pressure text on `resolves=false` precursor scenes.

Responsible boundary:
`R58_MULTI_STAGE_PRE_RESOLUTION_SEMANTIC_TARGET_ERASURE__CANONICAL_TARGET_VS_REALIZED_DELTA_NOT_TYPED`

## Repair objective / 수리 목표
Preserve the exact caller-frozen semantic target through every transaction stage **without falsely claiming that the target state has already been realized**.

## Allowed intervention / 허용 범위
Only:
- adaptive semantic scene-anchor target fields;
- adaptive -> EpisodeResult lowering for semantic targets;
- Canonical SceneIR semantic target contract + hashes;
- renderer projection/validation needed to preserve those fields;
- tests/diagnostics.

Forbidden:
- sequence selection/order/bundling;
- scene count/stage selection/action generation;
- F04/F06/F01/F07;
- UL18 open-touch selection/closure;
- trusted-root semantics;
- spacetime ordering;
- DB/Provider/Production.

## Typed contract / 형식 계약
Each transacting scene must carry:
- `semantic_target_deltas.information_target`
- `semantic_target_deltas.relationship_target`
- `semantic_target_deltas.social_target`

Rules:
- target field equals the concrete source obligation delta when provided;
- it survives every stage, including precursor scenes;
- `semantic_state_deltas` continues to mean **realized current state change**;
- precursor scene may keep generic/no realized change;
- resolving scene may realize the concrete source delta;
- target and realized fields must never be conflated.

Canonical IR must hash/validate the target-delta object independently.

## Frozen gates / 동결 관문
1. UL21 semantic preservation fixture: 0 target-loss issues.
2. Precursor scenes do not falsely report target as already realized.
3. Resolving scenes realize concrete source delta where applicable.
4. Canonical IR target hash PASS.
5. Renderer projection target hash PASS.
6. UL20 F04 fresh 16/16 preserved.
7. R68 historical 16/16 preserved.
8. R69 F06 16/16 preserved.
9. UL18 open-touch 4-state preserved.
10. scene/sequence counts and architecture hashes excluding added diagnostic target fields remain behaviorally invariant.
11. Python compile 45/45 PASS.
12. unrelated Python source drift = 0 except files strictly required for typed target propagation.

## Claim boundary / 주장 경계
UL22-A PASS repairs semantic contract drift only. It does not solve UL21 spacetime failure and cannot reopen blind dispatch until UL22-B closes.

Status token:
`UL22A_PREREGISTERED__SEMANTIC_TARGET_VS_REALIZED_DELTA_TYPED_REPAIR__NO_OUTPUTS`
