# Literary OS — R11 Codex Formal Experiment Execution, Evaluation & Return Protocol R2
Date: 2026-09-06

Status at handoff:
`P07_ACTIVE_PREFORMAL__R_F_LIVE_NOT_STARTED__R140_FORMAL_0_ATTEMPTS_0_OUTPUTS_0_SCORES`

Formal scored count before this work: **137**
Latest formal scored experiment: **R138**
Production engine: **ENG:R47 immutable**
Frozen research DB: **DB59**
DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

This document supplements the R11 Codex/API handoff and defines the full execution, evaluation, closure, and return contract.

## 1. Evidence strata
1. Concept Application(개념 적용)
2. Virtual/Local Engine Rehearsal(가상·로컬 엔진 예행)
3. Live Provider Engine Execution(실제 제공자 엔진 실행)
4. Formal Controlled Evaluation(정식 통제 평가)

R-FV local/Test-Double evidence is not live OpenAI evidence. R-F live evidence is not automatically Formal R140 evidence.

## 2. Immediate prerequisite — R-F Live Reference-vs-Actual Engine Craft Parity
Purpose: verify that the exact R11 candidate runs through the real OpenAI Provider path under identical provider/model/settings for Reference and Engine arms while preserving Source Cutoff, Structured Voice Profile, R-B/R-C bindings, R-D state handoff, R-E surface guards, R-EI bidirectional refinement, R-FV Provider-boundary integrity, and Checkpoint/Resume.

Credential Gate(인증정보 관문):
- inspect for a usable `OPENAI_API_KEY` without printing it;
- ask whether to reuse an existing usable key or create a new key;
- if creating, use the secure OpenAI Platform Codex key flow;
- never expose plaintext credentials in chat, logs, ZIPs, manifests, receipts, or return packages.

R-F execution:
1. verify the current R11 5-part / 9-package authority set and repaired C2 transport manifest;
2. reassemble C2 if split transport volumes are used;
3. fresh-extract C2 current overlay and reproduce regression;
4. mint a **NEW R11 CP1 Checkpoint** after verification;
5. never use superseded R10 CP1 Checkpoint/Ready Packet;
6. run CASE-01 paired Reference-vs-Engine live smoke;
7. current frozen intent: OpenAI Responses API, model `gpt-5.6-sol`, reasoning `low`, `store=false`;
8. if exact settings unavailable: HOLD, never silently substitute;
9. every accepted Provider-rendered result requires a real Provider Receipt;
10. CP1 failure blocks later R-F stages; preserve failures before amendment/repair.

Only after R-F closes may Codex continue to R-G and Formal R140.

### Current 5-Part / 9-Package authority baseline
Unless a later preregistered authority revision supersedes it, the delivery baseline is:
- CONTROL: 1 package
- PART-A: 1 package
- PART-B: B1 + B2 = 2 packages
- PART-C: C1 + C2-A + C2-B = 3 packages
- PART-D: D1 + D2 = 2 packages
- Total = **5 Parts / 9 Packages**

C2-A and C2-B are transport partitions of the current C2 authority. Reassembly must reproduce the exact C2 authority SHA256 recorded in the current Delivery Manifest(전달 원장). The split does not change scientific runtime semantics.

## 3. R-G and Formal R140 entry
After R-F closes:
1. R-G Freeze(최종 후보 동결)
2. freeze exact candidate runtime bytes/hashes
3. create/freeze the fresh deterministic formal sample required by the then-current protocol
4. produce Revised R140 Preregistration(수정 사전등록)
5. perform new G0 Physical Seal(물리 봉인)
6. only then begin Formal R140 generation

Historical six works were: 101번째프로포즈, 토마토, 좋은사람, 신의퀴즈1, 스위치, 파리의연인. Current R11 requires a fresh deterministic sample after R-G; do not assume the historical six remain final unless the revised sample procedure reproduces and re-seals them.

## 4. Formal R140 purpose
R140 is Production-scale Promotion Qualification(운영 규모 승격 자격 검증), not a single-module ablation.

