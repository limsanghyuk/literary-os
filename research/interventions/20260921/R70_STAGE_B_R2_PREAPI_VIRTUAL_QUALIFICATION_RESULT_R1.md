# R70 Stage B R2 — Pre-API Virtual Provider Analog Qualification Result R1

Date: 2026-09-21
Status: `PASS__PREAPI_EXECUTION_HARNESS_QUALIFIED__LIVE_OUTPUTS_0`

## Purpose
Before connecting the real OpenAI API, reproduce the frozen R70 Stage B R2 execution contract in a transport-faithful virtual Responses API environment and detect execution-harness defects without changing the scientific treatment.

## Frozen scientific identity — unchanged
- Physical Authority: **SYNC-R67**
- Active Qualified Candidate: **R69/R68/R67/R66 lineage**
- Production: **ENG:R47 / LEGACY_R53**
- R2 Runtime SHA256: `34476d35f365a27e7e8e773b05c2951c4febc72bde8104e29f68e1e6d754d31d`
- Fresh Input SHA256: `2d16692cc970e3d54ce66b4dd318c83dcee08170fb2445739095f7750985c56e`
- Paired Payload SHA256: `bf0426e1c02c262a328c4691560048bcf737d7f4b3399ad1e0101b17a4e0ed76`
- Hidden Mapping SHA256: `c3340b146c3901b4e652b2b947ae76eb9a846fcbaad21a2bd17dda6b0e9cec17`
- Live Provider Outputs: **0**
- Mapping revealed: **NO**

## Virtual analog method
The frozen R2 runner and frozen OpenAI Responses request bytes were exercised against an in-process transport analog that returns Responses-shaped envelopes with:
- HTTP status / x-request-id;
- response ID;
- returned model ID;
- status;
- usage;
- message/output_text or refusal content.

The real frozen request builder, structured-output schema, local guard, retry loop, checkpoint custody and post-run audit were used.

## Initial virtual findings
PASS before repair:
1. Normal structured output -> 24/24 valid arms, 12/12 valid pairs, 24 calls.
2. First-attempt exit_state mismatch -> second-attempt recovery -> 12/12 pairs, 48 calls.
3. First-attempt incomplete -> retry recovery -> 12/12 pairs, 48 calls.
4. First-attempt HTTP error -> retry recovery -> 12/12 pairs, 48 calls.
5. Persistent returned-model mismatch -> 0/12 pairs / VALIDITY_HOLD / no crash.

New execution-harness defect found:
- HTTP 200 + malformed output_text caused uncaught JSONDecodeError.
- HTTP 200 + refusal/no output_text caused uncaught ValueError.
- Runner stopped after first call instead of applying the frozen retry rule.

This is relevant because Structured Outputs can return explicit refusal content and Responses API has non-completed terminal/intermediate states.

## Amendment
Preregistered BEFORE harness modification:
`research/interventions/20260921/R70_STAGE_B_R2_PREAPI_EXECUTION_HARNESS_AMENDMENT_PREREG_R1.md`

Commit:
`a5a2535a192e9b035a3bff6cff0ba411dc1d658f`

Allowed repair only:
- runner catches post-transport provider parsing/refusal exceptions;
- stores a non-OK provider_result;
- preserves raw response/transport custody;
- applies the unchanged maximum-two-attempt retry rule;
- exception can never count as valid.

The post-run audit was also improved to distinguish provenance validity failures such as model mismatch.

No Candidate runtime, prompt, schema, guard, context, inputs, mapping or quality thresholds changed.

## Revised harness
Runner R2 SHA256:
`1af544fc13e93e51f5c4fd8d657be6fc5896fc3bb2b130ee43e5b4fa1743a42c`

Post-run Audit R2 SHA256:
`c6b77acf0db285fe4ab11ec5f9279e565b24d9614ce0394c2a92ce8af2db67d4`

Revised Execution Seal SHA256:
`b23b7348174977f1befd8bc0171449fc77d52046149f6f589cf918f6d46b73d2`

Pre-API Qualification Receipt SHA256:
`c2b309ca76cab4128e3b65987b2d73c1d1a208374384b21033d89894f14c4166`

Pre-API Validated Codex Bundle SHA256:
`cfd1541e3eb533af209ecd1254eacf21896b3564b6f3b1a3d44ca10dd67f2503`

## Final virtual qualification matrix
1. Happy path -> PASS / 12/12 valid pairs / 24 calls.
2. Exit-state first-fail then valid -> PASS / 12/12 / 48 calls.
3. Incomplete first-fail then valid -> PASS / 12/12 / 48 calls.
4. HTTP error first-fail then valid -> PASS / 12/12 / 48 calls.
5. Failed-status first-fail then valid -> PASS / 12/12 / 48 calls.
6. Model mismatch persistent -> expected VALIDITY_HOLD / 0/12 / no crash.
7. Malformed JSON first-fail then valid -> PASS / 12/12 / 48 calls.
8. Refusal first-fail then valid -> PASS / 12/12 / 48 calls.
9. Persistent malformed JSON -> expected VALIDITY_HOLD / 0/12 / no crash.
10. Persistent refusal -> expected VALIDITY_HOLD / 0/12 / no crash.

Additional:
- no-key preflight: PASS; exits before first provider call and creates no output directory;
- existing-output rerun protection: PASS;
- fake credential artifact leakage: 0;
- live-looking secret scan in revised bundle: 0;
- hidden mapping file included in execution bundle: 0;
- bundle ZIP CRC: PASS;
- all SHA ledger entries: PASS.

## Claim boundary
This PASS establishes:
`R70_STAGE_B_R2_EXECUTION_HARNESS_PREAPI_QUALIFIED`

It does NOT establish:
- actual OpenAI Provider literary output quality;
- F08 surface-effect qualification;
- 12/12 live valid pairs;
- J01/J02/J03 preference result;
- Level-3 restoration.

## Exact next operation
When real API/Codex execution becomes available, use ONLY:
`R70_STAGE_B_R2_CODEX_EXECUTION_BUNDLE_R2_PREAPI_VALIDATED.zip`

Do not use the older R1 runner bundle.

Then:
1. inject OPENAI_API_KEY via environment/secret mechanism;
2. run revised sealed runner;
3. run post-run audit;
4. if and only if 12/12 valid pairs -> seal blind packets -> J01/J02/J03 -> mapping reveal -> unchanged quality gate.

Status token:
`R70_R2_PREAPI_VIRTUAL_ANALOG_PASS__EXECUTION_HARNESS_EXCEPTION_CONTAINMENT_REPAIRED__SCIENTIFIC_INPUTS_UNCHANGED__LIVE_OUTPUTS_0__READY_FOR_REAL_PROVIDER_WHEN_AVAILABLE`
