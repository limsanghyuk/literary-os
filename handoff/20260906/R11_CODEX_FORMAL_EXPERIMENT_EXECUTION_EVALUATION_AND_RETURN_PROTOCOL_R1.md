# Literary OS — R11 Codex Formal Experiment Execution, Evaluation & Return Protocol R1

Date: 2026-09-06

Status at handoff: `P07_ACTIVE_PREFORMAL__R_F_LIVE_NOT_STARTED__R140_FORMAL_0_ATTEMPTS_0_OUTPUTS_0_SCORES`

Formal scored count before this work: **137**  
Latest formal scored experiment: **R138**  
Production engine: **ENG:R47 immutable**  
Frozen research DB: **DB59**  
DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

This document supplements the R11 Codex/API handoff. It is the execution/evaluation/return contract for Codex.

---

## 1. Evidence strata

Do not collapse these evidence classes:
1. Concept Application(개념 적용)
2. Virtual/Local Engine Rehearsal(가상·로컬 엔진 예행)
3. Live Provider Engine Execution(실제 제공자 엔진 실행)
4. Formal Controlled Evaluation(정식 통제 평가)

R-FV local/Test-Double evidence is not live OpenAI evidence. R-F live evidence is not automatically Formal R140 evidence.

---

## 2. Immediate prerequisite — R-F Live Reference-vs-Actual Engine Craft Parity

### Purpose
Verify that the exact R11 candidate can run through the real OpenAI Provider path under the same provider/model/settings as the Reference arm while preserving Source Cutoff, Structured Voice Profile, R-B/R-C bindings, R-D long-horizon state, R-E surface guards, R-EI bidirectional refinement, R-FV Provider-boundary integrity, and Checkpoint/Resume.

### Credential gate
Before any live API run, Codex must:
1. check for a usable `OPENAI_API_KEY` without printing it;
2. ask whether to reuse an existing usable key or create a new one;
3. if creating, use the secure OpenAI Platform Codex key flow;
4. never expose plaintext credentials.

### R-F execution rule
- Verify all R11 packages.
- Fresh-extract C2 R38.
- Reproduce current regression.
- Mint a **new R11 CP1 Checkpoint**.
- Do not use the superseded R10 CP1 packet.
- Run CASE-01 paired Reference-vs-Engine live smoke.
- Current frozen R-F intent: `gpt-5.6-sol`, reasoning `low`, `store=false`.
- If exact settings are unavailable: HOLD; do not silently substitute.
- Every accepted Provider-rendered output requires a real Provider Receipt.
- Provider/transport failure is not automatically Craft FAIL.
- CP1 failure blocks later R-F stages.
- Preserve every failure before amendment/repair.

Only after R-F closes may Codex continue toward Formal R140.

---

## 3. R-G and Formal R140 entry

After R-F closes:
1. R-G Freeze(최종 후보 동결)
2. freeze exact candidate runtime bytes/hashes
3. create/freeze the fresh deterministic formal sample required by the then-current protocol
4. produce Revised R140 Preregistration
5. perform new G0 Physical Seal
6. only then begin Formal R140 generation

Historical R140 logic used six works: 101번째프로포즈 / 토마토 / 좋은사람 / 신의퀴즈1 / 스위치 / 파리의연인.

Current R11 authority requires a fresh deterministic formal sample after R-G. Do not assume the historical six are final unless the revised deterministic procedure reproduces and re-seals them.

---

## 4. Formal R140 scientific purpose

R140 is not a single-module ablation. It is a Production-scale Promotion Qualification(운영 규모 승격 자격 검증).

Primary scientific question:

> Is the fully integrated, frozen PRE-R140 Qualified Shadow Candidate sufficiently better than immutable ENG:R47 Production as an end-to-end system when each must create a new broadcast-scale episode from the same source-safe information?

A R140 PASS does not automatically promote the candidate to Production.

---

## 5. Formal R140 hypothesis