Primary question:
> Is the fully integrated, frozen PRE-R140 Qualified Shadow Candidate sufficiently better than immutable ENG:R47 Production as an end-to-end system when each creates a new broadcast-scale episode from the same source-safe information?

PASS does not automatically promote the candidate to Production.

## 5. Hypothesis
> Treatment B, the frozen qualified candidate, will produce materially better full-episode dramatic craft than Control A, immutable ENG:R47, while not materially degrading causal/source fidelity, character voice, repetition/template resistance, temporal validity, or trace integrity.

## 6. Arms
Control A: **immutable ENG:R47 Production**.
Treatment B: **exact R-G-frozen candidate derived from R11 and preregistered R-F closure repairs**.

No runtime patch after Formal R140 Preregistration/G0. If a defect requires a runtime change after G0, stop, preserve the failed attempt, preregister/amend/re-freeze as required, and do not silently continue.

## 7. Source cutoff and data authority
Current frozen research reference: DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

Historical rule to preserve unless explicitly superseded before outputs:
- EP01–EP05 only;
- actual EP06 forbidden to Generator and Judge;
- actual EP06 is not an answer key;
- future-source leakage prohibited;
- quarantined malformed P06 R1 delta prohibited;
- DB64/other Living DB successors may not silently replace DB59.

Scientific question: given the same first-five-episode state, which engine creates the better new sixth broadcast episode?

## 8. Broadcast-scale output contract
Historical locked target:
- 9–12 Sequence(시퀀스)
- 50–60 Scene(씬)
- 35,000–45,000 characters(문자)
- Adaptive Sequence Expansion(적응형 시퀀스 확장)
- no universal fixed 5-scene default
- final Scene Realization must contain actual dramatic action/dialogue/response/subtext, not only synopsis bullets

Any revised contract must be frozen before formal outputs.

## 9. Formal execution order
1. verify DB/sample/control/treatment/preregistration hashes
2. verify no post-G0 code mutation
3. verify Source Cutoff
4. compile uniform runtime inputs from allowed layers only
5. run Control A
6. run Treatment B
7. preserve full request/response/trace/checkpoint chain
8. require real Provider Receipts where Provider rendering is used
9. validate broadcast-scale contract
10. validate End-to-End Trace and critical guards
11. freeze full-episode output hashes
12. anonymize arms W/X or equivalent
13. create sealed Coordinator Secret(조정자 비밀 대응표)
14. create independent Blind Judge(맹검 심사) packets
15. obtain three independent Judge returns
16. freeze all Judge results before revealing Blind Map
17. aggregate scores
18. evaluate G0–G9
19. issue PASS/FAIL/HOLD/INVALID verdict
20. create all final sealed artifacts
21. return the complete experiment package to ChatGPT for independent re-audit

No result-driven prompt/runtime/threshold tuning inside a formal attempt.

## 10. Blind evaluation
Independent Judges: **3**.

Judges must not see Engine Identity, Arm Mapping, another Judge result, actual EP06, post-cutoff source, or coordinator hints that reveal identity/results. Coordinator Secret may be opened only after score freeze. Judge admissibility must be machine-readable.

## 11. R140 100-point Craft Rubric
1. Causal/Continuity Fidelity(인과·연속성 충실도): 20
2. Episode Architecture(회차 구조): 15
3. Ensemble/Ecology(앙상블·인물 생태): 10
4. Dialogue/Scene Craft(대사·씬 작법): 15
5. Character Voice Differentiation(인물 목소리 차별화): 10
6. Subtext/Physicalization(서브텍스트·행동화): 10
7. Pacing/Line Economy(페이싱·문장 경제성): 10
8. Repetition/Template Resistance(반복·템플릿 저항): 5
9. Unsupported Invention/Future-source Discipline(근거 없는 발명·미래 원자료 통제): 5
Total = 100.

Masked Speaker Attribution(화자가림 식별)은 별도 보조 측정으로 보존한다.

## 12. Promotion Qualification Gates G0–G9
G0: before first generation physically seal Preregistration, DB SHA, Control/Treatment binary hash, Sample Manifest.

G1: Future-source / Entity / Critical Trace violation = 0.

