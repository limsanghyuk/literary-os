# CT-07R preregistration — DB98 reinforcement replication + thick negative control

Document ID: `LOS-CT07R-PREREG-V1.0`  
Date: 2026-08-07  
Status: `PREREGISTERED_BEFORE_THICK_PACKET_SCORING`  
Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Active reinforcement schema: `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1`

## 0. Purpose

This is the global replication gate required by DB98 Reinforcement Master Authority §8 before bulk 98-work thick semantic authoring.

Question: does the CT-07 effect — deeper sequence design carrying substantially more scene-functional information than the current thin encoding — reproduce on two new works, while a deliberately mismatched thick design fails to steer the target?

This document freezes works, anchors, negative-control mapping, metrics, and decision thresholds before independent rendering/scoring. Thresholds must not be relaxed after seeing scores.

## 1. Works

Two works not used in the CT-07 primary pilot are selected:

1. `101번째프로포즈` — romance/melodrama axis; also first work in DB98 reinforcement authority order.
2. `38사기동대` — crime/con/heist/non-melodrama axis; early work in authority order.

Selection satisfies the authority's diversity recommendation and keeps the replication close to the future rollout order.

## 2. Anchor selection rule

Anchors were selected structurally before thick semantic authoring: approximately 10/30/50/70/90% of each season, then a lower-middle sequence within the selected episode and a lower-middle member scene as the scoring anchor. Selection did not use future thick-record quality.

### 101번째프로포즈

- EP02 `101번째프로포즈_02_S05`, anchor scene 28
- EP05 `101번째프로포즈_05_S06`, anchor scene 34
- EP08 `101번째프로포즈_08_S07`, anchor scene 39
- EP11 `101번째프로포즈_11_S07`, anchor scene 51
- EP14 `101번째프로포즈_14_S07`, anchor scene 42

### 38사기동대

- EP02 `38사기동대_02_S05`, anchor scene 39
- EP05 `38사기동대_05_S08`, anchor scene 67
- EP08 `38사기동대_08_S09`, anchor scene 88
- EP12 `38사기동대_12_S08`, anchor scene 61
- EP15 `38사기동대_15_S07`, anchor scene 56

## 3. Thick design contract

Each correct design is source-grounded and serialized under schema V1.0.1 with:

- `cast[]`
- `event`
- `info_shift[]`
- `plant_payoff[]`
- `scene_notes[]`

Existing human `member_scene_nos`, thin sequence data, SceneCards, Character/Relationship data, PayoffCandidates and CrossEpisodeEdges are evidence/indexes, not substitutes for source verification.

## 4. Arms

Minimum confirmatory arms per target anchor:

- `A`: no design / baseline context.
- `B`: human SceneCard reference arm, same role as CT-07 anchor.
- `T`: correct thick design for the target sequence.
- `TN`: mismatched thick negative control.

If the execution environment reproduces the full CT-07 generated-card route, additionally report `TG` (thick → generated SceneCard → render). Direct-thick `T` remains mandatory because CT-07 showed substantial compression loss.

No arm may read the score key or another arm's output before rendering.

## 5. Thick negative-control mapping — frozen before scoring

Negative control is a deterministic cyclic +1 substitution **within the same work**, preventing genre/work identity from becoming the control signal.

### 101번째프로포즈

- target EP02-S05 ← thick design EP05-S06
- target EP05-S06 ← thick design EP08-S07
- target EP08-S07 ← thick design EP11-S07
- target EP11-S07 ← thick design EP14-S07
- target EP14-S07 ← thick design EP02-S05

### 38사기동대

- target EP02-S05 ← thick design EP05-S08
- target EP05-S08 ← thick design EP08-S09
- target EP08-S09 ← thick design EP12-S08
- target EP12-S08 ← thick design EP15-S07
- target EP15-S07 ← thick design EP02-S05

The mismatched packet is never rewritten to fit target scene numbers. The control runner must present it explicitly as foreign/mismatched design context; it is experimental control data, not a valid ThickSequenceExtension for the target `seq_id`.

## 6. Primary endpoint

Use the same core concept as CT-07: functional fidelity against a sealed target-function key, with blinded independent scoring.

For a valid batch, human SceneCard signal must remain positive: `B - A >= 0.5` on the batch's own scale.

Define normalized relative position:

`r_T = (T - A) / (B - A)`

If a generated-card route is included:

`r_TG = (TG - A) / (B - A)`

Negative-control separation:

`D_N = T - TN`

## 7. Preregistered decision rule

Replication PASS requires all of the following:

1. batch validity: `B - A >= 0.5`;
2. correct thick direct arm `r_T >= 0.70` overall;
3. both works individually show positive thick signal, and neither work has `r_T <= 0.30`;
4. thick negative control is separated: `TN < T` overall and in both work-level summaries;
5. no post-hoc anchor deletion changes a FAIL to PASS; all sensitivity exclusions are reported rather than silently applied.

Strong replication is reported if `r_T >= 1.0` while the negative control remains below the correct arm.

If the generated-card route is run, `r_TG >= 0.70` is separately reported as reproduction of the CT-07 top-down-through-card result; failure of `TG` does not erase a direct-thick PASS, but it confirms compression/generation loss and affects architecture choice.

Replication FAIL if batch validity holds but condition 2 or 4 fails. If batch validity fails, result is `INVALID_MEASUREMENT`, not PASS/FAIL.

## 8. Required reporting

- overall A/B/T/TN (and TG if run)
- overall r and negative-control separation
- work-level r/separation
- anchor-level raw scores
- sensitivity report
- scorer agreement/reliability
- packet and blind-map SHA256
- deviations from preregistration

## 9. Independence and environment boundary

Source-grounded thick authoring may be performed in the DB reinforcement session. Rendering and scoring must remain independent/blinded from the authored target-function key and from each other's outputs.

If the active environment cannot provide independent renderer/judge channels, it may prepare and seal the authoring/control packets but **must not fabricate PASS/FAIL**. The global state remains `FULL_THICK_ROLLOUT_BLOCKED_PENDING_CT07_REPLICATION` until valid independent results exist and the developer accepts the replication.

## 10. Rollout consequence

PASS + developer acceptance permits updating the DB98 root pointer/work index to `FULL_THICK_ROLLOUT_AUTHORIZED`, after which full thick semantic reinforcement proceeds in `authority_order`.

FAIL keeps bulk thick authoring blocked and requires versioned redesign. Existing Stage01–04, human SceneCards, thin sequences, and experimental packets remain preserved.
