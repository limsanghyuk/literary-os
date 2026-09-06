# Literary OS — P07-B DB59 Connection & Propagation Pretest Preregistration R1
Date: 2026-09-07
Classification: NONFORMAL_PREFORMAL_CONFIRMATORY_MECHANICAL_REVALIDATION
Formal scored count before: 137
R140 before: 0 attempts / 0 outputs / 0 scores
Starting physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07A_RFV2_CONTROLLED_RECOVERY_R1`
Package Set SHA256: `29ac62ea4877858693193bdc3b3f8e950e875c839ae5c54330ceba3e871ff928`
Frozen DB authority: DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## Purpose
Freshly verify, from the currently sealed 5-Part / 9-Package authority, that the frozen DB59 is not merely present/hashed but is correctly reconstructed, bound to the current C2 retrieval route, selected as actual donor semantics, propagated into semantic planning/provider input, and fail-closed under authority/index tamper.

This is confirmatory mechanical revalidation. Earlier 6/6 and 185/185 outcomes are known historical/recovery observations and are NOT targets. No threshold, field, donor, prompt, or rubric tuning is allowed after seeing results.

## Research questions
RQ1. Does D1+D2 reconstruct the exact frozen DB59 authority bytes?
RQ2. Does current C2 load the DB59-bound Frozen Retrieval Index and produce `USE_RETRIEVAL` on the six frozen development cases under the already sealed RFV2 contract?
RQ3. Are Direct DB59 and Frozen Index retrieval decisions/selected donors semantically equivalent on those cases?
RQ4. Does a selected donor semantic mutation change literary provider input while an irrelevant unselected donor mutation leaves literary input unchanged?
RQ5. Do selected DB59 donor payloads reach the actual semantic planning `SEQUENCE_PLAN` provider input on CASE-01?
RQ6. Do DB/index authority mismatches fail closed rather than silently proceeding?

## Frozen inputs
- Exact current 9-package authority only; no older working tree may substitute.
- Current C2 = `C2-A || C2-B`, expected SHA256 `1a9355169650d66af0a3f44fb867bad1c00e5dc643e8f28443d1b2f6c6cde62d`.
- Frozen DB59 = `D1 || D2` logical reconstruction, expected SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- Six existing development fixtures only; no actual EP06 or post-cutoff source may be introduced.
- Existing RFV2 retrieval contract only: work-level THICK functional profiles; TF-IDF/cosine; analyzer `char_wb`; char ngram 2–5; min_df=1; sublinear_tf=True; max_features=120000; top-k=4; HIGH >=0.13; MEDIUM >=0.10 and <0.13; LOW <0.10 -> fallback; top1-top2 margin diagnostic only.
- Existing semantic payload separation and `PYTHON_LITERARY_SURFACE_BYTES=0` rule remain fixed.

## Pretest sequence
1. Reverify package-set manifest/trust-root package hashes.
2. Reconstruct and verify current C2 SHA.
3. Reconstruct/verify frozen DB59 SHA and corpus membership counts.
4. Run six frozen cases through Direct DB59 route.
5. Run same six cases through Frozen Retrieval Index route.
6. Compare retrieval decisions, donor IDs/order, and literary semantic payload hashes.
7. CASE-01 actual semantic planning run using current `semantic_orchestration`; capture exact `SEQUENCE_PLAN` provider input and donor IDs/hashes.
8. Selected-donor controlled semantic mutation test.
9. Irrelevant-unselected controlled semantic mutation test.
10. Frozen Index outer-authority tamper HOLD test.
11. Frozen Index inner DB-binding tamper HOLD test.
12. Current packaged-C2 nonhistorical regression.
13. Scan for source-cutoff violations, Python literary prose generation, and secret patterns.

## Pass gates
P1. All 9 package hashes match current Manifest/Trust Root.
P2. C2 reconstruction exact.
P3. DB59 reconstruction exact and eligible membership is internally consistent; any mismatch = HOLD/FAIL, not retuning.
P4. Six-case runs complete without source leakage; outcome is recorded as observed, not tuned.
P5. Direct/Frozen equivalence holds for decision + selected donor set/order + literary payload hash on all completed cases.
P6. CASE-01 proves selected donor payload reaches actual `SEQUENCE_PLAN` provider input.
P7. Selected donor mutation changes literary provider input.
P8. Irrelevant unselected donor mutation does not change literary provider input when selected donor set/payload is unchanged.
P9. Outer and inner authority tamper fail closed/HOLD.
P10. Python literary prose generation = 0; source cutoff violations = 0; secret pattern hits = 0.
P11. Full nonhistorical regression passes on the exact packaged C2 bytes.

## Interpretation
- Mechanical PASS supports P07-B connection/propagation closure only.
- It does not establish craft improvement, Live Provider validity, CP1, RFV3 success, R-F, R-G, or R140 promotion.
- Any failed gate is preserved as FAIL/HOLD. No result-informed tuning is permitted.

## Packaging rule
If this pretest changes no runtime/package bytes, keep the 9 package files byte-identical and add only an external durable checkpoint/evidence record. If a repair becomes necessary, stop after the failed gate, repair under a new preregistered amendment, then propagate changed->new SHA / unchanged->byte-identical across all 9 packages before any next scientific task.