G2: Treatment B broadcast-scale contract PASS on all formal works.

G3: Complete End-to-End Trace. If Provider-backed Rendering is used, every accepted final Provider Scene requires a real Provider Receipt.

G4: Overall Craft B-A median >= +5/100. Historical six-work design: B wins >= 4/6 works. If sample size changes, revised preregistration must define the locked corresponding criterion before outputs.

G5: Fidelity 25-point subtotal B-A median >= -1. No individual-work regression worse than -3.

G6: Character Voice median B-A >= 0. Historical six-work design: B >= A on >= 4/6.

G7: Repetition/Template median B-A >= 0. Critical duplicate/template violation = 0.

G8: At least 2 of 3 Judges prefer B over A on at least 4/6 works under the historical six-work design; revise mathematically before outputs if sample size changes.

G9: No work Overall B-A <= -10. Critical violation = 0.

Primary PASS = G0–G9 ALL PASS.
Permitted claim after PASS: `ELIGIBLE_FOR_SEPARATE_PRODUCTION_PROMOTION_DECISION`.
Automatic Production promotion is forbidden.

## 13. Formal result states
Use one explicit state: PASS, FAIL, HOLD, INVALID_PROTOCOL, INCOMPLETE_INFRASTRUCTURE, or CLOSED_NOT_SCORED.

Do not convert provider/infrastructure failure into literary Craft FAIL unless preregistered. Do not increment formal scored count while incomplete, invalid, or still under blind evaluation.

## 14. Mandatory result data
For every work × arm preserve at minimum: case id, source cutoff, source/binding hash, DB hash, engine/runtime hash, model/settings, request id/hash, response id/hash, Provider Receipt, retry/timeout history, checkpoint lineage, semantic plan hashes, episode/sequence/scene counts, character count, script hash, trace root, guard outcomes, future-source outcome, critical flags, blind label, Judge scores/rationale, aggregate score, B-A deltas, and G0–G9 verdicts. Required-null fields fail closed.

## 15. Mandatory artifacts
Authority/status:
- `00_RETURN_START_HERE.md`
- `01_FINAL_EXPERIMENT_STATUS.json`
- `02_AUTHORITY_AND_PACKAGE_HASHES.json`
- `03_EXECUTION_ENVIRONMENT_REDACTED.json`
- `04_PREREGISTRATION_AND_AMENDMENT_INDEX.json`
- `05_CHECKPOINT_RESUME_LEDGER.json`

Live Provider:
- `10_PROVIDER_REQUEST_MANIFEST.json`
- `11_PROVIDER_RECEIPTS.jsonl` or per-receipt JSON files
- `12_PROVIDER_FAILURE_RETRY_LEDGER.json`
- `13_TRUSTED_TRANSCRIPT_HASH_AUDIT.json`
Never include API keys, `.env` secrets, private keys, or plaintext credentials.

Formal generation:
- `20_SAMPLE_MANIFEST.json`
- `21_CONTROL_RUNTIME_FREEZE.json`
- `22_TREATMENT_RUNTIME_FREEZE.json`
- all Control/Treatment full-episode outputs
- semantic/episode/sequence/scene plan artifacts
- End-to-End trace and guard receipts

Blind evaluation:
- `30_BLIND_PACKET_MANIFEST.json`
- all W/X Judge packets
- `31_COORDINATOR_SECRET_SEALED.*`
- `JUDGE-01_RESULT.json`, `JUDGE-02_RESULT.json`, `JUDGE-03_RESULT.json`
- Judge admissibility records
- `32_BLIND_AGGREGATE_FROZEN.json`
- `33_BLIND_MAP_REVEAL_AND_DECODE.json` only after score freeze

Evaluation/closure:
- `40_R140_100_POINT_SCOREBOOK.json`
- `41_R140_G0_G9_GATE_VERDICT.json`
- `42_CRITICAL_VIOLATION_LEDGER.json`
- `43_INTEGRATED_RESULT_REPORT.md`
- `44_SCIENTIFIC_CLAIM_BOUNDARIES.md`
- `45_EXPERIMENT_REGISTRY_ENTRY.json`
- `46_DEVELOPMENT_TIMELINE.md`
- `47_ENGINE_EVOLUTION_MAP.md`
- `48_FRESH_EXTRACTION_VALIDATION.json`

