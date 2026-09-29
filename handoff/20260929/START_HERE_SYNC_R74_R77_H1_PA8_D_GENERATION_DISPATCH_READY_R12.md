# START HERE — SYNC-R74 / R77-H1 PA8-D GENERATION DISPATCH READY — R12

Date: 2026-09-29
Status:
`PA8_A_PASS__PA8_B_PASS__PA8_C_R2_PASS__PA8_D_GENERATION_DISPATCH_READY__SURFACE_OUTPUTS_0__HUMAN_TARGET_UNOPENED`

R12 supersedes R11 for research/session recovery interpretation.
R12 does NOT change Physical Authority, Active Runtime, Production, Runtime DB, Operational Level-3, Formal count, or R140.

## 1. Current authority
- Physical Authority: **SYNC-R74**
- Active Runtime: exact R69
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Latest audited research DB candidate: DB64-R134 — semantic re-audit HOLD
- Operational Level-3: `SUSPENDED__REQUALIFICATION_REQUIRED`
- Formal scored total: 137
- Latest formal scored: R138
- Formal R140: NOT_STARTED

## 2. Why PA8 was started
PA7 improved the intended literary surface dimensions:
- Treatment whole preference: 3/3
- Treatment surface preference: 3/3
- Focus Gate: PASS 5/6
- Recoverability: PASS

PA7 nevertheless failed the frozen Absolute Gate because all judges identified a serious chronology/continuity defect inherited from the shared episode architecture.

Responsible ancestor:
`COMMON_EPISODE_ARCHITECTURE_TEMPORAL_SCHEDULING_AND_VALIDATION_LAYER`

The canonical PA7 failure pattern was a scene occurring around 00:38 while treating a delivery event constrained to approximately 23:55 as a future event.

## 3. Existing code boundary learned before PA8
Existing modules already covered adjacent but different layers:
- `literary_system/coherence/temporal_coherence.py`: episode-to-episode state/reveal/residue continuity
- `literary_system/nie/temporal_cim.py`: episode-indexed relationship evolution
- `literary_system/action_compiler/spatial_constraint_gate.py`: action-level co-location

The missing layer was:
within-episode absolute scene clock + event window/ETA + cross-scene entity/location/container movement continuity.

## 4. PA8-A — deterministic predicate
Preregistration:
`research/interventions/20260929/R77_H1_PA8_EPISODE_SPACETIME_CONTINUITY_PREREG_R1.md`

Frozen cases:
`research/interventions/20260929/pa8_spacetime_r1/PA8_FROZEN_16_CASES_R1.json`

Result:
`research/interventions/20260929/pa8_spacetime_r1/PA8_A_DETERMINISTIC_RESULT_R1.json`

Result:
- Positive violations: **8/8**
- Negative controls: **8/8**
- FP: **0**
- FN: **0**
- Deterministic rerun identity: PASS
- PA7-style future-event-in-past case: correctly detected

Status:
`PA8_A_PASS`

No active runtime mutation.

## 5. PA8-B — causal consumption
Preregistration:
`research/interventions/20260929/R77_H1_PA8_B_CAUSAL_INTEGRATION_PREREG_R1.md`

Frozen fixture:
`research/interventions/20260929/pa8_spacetime_r1/PA8_B_FROZEN_CAUSAL_FIXTURE_R1.json`

Result:
`research/interventions/20260929/pa8_spacetime_r1/PA8_B_CAUSAL_INTEGRATION_RESULT_R1.json`

PASS established:
- relevant earliest-start change -> provider-facing input hash changes -> downstream schedule changes;
- relevant travel-gap change -> provider-facing input + schedule change;
- invalid resource window -> REPLAN_REQUIRED;
- PA7-like future-event conflict -> REPLAN_REQUIRED;
- irrelevant metadata changes -> provider input and schedule remain byte-identical;
- semantic payload remains invariant;
- deterministic rerun PASS.

Status:
`PA8_B_PASS`

No active runtime mutation.

## 6. PA8-C — fresh architecture
Preregistration:
`research/interventions/20260929/R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_PREREG_R1.md`

Fresh synthetic episode:
**새벽 보존실**

R1:
- 9 sequences
- 50 scenes
- 01:48-03:32 episode clock
- Surface outputs: 0
- Preflight result: FAIL
- Exact failure: **35 UNTYPED_ZERO_GAP_LOCATION_JUMP**
- R1 preserved as immutable failure evidence.

R2 repair preregistration:
`research/interventions/20260929/R77_H1_PA8_C_R2_TRANSITION_TYPING_REPAIR_PREREG_R1.md`

R2 allowed only movement typing.
No premise, due/deferred, sequence, scene function, must-change, scene time, duration, location, resource window, blind sample, or arm policy change was allowed.

R2 result:
- transition count: 66
- AT_SCENE_OPEN: 35
- BETWEEN_SCENES: 31
- unrepairable transitions: 0
- preflight issues: 0
- 50 scenes / 9 sequences
- semantic projection invariant:
  `a449ed98f5845003cd1d496dc6e9f65a1bae651f46a24ef75e7b9148cfaa85b1`
- R2 architecture SHA256:
  `2486c4534482943d82fb91723d931a611551d8c3b2cf4ba36907852d325c9bbf`

Canonical R2:
`research/interventions/20260929/pa8_spacetime_r1/R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R2.json`

Status:
`PA8_C_R2_PASS`

