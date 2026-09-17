# UL-16 R58C Scene Depth & Material Diversity Repair Receipt R1

Date: 2026-09-17
Status: `PASS_AFTER_ROOT_CAUSE_REPAIR__RESEARCH_ONLY__NO_PHYSICAL_AUTHORITY_CHANGE`
Parent physical authority: SYNC-R57.
Execution lane: R7 Small-Source Research Lane.

## Root causes isolated
R57 successfully removed quota padding and obligation cloning, but over-corrected repetition by treating one due obligation as effectively one Scene transaction. That produced insufficient Scene depth on a human-median workload.

R58 then allowed one obligation to span multiple distinct transaction stages while requiring exactly one final resolution. This restored Scene depth without quota padding.

R58B isolated a second root cause: entity/id substitutions could hide mechanically cloned story material. A normalized semantic-pattern signature was added so `C01 does X` / `C13 does X` clones are not counted as diverse material.

R58C isolated a third root cause: even when upstream story material was genuinely different, `_stage_action()` ignored the supplied `visible_action` and collapsed Scenes into a small family of kind-level action templates. This reintroduced mechanical similarity at the Scene-action boundary.

## Frozen preregistration
R58C prereg SHA256:
`a7f07cf0435338b7c0a126ea1ed261a8711210f24f679c64bba759e3905f0a4f`

Frozen diverse-material fixture:
`R58B_DIVERSE_MATERIAL_FIXTURE_R1.json` — 37 distinct cutoff-safe obligations, all with supplied visible physical actions.

Human reference retained from the DB64 learning bundle:
- Princess Man: 24 episodes / 349 sequences / 1,784 scene-function propositions;
- within-episode nearest-neighbor scene-function Jaccard mean ≈ 0.0938, median ≈ 0.0769, p90 ≈ 0.129;
- Princess Man episode Scene median ≈ 75;
- DB64 61-work episode Scene median ≈ 64.8.

The human scene-function metric and Candidate concrete-action metric are not identical text fields, so exact equality is not claimed.

## R57 -> R58 -> R58B -> R58C findings
R57 human-median-style fixture:
- about 12-13 sequences / 37 scenes;
- repeated padding 0 but underdeveloped Scene depth;
- generic action skeleton dominated the action surface.

R58 multi-stage repair:
- 12 sequences / 66 scenes;
- each due obligation resolves exactly once;
- exact action duplicates 0;
- quota padding 0;
- nearest-neighbor concrete-action Jaccard mean ≈ 0.6048.

R58B material-pattern gate:
- entity/id-normalized mechanical clone fixture: fail-closed `MECHANICAL_OBLIGATION_PATTERN_REPEAT`;
- genuinely diverse fixture: 12 sequences / 66 scenes PASS;
- due resolved once PASS;
- exact action duplicates 0;
- NN Jaccard mean ≈ 0.4522.

R58C visible-action grounding repair:
- resolving Scene uses the obligation's supplied concrete `visible_action` when available;
- pre-resolution Scene uses the obligation's own statement/obstacle plus a stage-specific transaction primitive instead of a four-template paraphrase family;
- one obligation may develop across distinct transaction stages, but identical stage/function/action/state signatures remain forbidden;
- resolution still occurs exactly once.

R58C result on the same frozen diverse fixture:
- validation PASS;
- 12 sequences / 66 scenes;
- scene range 2..8;
- weaving fraction 0.917;
- 66/66 concrete actions unique;
- visible-action grounding 37/37 obligations;
- exact action duplicates 0;
- duplicate Scene-function signatures 0;
- due obligations resolved exactly once PASS;
- generic fallback ratio 0;
- NN concrete-action Jaccard mean **0.2162**;
- median **0.1429**;
- p90 **0.45**;
- max 0.5128.

The preregistered R58C gates (mean <=0.25, p90 <=0.50) PASS.

Mechanical-clone fixture remains BLOCKed after R58C.
Runtime Python compile: 45/45 PASS.
Only `adaptive_showrunner_ul16.py` changed relative to the R57-derived research working runtime; other runtime Python modules remained byte-identical in this repair.

## Interpretation
The session-level structure is materially improved versus R57: Scene depth is now within observed human broadcast ranges without reintroducing obligation cloning or quota padding, and distinct upstream material survives much more directly into distinct physical Scene actions.

However, R58C still does **not** establish that autonomous Candidate material invention has reached human-writer diversity. The remaining concrete-action similarity is higher than the human scene-function reference, and those two measures are only approximate comparators. A fresh physicalization and fresh blind/provider evaluation are still required.

## Research package
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R58C_SCENE_DIVERSITY_PASS_20260917.zip`

Size: 18,738,343 bytes.
SHA256:
`121aa57b8df9bcf0173aaa7420d9b7dadf59c87c7588e175c133b8f4df4b03a8`
ZIP CRC: PASS.
Persistent Library:
`/Literary_OS/Physical_Archive/RESEARCH_UL16_R58C_20260917/`

## Authority boundary
Physical authority remains SYNC-R57.
Production remains ENG:R47 / LEGACY_R53.
R58C is research evidence only until deliberately physicalized into a new audited SYNC successor.

## Next
Before Architecture Blind is restarted, decide whether to physicalize R58C into the next SYNC successor; because R58C changes Candidate planning behavior, any pre-R58C blind packet is historical only for current qualification.

## Status token
`UL16_R58C__SCENE_DEPTH_66__VISIBLE_ACTION_GROUNDING_37_OF_37__MECHANICAL_PATTERN_CLONES_BLOCKED__ACTION_NN_0_2162__R7_SMALL_SOURCE_LANE__RESEARCH_ONLY__PHYSICAL_R57_UNCHANGED`
