# Contract / Load Consumption Receipt Specification R1

Date: 2026-09-12
Classification: ENGINEERING_GOVERNANCE_SPEC__NO_RUNTIME_PROMOTION

## 1. Problem
Historical evidence shows that a repaired contract or code artifact can exist without proof that the active generation path actually consumed it. Package presence, successful unit tests, and a repaired development overlay are not sufficient evidence of runtime use.

## 2. Required receipts
Every future generation or integration run that claims use of a protected contract/capability must emit both receipts below.

### A. ACTUAL_LOAD_RECEIPT
Required fields:
- run_id / job_id / provider_receipt_id where applicable
- execution_entrypoint
- loaded_module_or_artifact_path
- loaded_sha256
- expected_role
- expected_sha256 or allowed_sha_set
- package_transport_source
- load_time
- process/runtime identity
- result: PASS / FAIL

Hard rule: a role cannot be claimed as repaired/active merely because a repaired copy exists elsewhere. The actually loaded SHA must be recorded.

### B. CONTRACT_CONSUMPTION_RECEIPT
Required fields per contract:
- contract_id
- required_for_run
- source_path
- source_sha256
- consumer_component
- invocation_count
- first_invocation_stage
- last_invocation_stage
- input_binding_sha256
- output_binding_sha256
- zero_invocation_reason

Hard rule: any preregistered `required_for_run=true` contract with invocation_count=0 invalidates the claimed contract-enabled run before scoring/promotion.

## 3. Inheritance rule
A new pipeline path must inherit the required-contract set from its parent path unless the preregistration explicitly removes a contract before outputs. Silent omission is forbidden.

## 4. Current engine-self-description audit target
Observed historical split to resolve prospectively:
- original/current-carrier copy: `engine_self_description.py`, 15,972 bytes, SHA256 `8d176c2baf550eb61e64732332a3fffd627f19c742f4ef5ed2e6babbddb0b4fe`
- repaired development-overlay copy: 17,444 bytes, SHA256 `01474be7aac676937ba80dedafdc71ec2b8fc7d4ece4291636996b8a63e1f0ec`

This specification does NOT declare which should be production authority. It requires an execution-path audit to prove which copy is actually loaded in each role and why.

## 5. Promotion boundary
No pointer reassignment, carrier replacement, Active Engine promotion or Production promotion follows merely from a load audit. If a repaired candidate is to replace a current carrier, it must undergo its own regression, integration, package reseal and promotion gate.

## 6. Package implications
Research-only receipt specifications normally propagate through CONTROL/A/B2. If instrumentation changes runtime/candidate code, C1/C2 candidate transports change and must be fully re-audited. Production ENG:R47 remains immutable absent explicit promotion.

Status: SPEC_SEALED__EXECUTION_PATH_AUDIT_REQUIRED__NO_AUTHORITY_CHANGE
