# R70 Stage B R2 — Pre-API Virtual Execution Harness Containment Amendment Prereg R1

Date: 2026-09-21
Status: `PREREGISTERED_BEFORE_EXECUTION_HARNESS_CHANGE__LIVE_OUTPUTS_0`

## Parent
Scientific experiment remains:
`R70 Stage B R2 — Exit-State Machine-Contract Repair`

Frozen scientific artifacts remain unchanged:
- Runtime SHA256: `34476d35f365a27e7e8e773b05c2951c4febc72bde8104e29f68e1e6d754d31d`
- Fresh input SHA256: `2d16692cc970e3d54ce66b4dd318c83dcee08170fb2445739095f7750985c56e`
- Paired payload SHA256: `bf0426e1c02c262a328c4691560048bcf737d7f4b3399ad1e0101b17a4e0ed76`
- Hidden mapping SHA256: `c3340b146c3901b4e652b2b947ae76eb9a846fcbaad21a2bd17dda6b0e9cec17`

Live provider outputs remain:
`0`

## Virtual pre-API finding
A transport-faithful Responses API analog was run against the frozen R2 runtime and request hashes.

PASS:
- normal structured response -> 12/12 valid pairs;
- first-attempt EXIT_STATE_MISMATCH then valid retry -> 12/12 valid pairs;
- first-attempt incomplete then valid retry -> 12/12 valid pairs;
- first-attempt HTTP error then valid retry -> 12/12 valid pairs;
- returned model mismatch -> validity hold, 0/12 valid pairs.

DEFECT:
- HTTP 200 + malformed output_text causes uncaught JSONDecodeError;
- HTTP 200 + refusal/no output_text causes uncaught ValueError;
- runner terminates after first provider call instead of recording an invalid attempt and applying the frozen retry rule.

## External API relevance
OpenAI Structured Outputs can return explicit refusal content and Responses may end in incomplete/failed/cancelled/other non-completed states. The execution harness must contain provider parsing exceptions without changing the frozen request or Candidate runtime.

## Allowed repair
Execution harness only:
1. Wrap `provider.generate(...)` in exception containment.
2. Convert post-transport parse/refusal exceptions into a non-OK provider_result for that attempt.
3. Preserve exact request bytes, transport receipt and raw provider response already captured by the observation wrapper.
4. Continue under the existing maximum-two-attempt retry rule.
5. Never convert an exception into a valid arm.
6. Preserve all frozen request hashes exactly.

Post-run audit may be improved only to distinguish validity provenance failures (for example model mismatch) from local-guard reasons.

## Prohibited
No change to:
- frozen R2 runtime;
- Provider request construction;
- renderer instructions;
- dynamic output schema;
- exit_state guard;
- Control context;
- Treatment context;
- inputs;
- paired payloads;
- hidden mapping;
- provider/model/reasoning/token settings;
- retry count;
- literary quality gate.

## Qualification gates
H1. All 24 frozen requests remain byte/hash identical.
H2. Happy path -> 24/24 valid arms, 12/12 valid pairs, 24 calls.
H3. Exit-state first-fail -> retry -> 12/12 valid pairs, 48 calls.
H4. Incomplete first-fail -> retry -> 12/12 valid pairs, 48 calls.
H5. HTTP first-fail -> retry -> 12/12 valid pairs, 48 calls.
H6. Model mismatch -> 0/12 valid pairs and VALIDITY_HOLD, no crash.
H7. Malformed output_text -> bounded retries, VALIDITY_HOLD, no crash.
H8. Refusal/no output_text -> bounded retries, VALIDITY_HOLD, no crash.
H9. Credential string absent from all artifacts.
H10. Mapping remains hidden.
H11. Post-run output seal/audit completes for every non-crash scenario.
H12. Runtime/input/payload/mapping hashes remain unchanged.

Only after H1-H12 PASS may a revised execution bundle replace the previous runner bundle for future live Codex/API execution.

Status token:
`R70_R2_PREAPI_VIRTUAL_FINDING__EXECUTION_HARNESS_EXCEPTION_CONTAINMENT_ONLY__PREREGISTERED__LIVE_OUTPUTS_0`