> Treatment B, the frozen qualified candidate, will produce materially better full-episode dramatic craft than Control A, immutable ENG:R47, while not materially degrading causal/source fidelity, character voice, repetition/template resistance, temporal validity, or trace integrity.

---

## 6. Formal R140 arms

Control A: **immutable ENG:R47 Production**.

Treatment B: **the exact R-G-frozen candidate derived from R11 and any preregistered R-F closure repairs**.

No runtime patch after Formal R140 preregistration/G0. If a defect requires a runtime change after G0, stop, preserve the attempt, amend/re-freeze, and do not silently continue.

---

## 7. Primary data and source cutoff

Current frozen research reference DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

Historical rule to preserve unless explicitly superseded before outputs:
- EP01–EP05 only
- actual EP06 forbidden to Generator and Judge
- actual EP06 is not an answer key
- future-source leakage prohibited
- quarantined malformed P06 R1 delta prohibited
- DB64/other Living DB successors may not silently replace DB59

Scientific question: Given the same first-five-episode state, which engine creates the better new sixth broadcast episode?

---

## 8. Broadcast-scale output contract

Historical locked target:
- 9–12 Sequence
- 50–60 Scene
- 35,000–45,000 characters
- Adaptive Sequence Expansion
- no universal fixed 5-scene default
- final Scene Realization must contain actual dramatic action/dialogue/response/subtext

Any revised contract must be frozen before formal outputs.

---

## 9. Formal execution order

1. verify frozen DB/sample/control/treatment/preregistration hashes
2. verify no post-G0 code mutation
3. verify Source Cutoff
4. compile uniform runtime inputs using only allowed layers
5. run Control A
6. run Treatment B
7. preserve full request/response/trace/checkpoint chain
8. require real Provider Receipts where Provider rendering is used
9. validate broadcast-scale contract
10. validate End-to-End Trace
11. validate critical guards
12. freeze final full-episode output hashes
13. anonymize arms to W/X or equivalent
14. create sealed Coordinator Secret
15. create independent Blind Judge packets
16. obtain three independent Judge returns
17. freeze all Judge results before revealing the Blind Map
18. aggregate scores
19. evaluate G0–G9
20. issue PASS / FAIL / HOLD / INVALID verdict
21. create all final sealed artifacts
22. return the full experiment package to ChatGPT for independent audit

No result-driven prompt/runtime/threshold tuning is allowed inside the formal attempt.

---

## 10. Blind evaluation

Independent Judges: **3**.

Judges must not see Engine Identity, Arm Mapping, another Judge result, actual EP06, post-cutoff source, or coordinator hints that reveal results/identity.

Coordinator Secret is revealed only after score freeze. Judge admissibility must be machine-readable.

---

## 11. R140 100-point Craft Rubric

- Causal/Continuity Fidelity: **20**
- Episode Architecture: **15**
- Ensemble/Ecology: **10**
- Dialogue/Scene Craft: **15**
- Character Voice Differentiation: **10**
- Subtext/Physicalization: **10**
- Pacing/Line Economy: **10**
- Repetition/Template Resistance: **5**
- Unsupported Invention/Future-source Discipline: **5**

Total = **100**.

Masked Speaker Attribution is separate supporting metrology.

---

## 12. R140 Promotion Qualification Gates G0–G9

**G0** Before first generation physically seal Preregistration, DB SHA, Control/Treatment Binary Hash, and Sample Manifest.

**G1** Future-source / Entity / Critical Trace violation = **0**.

**G2** Treatment B broadcast-scale contract PASS on all formal works.

**G3** Complete End-to-End Trace. If Provider-backed Rendering is in the route, every accepted final Provider Scene requires a real Provider Receipt.

**G4** Overall Craft B-A median **≥ +5/100**. Historical six-work design: B wins **≥ 4/6 works**.

