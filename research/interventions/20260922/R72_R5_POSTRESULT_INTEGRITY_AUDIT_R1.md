# R72 R5 Post-Result Integrity Audit R1

Date: 2026-09-22

Status:
`PASS_WITH_DOCUMENTED_PROTOCOL_METADATA_MISMATCH__SCIENTIFIC_RESULT_REMAINS_FROZEN_LEDGER_NEGATIVE_RESULT`

## DB64 materialization
- Logical DB64 SHA256: `4703e9a99da2deb66eef08f09b08141db6c4d19bc76f77d1c8159dcb7633d6e7`
- consumer_ready_r53 independently verified works: 72
- selected works all in consumer_ready_r53: PASS
- selected referenced source/planner/thread-state paths missing: 0

## Frozen R5 case ledger
- selected cases: 24
- LOW/MEDIUM/HIGH: 8 / 8 / 8
- distinct works: 16
- max cases/work: 2
- R71 primary-work overlap: 0
- SOURCE HOLD overlap: 0
- R2/R3/R4 prior-case reuse: 0
- case ledger SHA256: `d4398a3568f55258fb664f782f5542431795ab471f944a5df168c5501478a364`
- freeze seal SHA256: `190c6f29c37cc2a1f69b415ac8cbbc45e7bb1755772ba2b3c8fe31d30a11b1db`

Local creation order preserved:
R5 preregistration -> preexecution seal -> case ledger -> case freeze seal -> Control precheck -> primary result -> final closure receipt.

## Control precheck
Exact R69 execution status OK: 24/24.
Eligibility required successful exact R69 execution, not zero architecture-validator issues.

## Metadata discrepancy
`R72_PRIMARY_MATERIALIZATION_PROTOCOL_R4.parent_prereg_sha256` contains stale R2 SHA `a38d9e...`.
Actual R5 preregistration SHA, selection seed, ledger parent SHA and preexecution seal use:
`fc4b76f62fe9c38a14abac42a3fda773e0c78ea6aa25b0930be20359c30e85a8`.

Classification:
`DOCUMENTATION_METADATA_HASH_FIELD_MISMATCH__NO_POST_OUTPUT_CASE_MUTATION`

The frozen protocol is not modified. The primary ledger was already frozen before outputs, so there is no evidence of post-output case substitution. This remains a documented preregistration-chain deviation.

## Scientific result
- R5 result SHA256: `a9854210bf21bcc50915cd953abaca6742b150917cc91ba2f5d117ec80292144`
- final status: CLOSED FAIL
- G9: 0/8 improvement
- all 8 HIGH exact R69 Control cases had frozen forced-compression/overload count 0
- LOW economy: 8/8 improvement
- MEDIUM noninferiority: 8/8
- critical violations: 0
- blind stage: NOT RUN

Next study must use a fresh preregistration; do not change the R72 effect target post hoc.
