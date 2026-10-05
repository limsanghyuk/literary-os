# UL22-A Semantic Target Preservation Implementation Freeze R1

Date: 2026-10-05
Status: `IMPLEMENTED_SOURCE_FROZEN__FRESH_PRIMARY_NOT_YET_CREATED`

## Parent / 부모
Physical Authority(물리 권위): **SYNC-R77**
Active Runtime(활성 런타임): **UL20_F04_TRUSTED_ROOT_SUCCESSOR_RUNTIME_R1**
Parent Runtime SHA256:
`aeb24721f9ef483daefe922cef1842f6459e07f0fd72e4e31d4bb4ed4094f200`

## Frozen source / 동결 소스
Changed files only:
- `literary_os_runtime/adaptive_showrunner_ul16.py`
- `literary_os_runtime/canonical_ir_v2.py`

Parent -> Candidate source SHA256:
- adaptive: `112a43d5609d2c35fb86c9f03f1494ba77f2da4118b02284c2db03334a6bf94a`
  -> `c57ccc62371f10e8ab169a198aabe093b48495be9eec4a60e179d07d325c6642`
- canonical_ir_v2: `3ed8365fa3e9fa753eeab205e3d6fe1338ac36745135a205271fc41edb2b920d`
  -> `1fb1289bc656f9d09bbb5259513f718607f001793f15281ea033a2451a3963b4`

Canonical diff SHA256:
`ed5d39a07a3459231f281173ef086b2ad947e48834a5a0a28a91e5af0d2cd53c`

Frozen candidate runtime ZIP:
- bytes: **18,753,461**
- SHA256: `5702938e6134ad181bb1ebe9f64c74b7832f94c194ea2a759d61853b5a85c5a4`
- entries: **452**
- CRC: PASS

## Intervention / 개입
Adaptive scene anchors now carry a separate:
`semantic_target_deltas = {information_target, relationship_target, social_target}`

Canonical SceneIR independently stores/hashes:
- `semantic_state_deltas` = realized current state change;
- `semantic_target_deltas` = concrete intended semantic target.

Renderer projection preserves and validates the target hash independently.

No change was made to:
- sequence selection/order/bundling;
- scene count/stage choice/action generation;
- F04 grouping;
- F06 scene necessity;
- F01/F07;
- UL18 open-touch disposition/closure;
- trusted-root partition semantics;
- DB/Provider/Production.

## Deterministic pre-freeze gate / 동결 전 결정론 관문
Result SHA256:
`d3c9eae63841fa51e8ac0baad666f3b2f6c95fcfc9f2a9a33790980124a6417f`

PASS:
- Relationship precursor target preserved / not falsely realized;
- Relationship resolve target preserved / realized;
- Information precursor/resolve same rule;
- Social precursor/resolve same rule;
- parent/candidate legacy behavior excluding added target field: **14/14 identical**;
- Canonical target hash PASS;
- Renderer target hash PASS;
- Python compile **45/45 PASS**.

## Freeze rule / 동결 규칙
This source is immutable for UL22-A qualification.
Fresh primary cases may only be created after this commit.
No threshold, field semantics, source code, or adapter rule may be tuned after fresh inputs are sealed.

Authority effect: **NONE**.
SYNC-R77 remains Physical Authority.

Status token:
`UL22A_SOURCE_FROZEN__SEMANTIC_TARGET_TYPED_SEPARATELY_FROM_REALIZED_STATE__45_OF_45_COMPILE__FRESH_PRIMARY_NOT_CREATED`