**G5** Fidelity 25-point subtotal B-A median **≥ -1**. No individual-work regression worse than **-3**.

**G6** Character Voice median B-A **≥ 0**. Historical six-work design: B ≥ A on **≥ 4/6**.

**G7** Repetition/Template median B-A **≥ 0**. Critical duplicate/template violation = **0**.

**G8** At least **2 of 3 Judges** prefer B over A on at least **4/6 works** under the historical six-work design.

**G9** No work may have Overall B-A **≤ -10**. Critical violation = **0**.

Primary Pass: **G0–G9 ALL PASS**.

Permitted claim after PASS: `ELIGIBLE_FOR_SEPARATE_PRODUCTION_PROMOTION_DECISION`.

Automatic Production promotion is forbidden.

---

## 13. Formal result states

Use one explicit state: PASS / FAIL / HOLD / INVALID_PROTOCOL / INCOMPLETE_INFRASTRUCTURE / CLOSED_NOT_SCORED.

Do not increment formal scored count while incomplete, invalid, or still under blind evaluation.

---

## 14. Mandatory result data

For every work × arm preserve: case id; source cutoff; source/binding hash; DB hash; engine/runtime hash; model/settings; request id/hash; response id/hash; Provider Receipt; retry/timeout history; checkpoint lineage; semantic plan hashes; episode/sequence/scene counts; final character count; final script hash; trace root; guard outcomes; future-source leakage outcome; critical flags; blind label; Judge scores/rationale; aggregate score; B-A deltas; G0–G9 verdicts.

Required-null fields must fail closed.

---

## 15. Mandatory experiment artifacts

### Authority / status
1. `00_RETURN_START_HERE.md`
2. `01_FINAL_EXPERIMENT_STATUS.json`
3. `02_AUTHORITY_AND_PACKAGE_HASHES.json`
4. `03_EXECUTION_ENVIRONMENT_REDACTED.json`
5. `04_PREREGISTRATION_AND_AMENDMENT_INDEX.json`
6. `05_CHECKPOINT_RESUME_LEDGER.json`

### Live Provider execution
7. `10_PROVIDER_REQUEST_MANIFEST.json`
8. `11_PROVIDER_RECEIPTS.jsonl` or per-receipt JSON files
9. `12_PROVIDER_FAILURE_RETRY_LEDGER.json`
10. `13_TRUSTED_TRANSCRIPT_HASH_AUDIT.json`

Never include API keys, `.env` secret files, private keys, or plaintext credentials.

### Formal generation
11. `20_SAMPLE_MANIFEST.json`
12. `21_CONTROL_RUNTIME_FREEZE.json`
13. `22_TREATMENT_RUNTIME_FREEZE.json`
14. all Control full-episode outputs
15. all Treatment full-episode outputs
16. semantic/episode/sequence/scene plan artifacts
17. End-to-End trace and guard receipts

### Blind evaluation
18. `30_BLIND_PACKET_MANIFEST.json`
19. all W/X Judge packets
20. `31_COORDINATOR_SECRET_SEALED.*`
21. `JUDGE-01_RESULT.json`
22. `JUDGE-02_RESULT.json`
23. `JUDGE-03_RESULT.json`
24. Judge admissibility records
25. `32_BLIND_AGGREGATE_FROZEN.json`
26. `33_BLIND_MAP_REVEAL_AND_DECODE.json`

### Evaluation / closure
27. `40_R140_100_POINT_SCOREBOOK.json`
28. `41_R140_G0_G9_GATE_VERDICT.json`
29. `42_CRITICAL_VIOLATION_LEDGER.json`
30. `43_INTEGRATED_RESULT_REPORT.md`
31. `44_SCIENTIFIC_CLAIM_BOUNDARIES.md`
32. `45_EXPERIMENT_REGISTRY_ENTRY.json`
33. `46_DEVELOPMENT_TIMELINE.md`
34. `47_ENGINE_EVOLUTION_MAP.md`
35. `48_FRESH_EXTRACTION_VALIDATION.json`

