# R73 Stage B — Metric Comparability Audit R1

Date: 2026-09-22

Status:
`FAIL_COMPARABILITY__STAGE_B_EFFICACY_INVALIDATED`

Preregistration SHA256:
`593814b54719e202056463cb16b7b2ad0c7ef0fecf3efe0cecbbc5b7f3bb90bb`

Stage-A result SHA256:
`b060ecd8e86cd29746085b8b7fc968b5e2a5f6ddf9f23c9f25bcc8d2ed3465b7`

Stage-B raw result SHA256:
`35c268423ffa209b391a9b9497c2168fcb265cfb553eeb031090163a07f65395`

## Finding
Across all 41 fresh HIGH exact-R69 Controls, allocation-only economy components were zero:
- unnecessary allocation scenes: 0
- allocation duplicate count: 0
- F06 redundant/mergeable count: 0

All preregistered economy headroom came from **F04 semantic transaction repetition**:
- F04 semantic repetition groups: 125 total
- F04 headroom cases: 41/41
- allocation-only headroom cases: 0/41

In the 24 frozen Stage-B cases, all 76 Control economy violations were F04 semantic repetition groups. Treatment allocator output had no equivalent semantic-transaction representation and therefore could not be evaluated with the same F04 validator.

## Consequence
The apparent 24/24 numerical economy improvement is not admissible as a causal Treatment efficacy result because the two arms were measured with semantically non-equivalent instruments.

Preserve Stage-B execution as exploratory evidence only.

R72 remains CLOSED FAIL. F05 remains NOT QUALIFIED.

## Required next
A fresh preregistered symmetric measurement bridge must realize Control and Treatment into comparable scene-contract / semantic-transaction structures and apply the exact same F04/F06 validators to both arms.
