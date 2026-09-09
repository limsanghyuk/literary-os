# P07 SEMANTIC CONTRACT ALIGNMENT VIRTUAL R1 — CANDIDATE CLOSURE

Date: 2026-09-09

## CLASSIFICATION
`VIRTUAL_QUALIFIED_SHADOW_CANDIDATE__LIVE_CONFIRMATION_REQUIRED__NO_ACTIVE_AUTHORITY_PROMOTION`

Current active physical authority remains:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R3`.

This cycle does **not** establish OpenAI Live qualification, Production promotion, Formal R140, I4I execution, or DB64 adoption.

## PARENT
- Active parent: P07-I4H Recovery R3.
- Parent package-set SHA256: `9327630e8fc8c9b88a8233055b939e08ab5d3726a777b44122bb6682a8c436f8`.
- Parent combined C2 SHA256: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- RFV2 frozen index SHA256: `e13b55f940ad3395e6db2a63829cc70e4754acd7438104ee2aba1ee07b0905cb`.

## ROOT CAUSE CLOSED IN THIS CYCLE
Frozen Codex Live diagnostic reached SERIES_PLAN → EPISODE_ALLOCATION → EPISODE_PLAN → SEQUENCE_PLAN with real OpenAI Responses calls, then stopped at `SEMANTIC_JUDGE_INVALID:POSITIVE_JUDGMENT_CROSS_GROUP_EVIDENCE`.

Root cause: validator required positive evidence IDs to stay inside the same semantic group, while the Judge prompt/payload did not explicitly communicate that restriction. The real frozen output had 13 raw positive and 2 raw negative judgments; packet invalidity was incorrectly liable to be summarized as if all obligations were literarily unfulfilled.

Treatment aligns Prompt/Payload/Schema/Validator and separates `JUDGE_INVALID` from `VALID_SEMANTIC_HOLD` without weakening fail-closed semantics.

## AUTHORIZED CODE DELTA
Parent tree → candidate tree:
- added `literary_os_runtime/semantic_contract_v2.py`;
- changed `literary_os_runtime/semantic_orchestration.py`;
- added two semantic alignment tests;
- added two frozen Codex judge fixtures.

Final code hashes:
- `semantic_orchestration.py`: `dd5e60dd2d8e6f88f9b9ff5b9d53cd565cbad5a172858cb10ed93ee68d6fb4c6`;
- `semantic_contract_v2.py`: `3516d49bdcb9dfe55928122fb1bdae4f32f78b7d969b1f59133d399b3bc5baee`.

I4H/I4D frozen runtime 8/8 remained byte-identical.

## TEST RESULTS
- Parent nonhistorical baseline: `258/258 PASS`.
- New alignment tests: `23/23 PASS`.
- Candidate nonhistorical + alignment: `281/281 PASS`.
- Candidate physical C2 rematerialization regression: `281/281 PASS`.
- Critical false accepts: `0`.

## PROVIDER-ANALOG MATRIX
The developer stated that an API-capable Codex environment was not available, so this cycle used a local Responses-compatible Provider-Analog. This is not a preregistration rewrite and does not satisfy the original fresh-Live gate.

The analog path used the real `OpenAIStructuredSemanticProvider`, local HTTP `/v1/responses`, strict JSON schema validation, Responses-style IDs/envelopes, TrustedTransport receipts, frozen DB59/RFV2, and explicit test-double classification (`provider_backed=false`).

1. Compliant same-group judgments:
   - result `PASS`;
   - `SCENE_PLAN` reached;
   - 9 Semantic Fulfillment Judge calls total (Episode→Sequence + 8 Sequence→Scene);
   - all 9 hierarchy verdicts ACCEPT;
   - receipt chain PASS.
2. Frozen semantic reality preserved as 13 positive / 2 negative:
   - result `VALID_SEMANTIC_HOLD`;
   - repair decision `REPAIR_CHILD`;
   - validated unfulfilled count `2`;
   - SCENE_PLAN not called.
3. Intentional cross-group evidence packet:
   - result `SEMANTIC_JUDGE_INVALID_HOLD`;
   - invalid reason `POSITIVE_JUDGMENT_CROSS_GROUP_EVIDENCE`;
   - validated unfulfilled count unavailable/null rather than fabricated;
   - SCENE_PLAN not called.

This demonstrates that the treatment does not force a PASS: valid semantic omissions remain HOLD and malformed judge packets remain invalid.

## EXECUTION INCIDENTS PRESERVED
- One initial parent-suite failure was an intentionally preserved historical fixture; correct nonhistorical parent baseline was 258/258.
- Early result summary incorrectly reported `scene_plan_called=false` despite actual Sequence→Scene verdicts. Cause was bookkeeping that did not account for multiple judge results; final summaries use actual call trace.
- Tool timeouts left prior commands running in the background. One rejected branch temporarily removed the `RFV2_INDEX_REQUIRED_FOR_DB59` fail-closed guard. That branch was not accepted. The exact last-known-good treatment hash `dd5e60...` was restored and both 23/23 and 281/281 were rerun before packaging.
- Provider-Analog multi-mode server shutdown caused infrastructure timeouts; modes were rerun independently without changing frozen inputs or treatment.

## PHYSICAL CANDIDATE DELIVERY
Only five transport files changed in this cycle and were physically rebuilt/audited for developer delivery:
- CONTROL candidate SHA256 `0f93af6a07ea0459c22c1fa5073fdada303a18b0550325d34d656bb8bc1df479`;
- Part A candidate SHA256 `9cdff8f8711f41ea6f42299992c769c49db27f0112cecd3a406e990c770b0671`;
- Part B2 candidate SHA256 `e8da85d897b99c2b5b07c6b42615ff55d374f14cbb39970614db131e6ca74ef0`;
- C2-A candidate SHA256 `bce009adf7b031eb537be4f50dfa03e6a0eb4fb847677fa1199b6dbc9a403468`;
- C2-B candidate SHA256 `6ca6198ae8968689aa0020a7544a2d8242b0ae7eafb061880481fef25167fcc7`.

Reuse byte-identical R3 B1/C1/D1/D2.

Candidate combined C2:
- bytes `318521975`;
- entries `3795`;
- SHA256 `36d93da0aeb8306234ce6b0951a9f6ddbe17b8b331c322bf80d51bac3b2eae1b`;
- CRC PASS;
- duplicate path 0;
- unsafe path 0;
- symlink 0;
- encrypted 0.

Full logical 9-set manifest hash:
`924ff25023a969ee47b729eee94a2b8a64b9d474da5e45377db701bbbc3199db`.

## FIXED STATE
- Active authority: I4H Recovery R3 (unchanged).
- Production: ENG:R47.
- Formal scored count: 137.
- Latest formal: R138.
- R140: 0/0/0.
- I4I: 0/0/0/0.
- DB59 frozen.
- DB64 candidate not adopted.

## NEXT EXACT RESEARCH BOUNDARY
When a genuine OpenAI API-capable environment is available, execute the original frozen fresh-Live confirmation against this exact candidate without changing thresholds or treatment. If the valid hierarchy accepts, require SCENE_PLAN reach and complete receipts. A valid semantic HOLD remains HOLD. Only after real Live confirmation may physical Active Authority promotion be considered.
