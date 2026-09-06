# Literary OS — RFV2 / CP1 Recovery Pending Checkpoint R1
Date: 2026-09-06

Status: `RFV2_REPRETEST_ACTIVE__R140_HARD_BLOCK__CP1_CURRENT_AUTHORITY_RESTORATION_PENDING`

## Scientific state
- Formal scored count: 137
- Latest formal scored: R138
- R140: 0 attempts / 0 outputs / 0 scores
- Production: ENG:R47 immutable
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- No new Formal count is authorized by this checkpoint.

## Why RFV2 exists
Claude CT Addendum 7 independently confirmed that the prior R11 C2 R39 path could execute the DB archive code yet still deliver `NO_RETRIEVAL` to semantic planning, that the former DB-dependency test had been inverted, and that the current R11 `rf_live_parity_runner.py` had no successful CP1 live path. The previous RFV Provider-boundary evidence remains useful, but its DB-adoption-completeness claim is withdrawn.

## Frozen RFV2 preregistration / amendments already created before the corresponding repairs
- RFV2 preregistration SHA256: `1ccce076164cfad67297f639195342cf859bf29e041206df2abae51372b6ce3d`
- Retrieval Contract Restoration Amendment A1 SHA256: `0a430cca636b4be0597eb1c433ab40407677804f47544edbdd2f66e98fa7f20d`
- Source Scope / Dependency Addendum A1.1 SHA256: `f438c626668173baa3ae0d9befba8333ef193a9935394a03ce96c8909b4c1373`
- Work Profile Unit Correction Addendum A1.3 SHA256: `ae7ca2b59668b909f26e4f1636161bb401259bdc8c25ad45ab475ccc999fe828`
- Governance normalization checkpoint SHA256 previously reported: `ff35e99334c5c5dbffaeddba3479d62ed98b2f08239136d3367b68027411f7c8`

Some local addendum numbers A1.5/A1.6 were duplicated during engineering exploration. They are not to be treated as a linear scientific lineage merely by filename. The final physical closure must publish one normalized amendment index and explicitly mark superseded proposal branches.

## Last locally verified RFV2 engineering results before container-backend interruption
The following were reported from direct local execution before the current backend interruption and must be reverified during Fresh Extraction before physical closure:
- Actual DB59 eligible retrieval corpus: 1,097 THICK members / 10,784 records.
- Six historical EP06-style development cases: 6/6 `USE_RETRIEVAL` after restoration.
- Each case selected four donor records/works under the restored retrieval contract.
- Direct DB59 vs Frozen Retrieval Index: 6/6 selected donor and retrieval-payload equivalence.
- Frozen Retrieval Index SHA256: `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`.
- Frozen Index equivalence/tamper audit SHA256: `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`.
- CASE-01 verified semantic-planner end-to-end evidence SHA256: `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`.
- Selected donor mutation changes semantic provider input; unselected irrelevant donor mutation does not change semantic provider input when selected donor bytes are unchanged.
- Current non-history local regression after the DB-dependency repairs: 185/185 PASS.

These results are engineering evidence, not live Provider evidence and not Formal R140 evidence.

## Retrieval restoration rule
Do not treat the repair as an arbitrary lowering of `0.60` after observing outcomes. The active restoration is based on the earlier sealed R37/R38 retrieval design: work-level TF-IDF `char_wb`, ngram 2–5, cosine similarity, top-k=4, confidence bands HIGH >=0.13 / MEDIUM >=0.10 and <0.13 / LOW <0.10 fallback. The historical `0.03` top-1/top-2 margin is not to be used as a hard gate in the restored path; retain it only as diagnostic evidence unless a later preregistered amendment explicitly changes this.

Current R-F/R0C source membership remains authoritative: DB59 THICK eligible member set, target-work EP06+ excluded, source cutoff EP01–EP05 for the formal target. Do not silently broaden to EpisodePlan or other source layers just to reproduce historical search documents.

## CP1 historical authority and current defect
The current R11 runner was independently verified to have no successful CP1 branch (`CP1 is deliberately not implemented`). This remains a hard blocker.

However, historical P07-PRE-09 evidence records a previously created Live Craft Parity Runner with SHA256:
`d5d82b3f1791d36d8723e510a46fa9d272fef70b27cd8c85f99f97ac0d0e7adf`

Historical CP0 authority also records:
- Live Craft Parity preregistration SHA256 `b61d469585896277a97ab2153073be45c2eb554ca28524b8c72a370dd94b46bd`
- CP0 checkpoint SHA256 `2db5eab97fd83cfdacbdedea81316f712fbe6859b832912e4607157e49e94b72`
- CP1 had not started; real Provider calls/outputs remained zero.

