# R74 Primary Exclusion Custody Audit R1

Date: 2026-09-22

Status:
`HOLD__R72_R2_R3_R4_R5_CASE_ID_CUSTODY_INCOMPLETE__NO_PRIMARY_FREEZE`

## Canonical R74 requirement
The SHA-sealed R74 preregistration requires fully fresh primary efficacy cases and therefore excludes:
- all R71 primary works;
- all R72 R2/R3/R4/R5 primary cases;
- all 41 R73 Stage-A HIGH cases;
- all R73 Stage-B Treatment cases;
- SOURCE HOLD works.

R73 Stage-B cases are a subset of the 41 Stage-A cases, so the exact 41-case R73 exclusion manifest is sufficient for the R73 boundary.

## R72 revision facts

### R2
Status:
`EXECUTION_HOLD__CONTROL_INPUT_ADAPTER_PATTERN_COLLAPSE__NO_SCIENTIFIC_PASS_FAIL`

Facts:
- 24 primary cases were selected;
- Treatment outputs existed;
- exact R69 Control failed on 5/24 before valid paired completion;
- R2 cases may not be reused in R3 or later R74;
- R2 hold receipt SHA256:
  `fbef970e8cbc564c20e7a3a737356bee9db2700ea411d70b2e1848f6c82a03c9`
- exact 24 case IDs: **not durably recovered in current custody**.

### R3
Status:
`CONTROL_PRECHECK_HOLD__THREAD_STATE_SOURCE_REQUIRED__R3_TREATMENT_OUTPUTS_0`

Facts:
- fresh 24-case ledger was selected;
- Control-only precheck passed 22/24;
- Treatment outputs = 0;
- R3 cases are excluded from R4/R5/R74;
- R3 control-precheck hold receipt SHA256:
  `2a4030835d4f91818c64f5727a7b1f46f3be59a0990cc5409612ef3e631f1618`
- exact 24 case IDs: **not durably recovered in current custody**.

### R4
Status:
`CONTROL_PRECHECK_HOLD__R69_PORTFOLIO_INPUT_VALIDITY_REQUIRED__R4_TREATMENT_OUTPUTS_0`

Facts:
- wholly fresh 24-case ledger was selected;
- Control-only precheck passed 20/24;
- Treatment outputs = 0;
- R4 cases are excluded from R5/R74;
- R4 hold receipt SHA256:
  `9b8f13ed5ebe1ea613115e68131bd69c5498cb3d53760b596b9d94207fbf97ee`
- exact 24 case IDs: **not durably recovered in current custody**.

### R5
Status:
scientific primary completed, R72 CLOSED FAIL.

Facts:
- fresh 24 cases;
- 16 distinct works;
- LOW/MEDIUM/HIGH = 8/8/8;
- R2/R3/R4 prior-case reuse = 0;
- frozen ledger SHA256:
  `d4398a3568f55258fb664f782f5542431795ab471f944a5df168c5501478a364`
- freeze seal SHA256:
  `190c6f29c37cc2a1f69b415ac8cbbc45e7bb1755772ba2b3c8fe31d30a11b1db`
- exact 24 case IDs: **not durably recovered in current custody**.

## Recovery attempts completed
- current GitHub main tree searched: no R72 primary ledger files;
- exact protocol SHA references searched: no materialization protocol bytes found;
- R72 preregistration commits inspected: only prereg documents were committed;
- conversation file catalog around the R72 execution window inspected: no raw R2/R3/R4/R5 ledger files present;
- Project/Library search by R5 ledger SHA and R72 ledger terms: no original ledger bytes recovered;
- current local container/Python/Jupyter runtime is unavailable due TransportTimeoutError, preventing inspection of physical C2 research evidence where these ledgers may still exist.

## Scientific consequence
Do NOT:
- guess R72 case IDs;
- exclude only known works as a substitute;
- weaken the canonical R74 freshness rule;
- freeze R74 primary cases before R72 exclusion custody is complete.

Qualified R74 freeze harness intentionally fails closed until this custody is repaired.

## Recovery path
When local physical access is restored:
1. verify current SYNC-R72 / historical C2 research evidence hashes;
2. inspect physical C2 for R72 R2/R3/R4/R5 primary ledgers / materialization protocols;
3. verify recovered R5 ledger bytes against SHA256 `d4398a...`;
4. verify R2/R3/R4 receipts/protocol hashes;
5. build one complete R72 exclusion-custody manifest with exact case IDs;
6. only then run the qualified R74 primary freeze harness.

This is a custody HOLD, not an R74 scientific FAIL.
