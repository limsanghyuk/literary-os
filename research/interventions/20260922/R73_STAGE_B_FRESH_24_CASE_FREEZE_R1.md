# R73 Stage B — Fresh 24-Case Freeze R1

Date: 2026-09-22

Status:
`FROZEN_BEFORE_ANY_R73_TREATMENT_OUTPUT`

Preregistration SHA256:
`593814b54719e202056463cb16b7b2ad0c7ef0fecf3efe0cecbbc5b7f3bb90bb`

Stage-A result SHA256:
`b060ecd8e86cd29746085b8b7fc968b5e2a5f6ddf9f23c9f25bcc8d2ed3465b7`

Stage-B selection IDs SHA256:
`c451ed441ac35ac0c861cd785e02f4d043c6c91d09e4f250fef6623d7c84db77`

Full 24-case ledger SHA256:
`1ad52097d9e35a487aa0eb2f84b3f9a0a0670dd1c538c3b30b0ee29e292bc014`

Freeze seal SHA256:
`fab0f77f60735a09cf2927d90c47d0a627a41eb3214abcc99868dbfe3ba255d3`

## Frozen sample
- 24 fresh HIGH-pressure cases
- 18 distinct works
- max 2 cases/work
- R72 R2/R3/R4/R5 primary overlap: 0
- R71 primary-work overlap: 0
- all 24 exact-R69 Controls have economy/fragmentation headroom >=1
- all 24 old-G9 forced-compression/overload headroom = 0
- Treatment outputs at freeze: **0**

## Selection rule
Eligible cases were selected only from the sealed Stage-A Control census using the frozen rule:
`SHA256(preregistration_sha256|work|episode_no)`, max 2 cases/work, first 24, >=12 works.

The Treatment allocator, thresholds, and sample may not be changed after this freeze.