The historical CP1 contract is to regenerate semantic plans from EP01–EP05 with the actual LLM and compare Reference vs Engine under the same provider/model/settings. It must not use the E9 scripted fixture as craft evidence.

## Mandatory CP1 restoration — no improvising
Do not invent a new CP1 scientific design. Restore the historical paired structure into the current RFV2 candidate while preserving current safety/evidence contracts:
1. CASE-01 only for CP1 smoke.
2. Paired Reference Arm and Engine Arm.
3. Same OpenAI Responses API provider, same frozen model/settings for both arms.
4. Six semantic stages per arm: Series Plan -> Episode Allocation -> Episode Plan -> Ensemble/Ecology -> Sequence Plan -> Scene Plan.
5. Deterministically select first / middle / last planned scene for CP1 surface realization, maximum three surface scenes per arm.
6. Engine Arm must use the current verified DB59/Frozen Retrieval Index path and prove DB59 donors are present in the semantic provider input.
7. Reference Arm must use the preregistered reference orchestration, not the Engine treatment modules.
8. Current R-E Surface Craft / structured source-derived voice profile requirements apply to accepted surface rendering where the frozen CP1 protocol requires them.
9. Current R-FV Provider-boundary integrity applies: returned model binding, request/response hash binding, malformed/refusal normalization, bounded retry, failed attempts never promoted to Provider Evidence.
10. Python literary prose generation = 0.
11. Actual OpenAI credential must never be embedded in source, logs, ZIPs, receipts, or chat.
12. No actual live call until the restored runner passes TestDouble/fail-closed rehearsal and a new CP1-ready checkpoint is physically sealed.

## Required CP1 TestDouble rehearsal before any live call
- exact paired arm count = 2
- semantic call count = 6 per arm
- surface selected scenes = first/middle/last, max 3 per arm
- Reference and Engine provider/model/settings identity = exact
- Engine retrieval decision = `USE_RETRIEVAL` for CASE-01 under the restored DB59 path
- Engine SEQUENCE_PLAN/SCENE_PLAN semantic provider input contains the selected DB59 donor payload/binding
- no-key => HOLD and live provider calls = 0
- key-present but explicit live permission absent => HOLD and live provider calls = 0
- model mismatch => BLOCK/HOLD
- trusted request/response hash mismatch => BLOCK/HOLD
- malformed/refusal/retryable failures follow current provider-boundary contract
- Provider Receipt count is exactly the accepted successful call count and failed retries are not receipts
- Python literary prose bytes = 0

## Fresh-closure gates after CP1 restoration
Before RFV2 Physical Closure:
1. re-run actual DB59 1,097/10,784 six-case audit;
2. direct DB59 vs Frozen Index equivalence 6/6;
3. selected/unselected donor causal-propagation tests;
4. full non-history regression, with the exact test scope and count recorded;
5. Provider failure/receipt proxy suite;
6. CP1 paired TestDouble rehearsal;
7. fresh extraction from the final candidate bytes and repeat all gates;
8. scan package runtime for `.pyc`, `.pytest_cache`, plaintext credentials, and blind coordinator secrets; move blind secrets outside executable runtime;
9. only after all gates PASS, propagate the exact final bytes into the 5-Part / 9-Package authority set.

## 5-Part / 9-Package rule
Future authority delivery baseline:
CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2 = 9 packages.
Do not publish an intermediate RFV2 repair as current authority. C2-A and C2-B must reconstruct the exact sealed C2 authority bytes and the reconstruction SHA must be stated in the delivery manifest.

## Infrastructure interruption
At creation of this checkpoint, local `container` and Python execution backends repeatedly returned `ClientError`, including minimal `/bin/echo` calls. Per project rule this is an infrastructure UNKNOWN/HOLD, not experiment FAIL and does not increment any attempt or Formal count.

## Resume rule
When local execution is healthy:
1. health check;
2. verify the last RFV2 local working tree and all prereg/amendment hashes;
3. recover the historical CP1 runner bytes if available from the prior sealed package and verify SHA `d5d82b3f...e7adf`;
4. compare historical runner with the current R11 runner and current verified semantic runtime;
5. freeze a CP1 Restoration Amendment before changing CP1/current runtime bytes if not already frozen locally;
6. implement only the restoration delta above;
7. run CP1 TestDouble rehearsal;
8. complete RFV2 fresh closure and only then rebuild 5-Part / 9-Package authority.

Current Pointer must remain at the pre-RFV2 physical authority until those gates are complete. Formal R140 remains forbidden.