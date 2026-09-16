# UL-16 Candidate Main-Path Integration Receipt R1

Date: 2026-09-16
Status: `MAIN_PATH_RESEARCH_INTEGRATION_PASS__LEGACY_PATH_INVARIANT__PHYSICAL_AUTHORITY_UNCHANGED`
Parents:
- UL-14 Human-Authored Hierarchical Census / Gap Audit
- UL-15 Adaptive Multi-Obligation Planner Preregistration
- UL-15 Prototype / Canonical Compatibility Receipt
- UL-16 Main-Path Integration Plan

## 1. Scope

This receipt records integration of the Adaptive Multi-Obligation planning path into an isolated research working copy of the actual R53 runtime source. It does **not** modify the sealed SYNC-R53 transport packages and does not promote Candidate or Production authority.

Base runtime source ZIP SHA256:
`b3873e98d8f5df44aee22c388ac9b19bf61cbdafd5f9c09cda7f06952125da55`

Research runtime package:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R1_20260916.zip`

Research package SHA256:
`c1dfda09c97771f56aa88adc402c8fe05a03c0fd2b93205b83dafdc8d2101441`

Persistent Library locator:
`/Literary_OS/Physical_Archive/RESEARCH_UL16_20260916/LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R1_20260916.zip`

Library presence/listing verified. Independent raw Library re-materialization/re-hash is not claimed.

## 2. Actual integration point

Direct package inspection established that the Candidate upper overlay itself contains validation/gating research modules, while the executable Episode/Sequence/Scene planning spine is in the common runtime source.

Therefore UL-16 integration correctly targets the runtime authoring router while preserving the legacy path.

Changed research files:
- `literary_os_runtime/canonical_authoring.py`
- `literary_os_runtime/adaptive_showrunner_ul16.py` (new)

All other Python modules in the working runtime package remain unmodified for this integration receipt.

## 3. Candidate routing

Legacy path remains available as `LEGACY_R53`.

New research Candidate mode:
`ADAPTIVE_UL16`

Candidate chain:
`current/cutoff-safe narrative state -> active typed obligation portfolio -> due/defer scheduler -> adaptive sequence graph -> adaptive scene graph -> reverse reconstruction gate -> canonical adapter -> Canonical Typed IR V2`

Unknown authoring modes fail closed.

## 4. DB64 use boundary

DB64 is consumed as a **distributional/metrology prior only**, never as hidden-target semantic donor.

DB64 R108 research-support SHA256:
`19f3c446a73408045d02d4d99e168251dca42da3bfa00abaff1d8f9159d7ea46`

Frozen UL-16 prior profile hash:
`a89dd2f9dd29635f294432703f2f908e2567ddc7c59acb4a90d910fa62689b22`

Future/post-cutoff source injection is fail-closed by the canonical compile boundary.

## 5. Same-input Legacy vs Adaptive integration test

Legacy R53 path:
- status: PASS
- sequences: 9
- scenes: 20
- per-sequence scene counts: `2,2,2,3,2,2,2,3,2`
- Canonical nodes: 31
- Canonical validation errors: 0

Adaptive UL-16 path on the same base fixture plus explicit rich obligations:
- status: PASS
- sequences: 9
- scenes: 59
- per-sequence scene counts: `10,5,5,5,8,5,8,8,5`
- scene range: 5..10
- weaving fraction: 0.889
- distinct owner count: 9
- deferred count: 2
- missing due obligations from sequences: 0
- missing due obligations from scenes: 0
- lost deferred obligations: 0
- false fulfilled deferred obligations: 0
- Canonical nodes: 70
- Canonical validation errors: 0

This is a structural integration test, not a literary-quality claim.

## 6. Dynamic architecture test

A richer ensemble fixture with 30 active obligations was used to test whether `9 sequences` had accidentally become another fixed quota.

Result:
- sequences expanded to 11;
- scenes expanded to 97;
- per-sequence scene counts varied 5..11.

Therefore the current research implementation uses 9 only as a broadcast-depth floor in the relevant profile, not as a hard upper bound or exact template.

## 7. Current-state automatic compiler test

The Candidate mode was tested without a manually supplied final Episode/Sequence/Scene plan. The adapter compiled an active obligation portfolio from current cutoff-safe state inputs and successfully produced an adaptive graph.

Decision: PASS.

This demonstrates Main-Path consumption rather than only a standalone manually authored prototype.

## 8. Fail-closed defect found and repaired

During regression, deliberate future-source leakage was correctly detected by Canonical IR, but the authoring router originally allowed the compiler `ValueError` to escape as an exception instead of converting it into a stable HOLD/FAIL-CLOSED result.

Repair:
- canonical compile exceptions at this boundary are now converted to `CANONICAL_IR_COMPILE_FAIL` fail-closed status for Candidate research execution.

Retest: PASS.

## 9. Regression suite

`UL16_REGRESSION_RESULT_R1.json` SHA256:
`791512d2768528694e5691df836b82aaa6c278c1c23be6497733144a72b40897`

All boolean gates PASS:
- Legacy path works;
- explicit adaptive path works;
- broadcast depth gate;
- due/defer integrity;
- current-state derived obligation compiler;
- dynamic sequence count not fixed at 9;
- future-source leakage fail-closed;
- unknown mode fail-closed.

Runtime Python compilation: 45/45 modules PASS.

## 10. Legacy invariance

A before/after probe of the normal Legacy path produced the exact same graph hash:
`f27df4468b4d2a8de1dfe50fdd6508a63dddd3d9dbb67d31eeb4428e39f9af6b`

Before:
- sequences 9
- scenes 20

After UL-16 research integration:
- sequences 9
- scenes 20

Decision: `LEGACY_NORMAL_PATH_INVARIANT = PASS`.

Therefore the research integration is isolated behind Candidate mode and does not alter the Production/Legacy algorithm in this working package.

## 11. Runtime resource observation

Earlier large DB/package work in this cgroup reached:
- `memory.max = 4 GiB`;
- `memory.peak = 4 GiB`;
- historical `memory.events max = 117`;
- OOM/OOM-kill = 0.

During the final UL-16 lightweight integration/checkpoint phase, `memory.events max` remained 117 (delta 0). No new memory-pressure event occurred.

Execution henceforth follows R4 Atomic Execution Protocol; large corpus work and Main-Path engineering are separated into independent transactions.

## 12. What is resolved

At research-integration level:
- fixed 2/3-scene Candidate lowering removed;
- single-owner/single-kind requirement removed;
- rich current-state obligations can causally feed the Candidate authoring path;
- due/defer preservation implemented;
- sequence/scene depth is adaptive;
- DB64 priors are explicitly hash-bound and non-semantic;
- future leakage and unknown modes fail closed;
- Legacy path is invariant;
- Canonical Typed IR compatibility remains intact.

## 13. What is NOT yet resolved / qualified

Still required before any Candidate promotion:
- diverse multi-work cutoff-safe historical replay;
- architecture-only independent blind evaluation;
- scene-plan semantic quality audit beyond structural coverage;
- state commit/carry + reverse replanning integration regression;
- real fresh-context OpenAI Provider generation with receipts;
- full >=35k broadcast screenplay evaluation;
- clean physical successor build;
- complete 12-step physical custody gate.

## 14. Authority impact

None.

Unchanged:
- Physical baseline: SYNC-R53;
- Production Engine: ENG:R47;
- Candidate Base authority: P07-I4H Recovery R3;
- DB runtime authority: DB59 frozen;
- DB64: research-support candidate only;
- Formal total: 137; latest R138; R140 0/0/0.

## STATUS TOKEN

`UL16__ACTUAL_MAIN_PATH_RESEARCH_INTEGRATION_PASS__CURRENT_STATE_OBLIGATION_COMPILER_PASS__ADAPTIVE_SEQUENCE_SCENE_GRAPH_PASS__LEGACY_INVARIANT__FUTURE_LEAK_FAIL_CLOSED__CANONICAL_IR_PASS__LIVE_PROVIDER_AND_PHYSICAL_PROMOTION_PENDING`