### Delivery / integrity
36. `90_FINAL_DELIVERY_MANIFEST.json`
37. `91_FINAL_HANDOFF_AUDIT.json`
38. Trust Root
39. individual experiment sealed ZIP
40. cumulative Research Master update if authority changed
41. Narrative Engine Master update if authority changed
42. Learning/Analysis handoff update if required
43. current DB package only if authority changed; otherwise identify unchanged DB by hash
44. updated 5-part / 8-package set if any official authority package changed

---

## 16. Failure preservation rule

If any failure occurs: stop the affected gate; preserve exact failed request/output/log/receipt/checkpoint; classify as engine/provider/infrastructure/protocol/judge-metrology/packaging-transport; do not overwrite; do not lower thresholds after seeing results; preregister any allowed repair before changing code/config; mint new hashes/checkpoint; rerun only under the amended protocol.

---

## 17. Exact return procedure from Codex to ChatGPT

When Codex finishes R-F, R-G, Formal R140, or stops at HOLD/FAIL:

### Upload first
1. `00_RETURN_START_HERE.md`
2. `90_FINAL_DELIVERY_MANIFEST.json`
3. `91_FINAL_HANDOFF_AUDIT.json`
4. Trust Root
5. individual experiment sealed ZIP

### Then upload
- all updated 5-part / 8-package authority ZIPs if changed
- all formal output/judge/receipt packages
- any split Research/Engine/DB volumes required by the manifest

If a package is unchanged, the manifest must state `UNCHANGED_BYTE_IDENTICAL` with filename + SHA256.

If split volumes are required, provide deterministic volume names, ordered volume index, per-volume SHA256, reconstructed SHA256, reconstruction instructions, and CRC results.

The accompanying message should state only safe metadata: final status; R-F status; R140 status; formal scored count before/after; formal attempt count; output count; Provider Receipt count; Judge count; G0–G9 verdict; individual seal SHA256; Trust Root SHA256; changed authority packages; missing/held items.

Never paste API keys or secret environment values.

---

## 18. ChatGPT independent re-audit after return

ChatGPT will independently verify the Return Manifest and Trust Root, SHA256 values, package CRC/duplicates/unsafe paths, DB/Engine/Research reassembly if applicable, real Provider Receipts, preregistration-before-output ordering, Blind admissibility and score-freeze-before-map-reveal, aggregate/G0–G9 results, and the formal-count increment. Only after that audit will Physical Closure and/or eligibility for separate Production Promotion review be declared.

Codex self-reported PASS is not by itself final independent closure.

---

## 19. Final prohibition list

Codex must not expose plaintext API credentials; use actual EP06 as answer key; reveal arm identity before score freeze; show Judges another Judge result; silently swap the frozen DB; silently replace model/provider/settings; use superseded R10 CP1 packets; patch Treatment after formal G0 without stopping/re-preregistering; promote local/Test-Double evidence to live Provider evidence; increment formal count before valid formal completion; or auto-promote candidate to Production after R140 PASS.

---

## 20. Required end-state statement

Every return must contain:
`R_F_STATUS`, `R_G_STATUS`, `R140_STATUS`, `FORMAL_SCORED_COUNT_BEFORE`, `FORMAL_SCORED_COUNT_AFTER`, `R140_ATTEMPTS`, `R140_OUTPUTS`, `R140_JUDGE_RETURNS`, `PROVIDER_RECEIPT_COUNT`, `G0_G9_VERDICT`, `PRODUCTION_PROMOTION_STATUS`, `INDIVIDUAL_SEAL_SHA256`, `TRUST_ROOT_SHA256`, `MISSING_OR_HELD_ITEMS`.

If R140 passes, the only allowed promotion-language at this stage is:
`ELIGIBLE_FOR_SEPARATE_PRODUCTION_PROMOTION_DECISION`.
