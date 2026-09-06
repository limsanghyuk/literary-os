# Literary OS — P07-B Retrieval Canonicalization Repair Preregistration Amendment R1
Date: 2026-09-07
Classification: PREFORMAL_ENGINEERING_REPAIR_AMENDMENT__RESULT_BLIND_TO_POSTREPAIR_OUTCOMES
Parent preregistration: `P07B_DB59_CONNECTION_PROPAGATION_PRETEST_PREREG_R1.md`
Attempt-1 HOLD: `P07B_DB59_CONNECTION_PROPAGATION_PRETEST_ATTEMPT1_HOLD_R1.md`
Formal count delta: 0
R140 attempts delta: 0

## Defect being repaired
`rfv2_retrieval.retrieve()` and `rfv2_retrieval.retrieve_many()` currently use different donor-sequence reranking algorithms, so batch/pretest evidence can disagree with the actual runtime donor payload.

## Frozen historical interpretation
Recovered R38-R wording says donor episode/sequence selection is a separate local TF-IDF/cosine stage **inside the already-selected donor works** after work-level top-k selection. It does not specify a per-work donor quota.

Therefore the canonical interpretation for this repair is:
1. work-level selection: one shared TF-IDF/cosine space over all eligible work profiles + query;
2. choose top-k works = 4;
3. donor-sequence selection: one separate local TF-IDF/cosine space over the union of eligible sequence records belonging to those selected works + query;
4. choose global top-k donors = 4;
5. no per-work quota;
6. confidence band is determined only by work-level top1 score; margin remains diagnostic only.

This matches the actual runtime `retrieve()` path already used by `semantic_orchestration` and removes batch-only behavior rather than changing runtime behavior to fit prior batch outputs.

## Repair rule
- Introduce one canonical single-query implementation helper.
- `retrieve()` MUST call that helper.
- `retrieve_many()` MUST call the same canonical helper for each query after a single index validation; performance optimization is secondary to semantic identity.
- No thresholds, profile fields, vectorizer settings, top-k values, query fields, or source-cutoff rules may change.
- No output-specific donor exceptions or work-specific branching may be added.

## Required tests before observing postrepair craft results
1. `retrieve()` vs `retrieve_many()` exact parity on all six sealed development fixtures: decision, selected donor IDs/order, selected semantic hashes, literary payload hash.
2. Direct DB59-built index vs Frozen Index exact byte identity and retrieval parity.
3. Selected donor semantic mutation changes runtime literary payload/provider input.
4. Irrelevant unselected donor mutation MUST use a record outside the selected top-work set; selected donor IDs/order and literary payload hash must remain unchanged.
5. CASE-01 actual `run_verified_hierarchical_semantic_planning()` must carry the same donor IDs/order as canonical retrieval into `SEQUENCE_PLAN` provider input.
6. Frozen Index outer/inner tamper HOLD.
7. Full nonhistorical regression PASS.
8. Source-cutoff violations 0; Python literary prose generation 0; secret pattern hits 0.

## Pass/Fail boundary
- Any runtime/batch parity mismatch = FAIL/HOLD.
- Any selected/unselected causal contract failure = FAIL/HOLD.
- No post-result tuning is allowed. A second repair would require a new preregistered amendment.

## Packaging requirement
Because current C2 runtime code will change, successful repair must be propagated into the canonical 5 Parts / 9 Packages. At minimum C2-A/C2-B change; CONTROL/A/B2 must be updated if current authority/evidence changes. B1/C1/D1/D2 remain byte-identical unless a strictly necessary role-specific change is demonstrated.
