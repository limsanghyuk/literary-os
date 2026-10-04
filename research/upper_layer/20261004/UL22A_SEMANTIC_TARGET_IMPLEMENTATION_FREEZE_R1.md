# UL22-A Semantic Target Preservation Implementation Freeze R1

Date: 2026-10-04
Status: `IMPLEMENTED_SOURCE_FROZEN__FRESH_PRIMARY_NOT_YET_EXECUTED`

## Parent / 부모
Physical Authority(물리 권위): **SYNC-R77**
Active Runtime(활성 런타임): **UL20_F04_TRUSTED_ROOT_SUCCESSOR_RUNTIME_R1**
Parent Runtime SHA256: `aeb24721f9ef483daefe922cef1842f6459e07f0fd72e4e31d4bb4ed4094f200`

Preregistration:
`research/upper_layer/20261004/UL22A_SEMANTIC_TARGET_PRESERVATION_PREREG_R1.md`

## Frozen Source / 동결 소스
Changed Python files only:
1. `literary_os_runtime/adaptive_showrunner_ul16.py`
   - parent SHA256: `112a43d5609d2c35fb86c9f03f1494ba77f2da4118b02284c2db03334a6bf94a`
   - candidate SHA256: `62dfaf7408df2024c0a07ccf03ddb245b3d4a605810e97fe48e8ec2fb8681c5f`
2. `literary_os_runtime/canonical_ir_v2.py`
   - parent SHA256: `3ed8365fa3e9fa753eeab205e3d6fe1338ac36745135a205271fc41edb2b920d`
   - candidate SHA256: `8274b7aa64076969022bd479246d8bf02a44d8937e77c20d77c69e90a8a28898`

Canonical source diff SHA256:
`d396e4cc5d0844098fad1596a80a2934f446387bfa8aa41fe0e288276b481111`

Changed functions:
- adaptive: `_semantic_scene_anchor`, `adapt_to_episode_result`
- canonical IR: `_scene_payload`, `validate_canonical_ir_graph`, `project_scene_ir_for_renderer`, `validate_renderer_projection`

No sequence ordering, bundling, scene-count, F01, F04, F06, F07, open-touch, trusted-root, DB, Provider or Production code changed.

## Repair / 수리
Each transaction stage now carries:
`semantic_target_deltas = {information_target, relationship_target, social_target}`

This target contract is separate from:
`semantic_state_deltas`

Therefore a precursor scene can preserve the exact source target while its realized state delta remains generic/non-final.

Canonical SceneIR and renderer projection independently hash and validate the target object.

## Deterministic Pre-Freeze Gates / 결정론 동결 전 관문
UL21 failing semantic set:
- exact failing obligation families rechecked: Relationship 4 + Information 5 + Social 5 = **14 obligations**
- stage checks: **28**
- target loss: **0**
- precursor falsely realized: **0**
- resolving target realization errors: **0**
- result rows SHA256: `142d02fcc47bad7954910732d9ce5e5e0adc0149877d155c47798beab02db078`

Adversarial target-contract checks: **8/8 PASS**
- valid contract
- projection tamper detection
- target-hash mismatch detection primitive
- legacy empty-target compatibility
- irrelevant-metadata invariance
- relationship target not falsely realized
- information target not falsely realized
- social target not falsely realized

## Preservation Evidence / 보존 증거
Representative multi-kind adaptive execution, after removing only newly added target fields and diagnostic hashes:
- parent/candidate core output **bit-identical**
- core SHA256: `7fbba5d45d5b297b305303089847da9539460f9f33618a7b015caa3f94f66a53`
- sequence count: 5 / 5
- scene count: 36 / 36
- validation issues: [] / []

UL18 four-state disposition matrix:
- parent/candidate **bit-identical**
- due=true/can_defer=false -> SELECTED_DUE
- due=true/can_defer=true -> SELECTED_DUE
- due=false/can_defer=true -> DEFERRED
- due=false/can_defer=false -> SELECTED_OPEN_TOUCH

Transitive validator/source identity:
- R66 transaction decision hash unchanged: `764acb78dfa959bb3b7d01c7e6c4f3ded93b1e1e908fddafba58f72852a27a47`
- R66 stage-plan hash unchanged: `ac9bddec30e5ef2411172f7b63a2ae417198bf128494d671c302840dc4007529`
- UL20 trusted-root partition hash unchanged: `9627292d319e311293afe5efdf228aa21ae9a1cfee142f648c1f1c4c491f66ea`
- R68/F04 grouping hash unchanged: `730875950e3786bd2995d5e1fadc5ee3f9d520cf8548c4b2861ae3f63052dd51`
- R69/F06 scene-necessity hash unchanged: `302fd14a8c2e4fa7fd569f708c4ff549d54bbb077a48946da1d1e27e0ecc0c9e`
- obligation compiler/open-touch hash unchanged: `c44f99f06fb68c9539cc943e96ce2d3f8bb95ede39c769413dbb8dc520481a63`
- reverse reconstruction hash unchanged: `c05c4bb540315c70162c0a6cc10e084e8acef6e0c8b48af8c9d3c8c652f6f3ab`
- R67 dual-ledger module SHA256 unchanged: `ce38885171d0f318aeb2142ec16d119814be7fb736ebc361166007b4d2eea087`

Historical frozen-case bytes remain in Hub custody but are not raw-materializable through the current connector-to-container boundary. This freeze therefore records preservation by deterministic transitive source identity plus parent/candidate behavioral equivalence, not a second byte-level replay of those Hub-only inputs. This distinction must remain visible in the final claim.

## Compile / Package / 컴파일·패키지
Python compile: **45/45 PASS**

Research-only candidate package:
`LITERARY_OS_UL22A_SEMANTIC_TARGET_RESEARCH_CANDIDATE_R1.zip`
- bytes: **19,076,076**
- SHA256: `26caeaabb62a162bc0887101619418147606e2817ae30f4220bb1f64ac63d5a5`
- entries: **497**
- CRC/testzip: **PASS**

## Freeze Rule / 동결 규칙
Source above is immutable for UL22-A primary qualification.
After this commit:
- no target contract changes;
- no hash/validation rule changes;
- no tuning from primary cases.

Authority effect: **NONE**.
SYNC-R77 remains Physical Authority.

Status:
`UL22A_SOURCE_FROZEN__SEMANTIC_TARGET_TYPED__14_OF_14_TARGETS_PRESERVED__ADVERSARIAL_8_OF_8__45_OF_45_COMPILE__FRESH_PRIMARY_NEXT`
