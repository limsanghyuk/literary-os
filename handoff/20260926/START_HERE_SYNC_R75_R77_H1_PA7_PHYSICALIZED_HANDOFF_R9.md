# START HERE — SYNC-R75 PHYSICAL / R77-H1 PA7 CHECKPOINT HANDOFF R9

Date: 2026-09-26
Status: **CANONICAL NEW-SESSION HANDOFF**

## 0. CURRENT AUTHORITY

- Physical Authority: **SYNC-R75**
- Parent: SYNC-R74
- Delivery/redownload verification: **PASS 9/9 / mismatch 0**
- Manifest SHA256: `f4db8fd53773fce3acdf846469f9b7bbea5c4b8cec04eda8a88591c2c7a9c2cc`
- Trust Root SHA256: `7c637bc25c9ffd7832727fdc5ccdb872b8d805fc0dd05b7882f4ec9cc59adc59`
- Package-set root SHA256: `7793c0f2b32bd3159c6ff595395e8b89debbed58c1e1e058bd6123fdb03caf04`
- Logical C2 SHA256: `5f6d171c19f230167745956dd674b319e1407705137db292058c73431f916761`
- Library physical custody: `/SYNC_R75_CURRENT_PHYSICAL_9PACKAGES`

SYNC-R75 is a physical snapshot ID. Historical Research Experiment R75 is a separate namespace.

## 1. ENGINE / DATABASE / FORMAL — UNCHANGED

