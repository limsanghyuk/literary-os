# P07 RFV3 — A/B/C/D Causal Re-pretest Preregistration R1
Date: 2026-09-06
Classification: NONFORMAL_PREFORMAL_VIRTUAL_LOCAL_CAUSAL_REPRETEST
Formal scored count before: 137
R140 before: 0 attempts / 0 outputs / 0 scores
Production: ENG:R47 immutable
Frozen DB authority: DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## Purpose
Resolve the current ambiguity between direct natural-language concept prompting, the pre-repair runtime, repaired DB59 retrieval, and the full candidate with bidirectional refinement.

## Research questions
RQ1. Does SUMMARY-only direct natural-language context outperform the pre-repair engine because the runtime loses literary information?
RQ2. Does repaired DB59 `USE_RETRIEVAL` add measurable craft value over the same engine with `NO_RETRIEVAL`?
RQ3. Does the full current candidate with Bidirectional Refinement improve further over repaired retrieval alone?
RQ4. Are any improvements due to changed surface settings, source leakage, or unequal inference budget rather than the intended treatment?

## Frozen arms
A — SUMMARY ONLY: same EP01–EP05 source-safe summary/context, no Literary OS runtime plan, no DB59 retrieval.
B — PRE-REPAIR ENGINE / NO_RETRIEVAL: historical pre-repair candidate behavior, same source cutoff, retrieval payload forced/observed as `NO_RETRIEVAL`, no repaired DB propagation.
C — RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL: same candidate family with repaired verified DB59 retrieval; selected DB59 donors must reach semantic provider input and receipts.
D — FULL CURRENT CANDIDATE + BIDIRECTIONAL REFINEMENT: Arm C plus current hierarchy/backprop-style responsible-ancestor refinement and re-lowering; no extra source information.

## Common controls
- Same work and same EP01–EP05 source cutoff for all arms.
- Actual EP06 forbidden to generator and evaluator.
- Same target episode: fresh synthetic EP06.
- Same surface realization contract and settings across A/B/C/D.
- Same model family/virtual model configuration when the local harness supports model identity; no arm-specific fallback.
- Same requested scene sample and output length contract per arm.
- No result-informed prompt, threshold, donor, or rubric tuning.
- Python literary prose generation = 0.

## Primary development case
CASE-01 `101번째프로포즈`, EP01–EP05 only, because it has historical CT-17 pre-repair live evidence and existing R-F fixtures. This is a development/repretest case, not the future Formal R140 sample.

## Generation contract
Phase V1: paired virtual/local semantic run for all four arms, preserving exact prompts/input hashes, retrieval decisions, donor ids/hashes, hierarchy receipts, and final semantic plans.
Phase V2: same-size surface realization sample for all four arms. Default development sample = deterministic first/middle/last scenes from a common scene-count contract. If full-episode virtual rendering is available without Python prose, additionally generate the same broadcast-scale target for all arms; do not mix full-episode scores with 3-scene scores.

## Required causal checks before craft scoring
1. A has no runtime retrieval payload.
2. B is `NO_RETRIEVAL` and contains no DB59 donor semantic content.
3. C is `USE_RETRIEVAL`; selected DB59 donor mutation changes semantic provider input; irrelevant unselected donor mutation does not.
4. D contains all C evidence plus at least one traceable Bidirectional Refinement decision or explicitly reports `NO_REFINEMENT_TRIGGERED`; D may not fabricate a refinement event.
5. Source cutoff violation = 0.
6. Same surface settings and comparable generation budget across arms.
7. Required-null receipt fields fail closed.

## Craft evaluation axes
- Causal/Continuity Fidelity
- Episode Architecture
- Ensemble/Ecology
- Dialogue/Scene Craft
- Character Voice Differentiation
- Subtext/Physicalization
- Pacing/Line Economy
- Repetition/Template Resistance
- Unsupported Invention/Future-source Discipline

Use a blinded A/B/C/D shuffle for craft judging. Evaluation must not use actual EP06 as answer key.

## Interpretation gates
- If B < A while C > B, evidence supports runtime information-loss plus DB retrieval recovery, not merely 'engine bad'.
- If C <= B, repaired retrieval has no demonstrated incremental craft value on this case even if `USE_RETRIEVAL` mechanically works.
- If D > C with fidelity non-regression and a real refinement trace, evidence supports incremental value of bidirectional refinement.
- If D == C because no refinement trigger fires, claim only 'no triggered treatment on this case'.
- A single-case result is diagnostic/nonformal and cannot support production promotion.

## Previous evidence boundary
CT-17 is preserved as PRE-REPAIR LIVE BASELINE evidence only. It is not CP1 and not Formal R140. Previous RFV Provider-boundary evidence remains valid, while previous DB-adoption-completeness claims are withdrawn.

## Mandatory task-close packaging rule
After each completed RFV3 task unit, create an atomic checkpoint and propagate the changed authority state into the canonical `5-PART / 9-PACKAGE` delivery structure:
CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2.
If the local artifact backend is unavailable, do not fabricate package closure: seal the exact external checkpoint, mark `9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE`, and resume packaging before beginning the next scientific task whenever the backend becomes healthy.

## Hard stops
- Any actual EP06/post-cutoff leakage.
- Arm-specific source or surface-setting asymmetry.
- B accidentally using repaired retrieval.
- C/D failing to prove DB59 donor propagation.
- D claiming refinement without trace.
- Result-informed threshold/prompt tuning.
- Formal count increment.

## Required final status
`RFV3_ABCD_CAUSAL_REPRETEST_{PASS|FAIL|HOLD|INVALID}` with explicit mechanical and craft sub-verdicts.
