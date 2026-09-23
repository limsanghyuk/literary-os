# R76 Provider-Analog Responsible-Ancestor Repair Generalization Result R1

Date: 2026-09-23

## Final status
`PASS__PROVIDER_ANALOG_STRUCTURAL_GENERALIZATION__SURFACE_NOT_YET_QUALIFIED`

## Provider Analog
OpenAI Responses-API-like contract implemented in clean GitHub Actions runners:
- request: model + input
- response: id / object / status / output / usage / error boundary
- x-request-id
- X-Client-Request-Id
- 200 / 400 / 429 / 500 contract checks

Model token used by the harness:
`gpt-5.6-sol-provider-analog`

Boundary:
This is a protocol/runtime analog. It is NOT an OpenAI-hosted model and makes no neural-weight,
sampling-distribution, latency, safety-stack, or prose-quality equivalence claim.

## R2A lineage

### R2A-R1
All-pairs semantic cohesion removed zero-related pairs but remained at 8 sequences.
Result: FAIL.

### R2A-R2
Rule:
- all-pairs relation >=2
- no internal dependency edge -> max 3 obligations
- any internal dependency edge -> max 4

Frozen engineering case:
- 9 sequences
- zero-related pairs 0
- clone/omission 0
Result: engineering PASS.

Fresh replication:
- 8 sequences
- zero-related pairs 0
Result: FAIL.
Conclusion: R2A-R2 did not generalize.

### R2A-R3
Preregistered repair:
A 4-obligation bundle is allowed only when:
- >=3 of 4 members participate in internal dependency edges; AND
- internal independent-root count <=2.
All-pairs cohesion remains required.

Original frozen R76 clean-room run:
- Actions run: 35860614230
- sequence_count = 9
- bundle sizes = [3,3,3,3,3,3,2,3,3]
- full coverage exactly once
- zero-related pairs = 0
- invalid four-bundle count = 0
- PASS

Fresh replication:
- work = SYNTH_R76_NIGHT_FERRY_TERMINAL
- Actions run: 35860635840
- sequence_count = 9
- bundle sizes = [3,3,3,3,3,3,4,3,1]
- full coverage exactly once
- zero-related pairs = 0
- invalid four-bundle count = 0
- PASS

## R2B Semantic Transaction Role Preservation
Repair:
Preserve evidence-derived dramaturgical subrole inside `transaction_kind_role`.
Do not change R68 F04 >=3 threshold.
Do not use obligation IDs in semantic signatures.

Original frozen R76:
- baseline coarse-role F04 groups present
- treatment F04 repetition groups = 0
- PASS

Fresh replication:
- baseline coarse-role F04 groups present
- treatment F04 repetition groups = 0
- PASS

## Combined provider-analog gates
Both original and fresh replication:
- Provider contract PASS
- obligation coverage exact once PASS
- clone/omission 0 PASS
- zero-related pairs 0 PASS
- invalid four-bundle 0 PASS
- sequence count >=9 PASS
- sequence count <=14 PASS
- F04 repetition groups 0 PASS
- F04 threshold unchanged PASS
- IDs excluded from semantic signature PASS
- independent GitHub Actions clean-room PASS

## Scientific interpretation
The previously observed R76 Stage-A structural blockers now have a generalizing repair
in the protocol-equivalent Provider-Analog structural environment.

This DOES NOT yet prove:
- exact R69 full-runtime bit-equivalent retest
- actual OpenAI model prose behavior
- >=35,000-character screenplay quality
- external blind quality
- Operational Level-3
- Production promotion
- R140

## Next gate
R76 Stage-B may begin only after a provider-semantic generation boundary is sealed:
1. preserve the Responses-API-like request/receipt envelope,
2. feed the repaired 9+ sequence / 45+ scene contract,
3. generate >=35,000-char Korean broadcast screenplay,
4. perform whole-episode architecture reverse reconstruction,
5. perform scene-sample surface-craft blind evaluation,
6. commit state only from observed screenplay evidence.

Physical Authority remains SYNC-R72.
Production remains ENG:R47 / LEGACY_R53.
Runtime DB remains DB59 frozen.
DB64-R128 remains research-only.