Delivery/integrity:
- `90_FINAL_DELIVERY_MANIFEST.json`
- `91_FINAL_HANDOFF_AUDIT.json`
- Trust Root
- individual experiment sealed ZIP
- cumulative Research Master update if authority changed
- Narrative Engine Master update if authority changed
- Learning/Analysis handoff update if required
- current DB package only if authority changed; otherwise identify unchanged DB by hash
- updated 5-part / 9-package set if any official authority package changed

## 16. Failure preservation
If any failure occurs: stop affected gate; preserve exact failed request/output/log/receipt/checkpoint; classify engine/provider/infrastructure/protocol/judge-metrology/packaging-transport; do not overwrite; do not lower thresholds after seeing results; preregister any repair before code/config change; mint new hashes/checkpoint after repair; rerun only under amended protocol.

## 17. Exact return procedure from Codex to ChatGPT
When Codex finishes R-F, R-G, Formal R140, or stops at HOLD/FAIL:

Upload first:
1. `00_RETURN_START_HERE.md`
2. `90_FINAL_DELIVERY_MANIFEST.json`
3. `91_FINAL_HANDOFF_AUDIT.json`
4. Trust Root
5. individual experiment sealed ZIP

Then upload all changed 5-part/9-package authority packages, all formal output/judge/receipt packages, and any split Research/Engine/DB volumes required by the manifest.

If a package is unchanged, manifest must state `UNCHANGED_BYTE_IDENTICAL` with filename + SHA256.

For the current authority, PART-C return packaging is counted as **three packages: C1 / C2-A / C2-B**. If C2 is reassembled for internal execution, the return manifest must still preserve the 9-package delivery accounting and provide the reassembled C2 authority SHA256.

If split volumes are used, provide deterministic names, ordered index, per-volume SHA256, reconstructed SHA256, reconstruction instructions, and CRC results.

Accompanying safe metadata only: final status, R-F status, R140 status, formal scored count before/after, attempt count, output count, Provider Receipt count, Judge count, G0–G9 verdict, individual seal SHA256, Trust Root SHA256, changed authority packages, missing/held items. Never paste API keys or secret environment values.

## 18. ChatGPT independent re-audit after return
ChatGPT will independently verify Return Manifest/Trust Root, SHA256, package CRC/duplicates/unsafe paths, DB/Engine/Research reassembly, real Provider Receipts, preregistration-before-output timing, Blind admissibility and score-freeze-before-map-reveal, aggregate scores and G0–G9, formal-count increment validity, Experiment Registry, and Scientific Claim Boundaries. Codex self-reported PASS is not final independent closure by itself.

## 19. Prohibitions
Codex must not expose credentials, use actual EP06 as answer key, reveal arm identity before score freeze, show Judges another Judge result, silently swap frozen DB, silently replace provider/model/settings, use superseded R10 CP1 packets, patch Treatment after formal G0 without stopping/re-preregistering, promote local/Test-Double evidence to live evidence, increment formal count before valid completion, or auto-promote Production after R140 PASS.

## 20. Required end-state statement
Every return must contain:
`R_F_STATUS`
`R_G_STATUS`
`R140_STATUS`
`FORMAL_SCORED_COUNT_BEFORE`
`FORMAL_SCORED_COUNT_AFTER`
`R140_ATTEMPTS`
`R140_OUTPUTS`
`R140_JUDGE_RETURNS`
`PROVIDER_RECEIPT_COUNT`
`G0_G9_VERDICT`
`PRODUCTION_PROMOTION_STATUS`
`INDIVIDUAL_SEAL_SHA256`
`TRUST_ROOT_SHA256`
`MISSING_OR_HELD_ITEMS`

If R140 passes, the only allowed promotion-language at this stage is:
`ELIGIBLE_FOR_SEPARATE_PRODUCTION_PROMOTION_DECISION`