## 7. PA8-D — paired surface generation protocol
Preregistration:
`research/interventions/20260929/R77_H1_PA8_D_PAIRED_SURFACE_GENERATION_PREREG_R1.md`

Both future arms:
- same semantic payload
- same PA7 residual surface policy
- >=40,000 characters
- no upper cap
- no quota padding
- same 9 sequences / 50 scene semantic functions
- Human target absent
- H1 real-work Past-Only payload absent.

Only difference:
- CONTROL: ESCC omitted
- TREATMENT: ESCC present and fail-closed.

Semantic payload SHA256 in both packets:
`adefb2f6463939cc2e23c5c08deee82c912932721753a3e1047ed9533cadac34`

Control packet SHA256:
`28fe250e505b6a3751435afd1ae384340ff1cac1f6e17d857ea007912fd274f7`

Treatment packet SHA256:
`fb17e6859c00bcbd1101d5f82a58e6bee88f01caa5bdd62b1ebc203a41d363ae`

## 8. Independent generation ZIPs
The two arm inputs are sealed as separate ZIPs.

CONTROL:
`research/interventions/20260929/pa8_spacetime_r1/PA8_D_CONTROL_INDEPENDENT_GENERATION_PACKAGE_R1.zip`
- 8,213 bytes
- SHA256:
  `67d3c4f76cfd29c5bc86dd417b024cc70b84fd76d02afde1dc1697d2230da323`
- CRC PASS

TREATMENT:
`research/interventions/20260929/pa8_spacetime_r1/PA8_D_TREATMENT_INDEPENDENT_GENERATION_PACKAGE_R1.zip`
- 11,288 bytes
- SHA256:
  `989cf32123780bc5ead50fe924e959bef0de964a7d7ee00aa272642c42d2b4ef`
- CRC PASS

Canonical ZIP manifest:
`research/interventions/20260929/pa8_spacetime_r1/PA8_D_GENERATION_ZIP_MANIFEST_R1.json`

ZIP commit:
`3f60554ac8da3dca718ca0fef687828476d0bf08`

## 9. Packaging incident — CLOSED
Initial ZIP workflow run:
`36574536664`
failed after the ZIP builder had already produced PASS/CRC-PASS outputs.

Root cause:
repository `.gitignore` excludes ZIP files; ordinary `git add` returned exit code 1.

Repair:
force-add only the two declared ZIP output paths.

Workflow repair commit:
`c302a6fdbb11233b571475241304a400cd489072`

Retry run:
`36576289701` -> SUCCESS

Incident closure:
`research/operations/20260929/PA8_D_GENERATION_ZIP_GITIGNORE_INCIDENT_CLOSURE_R1.json`

Scientific effect:
**NONE**

## 10. Frozen external evaluation sample
Before any PA8 surface output the sample is already frozen:
- SC05
- SC13
- SC21
- SC30
- SC39
- SC47

Do not replace this sample after first surface output.

## 11. Exact next transaction
Do NOT generate both arms in the coordinator context.

1. Give CONTROL ZIP to one fresh independent generation context.
2. Seal its first complete screenplay output.
3. Give TREATMENT ZIP to a different fresh independent generation context.
4. Seal its first complete screenplay output.
5. Do not let either generator see the other packet/output.
6. Run frozen mechanical validation.
7. Any underlength repair requires a new arm-local preregistration before editing.
8. Only after both arms mechanically qualify, build blind J01/J02/J03 packets.
9. Seal 3/3 first schema-valid raw judgments before revealing mapping.
10. Apply unchanged PA7 literary gates plus the separate PA8 continuity gate.
11. Only after PA8 full closure decide whether to implement the PA8 layer into the actual candidate runtime.

## 12. Why the coordinator must stop here
Current PA8-D surface outputs:
- Control: 0
- Treatment: 0

Current external judge outputs:
0

The coordinator has seen both arm specifications. Generating both scripts here would violate the preregistered independent-context rule and contaminate the causal comparison.

Therefore current valid status is:
`GENERATION_DISPATCH_READY__OUTPUTS_0`

It is NOT valid to call PA8 fully PASS/FAIL yet.

## 13. Physical-package boundary
No actual candidate-runtime source byte has changed.
No C1/C2 binding has changed.
No Production or DB59 byte has changed.

Therefore:
- Physical Authority remains **SYNC-R74**.
- No new 5-Part / 9-Package successor is authorized at this checkpoint.

Mandatory future rule:
`RESEARCH_FINDING -> IMPLEMENTED_IN_CANDIDATE -> REGRESSION_PASS -> C1/C2_BINDING_PASS -> 9_PACKAGE_RESEAL -> SHA/CRC/CUSTODY_PASS -> NEW_PHYSICAL_AUTHORITY`

If PA8 later changes actual candidate-runtime/package bytes and those gates pass, a fresh successor 5-Part / 9-Package set must be created and delivered to the developer.

## 14. Current checkpoint
Canonical:
`research/interventions/20260929/R77_H1_PA8_CURRENT_CHECKPOINT_R1.json`

Status token:
`SYNC_R74_CURRENT__PA8_A_PASS__PA8_B_PASS__PA8_C_R2_PASS__PA8_D_GENERATION_DISPATCH_READY__CONTROL_OUTPUTS_0__TREATMENT_OUTPUTS_0__JUDGE_OUTPUTS_0__H1_PRIMARY_0__HUMAN_TARGET_UNOPENED__NO_RUNTIME_OR_PHYSICAL_CHANGE`
