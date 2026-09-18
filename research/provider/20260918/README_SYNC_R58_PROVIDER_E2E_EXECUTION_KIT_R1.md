# SYNC-R58 Provider E2E Execution Kit R1

Status: `PREPARED__NO_ENGINE_CODE_CHANGE__PROVIDER_OUTPUTS_0`

This directory contains the execution infrastructure for the preregistered experiment:

`SYNC_R58_PROVIDER_E2E_FULL_EPISODE_QUALIFICATION_R1`

Canonical preregistration:
`research/provider/20260918/SYNC_R58_PROVIDER_E2E_PREREG_R1.md`

## Authority boundary

- Physical Candidate: **SYNC-R58 `ADAPTIVE_UL16`**
- Integrated runtime SHA256:
  `30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`
- C1 transport SHA256:
  `9282eb4b3241c13e17cf032c3814674409d5efac67c26024580930ecbb633307`
- Production/control remains **ENG:R47 / LEGACY_R53**
- This execution kit changes **no Candidate/runtime code**
- Physical authority remains **SYNC-R58**
- 5-Part / 9-package set is therefore unchanged

## Files

### 1. `prepare_sync_r58_p06_provider_request_r1.mjs`

Fail-closed request builder.

Frozen input source after legal blind-mapping reveal:
- J02 R58 Architecture Blind packet
- exact packet ZIP SHA256:
  `4a4a4100c4dbe85bbe9689606c5f11781c4b790ddb673946db01c4787aca9066`
- pair: **P06**
- legally revealed Candidate arm for J02 P06: **A**

The builder:
1. verifies the exact sealed J02 packet SHA;
2. reads JSON members using the system `unzip` command;
3. recursively locates P06;
4. extracts Candidate arm A;
5. fails closed if the source is ambiguous or missing;
6. writes:
   - `p06_candidate_architecture.json.txt`
   - `provider_surface_prompt.txt`
   - `provider_request.json`
   - `provider_request_manifest.json`
7. records architecture/prompt/request SHA256 values.

It does not call the Provider.

### 2. `run_openai_responses_with_receipt_r1.mjs`

Receipt-capable Provider runner.

It:
1. reads the exact frozen JSON request bytes;
2. reads the API secret only from the execution environment;
3. sends the exact request bytes to the OpenAI Responses endpoint;
4. records:
   - Provider response id;
   - `x-request-id` when returned;
   - requested/provider model;
   - usage receipt;
   - timestamps;
   - exact request-body SHA256;
   - raw response-body SHA256;
   - extracted screenplay-text SHA256;
   - retry count and retry reason;
   - transport/HTTP failure receipt;
5. writes:
   - `provider_raw_response.bin`
   - `provider_output_text.txt`
   - `provider_receipt.json`

The API secret is never written to the receipt.

## Execution order in a receipt-capable environment

1. R6-sync the physical SYNC-R58 authority.
2. Verify the sealed J02 packet bytes at the frozen SHA above.
3. Run the P06 request builder with an explicit model identifier.
4. Seal the generated request manifest before Provider execution.
5. Run the receipt runner on that exact request JSON.
6. Preserve every failed attempt receipt; never discard a failed call.
7. Do not count an output unless the receipt contains the required Provider identifiers/hashes.
8. Require the final screenplay to satisfy the preregistered >=35,000 Korean-character and E6/E3 regression gates.
9. Only then begin the independent screenplay-judge stage.

## Secret handling

The runner expects the Provider API secret to be injected by the execution environment / secret manager. Do not paste or store a raw API key in chat, GitHub research files, request JSON, or receipt artifacts.

## Current execution state

- Request builder source: **PREPARED**
- Receipt runner source: **PREPARED**
- Static syntax parsing: **PASS**
- Frozen request output: **0** (builder has not been executed in a healthy container)
- Provider outputs: **0**
- Current coordinating container: **TransportTimeoutError even on minimal commands**
- Same-chat text is not valid Provider evidence

Current token:

`SYNC_R58_PROVIDER_EXEC_KIT_R1__SOURCE_PREPARED__SYNTAX_PASS__REQUEST_NOT_BUILT__PROVIDER_OUTPUTS_0__NO_ENGINE_CODE_CHANGE__PHYSICAL_AUTHORITY_UNCHANGED`