- Active Runtime: **exact R69**
- Runtime SHA256: `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Research DB: **DB64-R131 research-only**
- Research DB SHA256: `4986730dc062610a2395960af83615dddaf986f53172914d2175b459fdaf9d7b`
- Operational Level-3: `SUSPENDED__REQUALIFICATION_REQUIRED`
- Formal scored total: 137
- Latest formal scored: R138
- Formal R140: NOT_STARTED

No PA6/PA7 result changes Runtime/Production/DB59/Formal authority.

## 2. SYNC-R75 PACKAGE SET

Read order: CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2

1. CONTROL — `LITERARY_OS_CURRENT_CONTROL_POST_PA6_PA7_CHECKPOINT_SYNC_R75_20260926.zip`
   SHA256 `770b70a15a62e98165cf064522ee3de52941d69dd6c35328c7d5e447231f424d`
2. A — `LITERARY_OS_CURRENT_PART_A_POST_PA6_PA7_CHECKPOINT_SYNC_R75_20260926.zip`
   SHA256 `4d594927909453b71fedb19a82bf7a3cda0e96b73d5258b2ed88fc4f25c09958`
3. B1 — `LITERARY_OS_CURRENT_PART_B1_SYNC_R75_INHERITED_BYTE_UNCHANGED_FROM_SYNC_R74.zip`
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. B2 — `LITERARY_OS_CURRENT_PART_B2_POST_PA6_PA7_CHECKPOINT_SYNC_R75_20260926.zip`
   SHA256 `ad757c87f0d99896c42c0788e7ec94252a9290f5dfb2953816301ba525f9af38`
5. C1 — `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_SYNC_R75_EXACT_R69_20260926.zip`
   SHA256 `262b12530d12c96299fd583d41f4c3fcf7e689e66ee6e63614c710b12d607c63`
6. C2-A — `LITERARY_OS_CURRENT_C2_BINARY_A_SYNC_R75_POST_PA6_PA7_CHECKPOINT_20260926.bin`
   SHA256 `b9bb7a76f07c391bd3814257f068cbf69d569aa716039827a3d2c207647fe2b4`
7. C2-B — `LITERARY_OS_CURRENT_C2_BINARY_B_SYNC_R75_POST_PA6_PA7_CHECKPOINT_20260926.bin`
   SHA256 `ed433113e0a15918b38755a80ea432fc661364b65bf233a8f16c9b89e80fa156`
8. D1 — `LITERARY_OS_CURRENT_PART_D1_DB59_SYNC_R75_INHERITED_BYTE_UNCHANGED_FROM_SYNC_R74.zip`
   SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. D2 — `LITERARY_OS_CURRENT_PART_D2_DB59_SYNC_R75_INHERITED_BYTE_UNCHANGED_FROM_SYNC_R74.zip`
   SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Changed: CONTROL/A/B2/C1/C2-A/C2-B.
Byte-identical from SYNC-R74: B1/D1/D2.
Existing parent members are preserved; new recovery evidence is additive under `SYNC_R75_CURRENT_RECOVERY_20260926/`.

## 3. PA6 CLOSED

Final PA6:
`CLOSED_FAIL__FOCUS_EFFECT_SIZE_GATE`

- Absolute Gate: PASS
- Paired Directional: PASS — Treatment preferred 3/3
- Recoverability: PASS
- Critical violation consensus: 0
- Focus Gate: FAIL
- Frozen requirement: pooled median delta >= +0.50 on >=4/6 focus axes
- Actual: 0/6

Do not weaken the gate post hoc.

## 4. PA7 EXACT CHECKPOINT

Fresh synthetic work:
**SYNTH_PA7_LAST_BUS_RADIUS / 막차의 반경**

Frozen scene sample:
SC05 / SC12 / SC21 / SC29 / SC38 / SC46.

Control R4 is immutable:
- PASS
- 40,055 chars / 9 sequences / 50 scenes
- SHA256 `41f45e7d00dbd9e4a89837cac0c7516c18c5f42fd1edd066015f824f27d36495`

Treatment R1:
- FAIL under 40K only
- 35,656 chars / 9 sequences / 50 scenes
- SHA256 `34590dc4892737e6ec24309c50088cc5a0ba0b508e30cd482568a333a006759f`

Completion D:
- SEALED / NOT COMPOSED
- 3,174 insert-text chars
- SC04 / 07 / 18 / 26 / 34 / 37 / 43 / 49
- frozen blind sample scenes intentionally not targeted

PA7 external judge outputs: 0/3.
No PA7 mapping exists yet.

## 5. H1 GUARD

The six isolated launch packets inherited from SYNC-R74 remain preserved as historical evidence but were built with the former >=35K floor.

Status:
`STALE_FOR_EXECUTION__35K_FLOOR`

Current production-scale floor: **>=40,000 chars**, no upper cap, padding prohibited.

H1 primary C/T outputs: 0.
Human target: unopened.
PM0: preregistered, not executed.
Real-provider H1 remains blocked.

## 6. EXACT NEXT

1. Verify SYNC-R75 manifest and Control R4 SHA.
2. Do not mutate Control R4.
3. Compose **Treatment R2 = existing Treatment R1 + sealed Completion D only**.
4. Validate exact chars / 9 sequences / 50 scenes / metadata leak 0 / duplicate checks.
5. If Treatment R2 is still below 40K, preserve the failed R2 and preregister the next bounded repair before new prose.
6. After Treatment passes, verify arm length difference <=10% of shorter arm.
7. Build balanced hidden PA7 J01/J02/J03 packets using the already frozen scene sample.
8. Run three fresh independent judges, seal 3/3, then reveal mapping.
9. Apply unchanged Absolute / Paired / Focus(+0.50 on >=4/6) / Recoverability gates.
10. Only after provider-analog qualification rebuild the six H1 launch packets at 40K.

## 7. FAILURE RECOVERY RULES

- ClientError / TransportTimeout => `RUNTIME_TRANSPORT_HOLD`, not scientific FAIL.
- Minimal health check → verify last atomic checkpoint → resume only failed step.
- Multi-create ambiguous failure => fetch path first; create only missing files.
- Serialization/parser defects must not be relabeled as screenplay quality failure.

## Recovery token

`PHYSICAL_SYNC_R75_9_OF_9_PASS__PA6_CLOSED_FOCUS_FAIL__PA7_CONTROL_R4_40055_PASS__TREATMENT_R1_35656_UNDER40K__COMPLETION_D_SEALED_NOT_COMPOSED__PA7_EXTERNAL_0_OF_3__H1_TARGET_UNOPENED__RESUME_TREATMENT_R2_ONLY`
