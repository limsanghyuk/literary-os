# Literary OS Evolution Architecture R1

Date: 2026-09-12
Classification: RESEARCH_AND_ENGINEERING_DESIGN__NO_PROMOTION
Parent physical authority: SYNC-R24 (`8b42c029f14f344ce7fbfc9407ab3cce1f9692f16ba8659c6045a327e3a8d043`)
Current frozen experiment: EXP-I4K5R4A-A2, mechanical prescore PASS, G5B PASS, exact arms frozen, mask/judges/mapping 0.

## 1. Purpose
Evolve Literary OS from a system that can create and preserve strong narrative architecture into a system that can also prove that the architecture is actually consumed, survives whole-episode scaling, renders as actor-playable/camera-legible broadcast surface, and passes both absolute and comparative quality gates before promotion.

## 2. Evidence synthesized
The design incorporates: (a) I4A-I4K research lineage, including repeated local-vs-whole-episode degradation; (b) I4K-4 same-agent masked PASS followed by I4K-5 independent surface FAIL; (c) I4K-5R2 valid internal FAIL localizing the remaining bottleneck to Plan→Surface realization; (d) I4K-5R3 PSSB internal PASS; (e) R4A Actor-Visible Expression Hygiene and hard debug gates; and (f) Claude's independently identified common-mode scorer blind spot, contract-consumption risk, whole-episode degradation hypothesis, power/N policy, and revision-axis ambiguity.

## 3. Core architectural change: seven-layer evidence pipeline
The next Literary OS must separate seven layers that were previously partially conflated.

### L0 Semantic Architecture
Series/Episode → Event Ecology → Sequence → Scene → Future Adoption.
Hard rule: decision owners, future owners, second-order obligations and future-adoption targets are sealed before surface generation.

### L1 Contract / Capability Consumption
Every required contract or capability must produce a machine-readable invocation receipt. Existence of code or a repaired artifact is not evidence of use.
Required receipt fields: contract_id, required=true/false, source_sha256, consumer_path, invocation_count, first_invocation_stage, last_invocation_stage, output_binding_sha256, zero_invocation_reason.
Hard rule: any preregistered required contract with invocation_count=0 blocks admission.

### L2 Surface Realization
Renderer consumes semantic facts rather than serialized plan-purpose prose.
Shared baseline: Actor-Visible Expression Hygiene.
Treatment-level experimental interventions such as PSSB remain separate and frozen per experiment.
The renderer must prefer playable action, facial change, gaze, breath, hand/object handling, blocking, timing, interruption, silence, failed action, bodily effort and spatial change over explanatory emotion labels or architecture prose.

### L3 Absolute Surface Hygiene
Deterministic gates independent of Control-vs-Treatment deltas.
Candidate metrics: scene-entry explanatory preface ratio, scene-entry preface chars, repeated sequence-purpose serialization, internal-plan token leakage, exact/mechanical repetition, procedural-abstraction density, screenplay-body scale.
Thresholds MUST NOT be invented from model outputs. They must be derived prospectively from a frozen human-broadcast-script reference distribution.

### L4 Relative Causal Effect
Paired Control/Treatment evaluation estimates the intervention effect while L0-L3 are already valid.
Relative deltas cannot substitute for L3 because common-mode defects cancel in deltas.

### L5 Independent Evaluation
Fresh independent judges/providers with mapping hidden until all judge packets are sealed. Same-agent masked results are DEVELOPMENT_PREFORMAL evidence only.

### L6 Human / Formal Promotion
Fresh-human validation, formal experiment and production promotion remain separate gates. No internal or independent-LLM PASS alone promotes Production.

## 4. Whole-episode scale doctrine
Whole-episode degradation is promoted to a first-class research problem.
Three hypotheses remain explicitly unproven until measured: H-W1 cumulative contamination, H-W2 repeated plan-purpose amplification, H-W3 continuity debt concentrated later in the episode.
Retrospective diagnosis must use already sealed I4C/I4E/I4K-5 material first; no new generation is needed for the diagnostic.
Only after the diagnostic may a new prospective intervention be designed.

## 5. Evaluation redesign
Every scored experiment must produce two independent evidence classes:
1. ABSOLUTE_ADMISSION: deterministic integrity/quality hygiene that can fail both arms.
2. RELATIVE_EFFECT: paired or blind comparative evaluation.
A PASS requires both classes where preregistered. A zero Treatment-Control delta is not evidence that absolute quality is acceptable.

## 6. Statistical doctrine
Future multi-work experiments must preregister target effect size, sample-size policy, confidence interval method, aggregation unit, stopping rule and missing/invalid-run handling.
Near-threshold runs remain immutable FAIL under their original threshold; they become inputs to power analysis, not reasons to lower the threshold or perform targeted post-hoc repair.

## 7. Runtime / load integrity doctrine
Do not infer active consumption from package presence. Add ACTUAL_LOAD_RECEIPT and CONTRACT_CONSUMPTION_RECEIPT.
For the currently observed `engine_self_description.py` split, original carrier hash and repaired-overlay hash must be traced through an execution-path audit before any pointer reassignment or promotion. Historical sealed carriers must not be silently rewritten.

## 8. Governance and naming
Do not rename historical sealed artifacts. Starting with new records, every revision token must carry an axis prefix: SYNC-, FORMAL-, ENGREC-, EXP-, AUTH-, DB-, PKG-.
Pointers and manifests must expose `revision_axis` and `canonical_alias` so a bare `R24` is never sufficient navigation.

## 9. Current R4A protection rule
EXP-I4K5R4A-A2 is frozen. No prose mutation, threshold change, new renderer feature, judge-count change or new PASS/FAIL gate may be added after output.
Before masking, only two actions are legal:
- execute the already-preregistered but not yet explicitly enforced `treatment_repeated_plan_purpose_copy=0` compliance audit;
- compute Claude-derived common-mode metrics as KNOWLEDGE_ONLY diagnostics with no effect on R4A PASS/FAIL.
If the preregistered repeated-plan-purpose gate fails, R4A becomes PRESCORE_HOLD/INVALID for scoring; the frozen prose may not be repaired because Attempt2 is the final provisional attempt.
If it passes, proceed to G6 mask and the preregistered three independent judges.

## 10. Evolution program
Phase E0: close R4A compliance/audit gap without mutating frozen surfaces.
Phase E1: retrospective Whole-Episode Degradation Diagnostic on sealed historical works.
Phase E2: Human Broadcast Surface Reference Distribution and absolute-gate calibration.
Phase E3: Contract/Load Consumption instrumentation and execution-path receipts.
Phase E4: fresh prospective renderer experiment using L0-L5 pipeline.
Phase E5: multi-work statistical replication with preregistered N/power/CI.
Phase E6: fresh-human gate, then Formal qualification; only then consider Active Engine/Production promotion.

## 11. Package propagation
Until engine/runtime bytes change, research/governance propagation should normally modify CONTROL/A/B2 only; B1/C1/C2/D remain byte-identical if their payloads are unchanged.
If a validated Contract Consumption implementation changes runtime/candidate engine bytes, C1/C2 become candidate-change transports and must undergo full regression, reassembly, package reseal and separate promotion review. Production ENG:R47 remains immutable until an explicit promotion gate passes.

Status: DESIGN_SEALED__R4A_FROZEN__PREFLIGHT_COMPLIANCE_NEXT__NO_AUTHORITY_PROMOTION
