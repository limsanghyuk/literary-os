# R74 Primary Symmetric F05 Result R1

Date: 2026-09-23

Status:
`FAIL__F05_NOT_QUALIFIED`

Primary result JSON SHA256:
`a6d1d83c2218ae7154584e18acf83eeaa6dfe16e36fb37d958708d1dbed4b0a2`

Final freeze ledger SHA256:
`53d17ec565418a8a3a7bb9333b4ad7de4ec0125a52c6200b3a31329cee1ee23c`

Final input bundle SHA256:
`d3a3b6b56b926203fc7bfdb5fb444f42b786bac126f3bc0e3d8fd950ad71a81e`

Sample:
- 24 fully-fresh paired cases
- 17 distinct works
- max 2 cases/work
- paired execution 24/24

## Gates
- P1 paired execution: PASS 24/24
- P2 bridge completeness: PASS 24/24 both arms / unresolved 0
- P3 F04 improvement: FAIL 0/24, required >=16
- P4 F04 non-worsening: FAIL 11/24, required >=22
- P5 F06 improvement: CEILING / NOT SCORED; Control headroom 0/24
- P6 F06 non-worsening: FAIL 12/24, required 24/24
- P7 due-now contribution coverage: PASS 518/518
- P8 visible-causal contribution coverage: PASS 518/518
- P9 premature deferred closure: PASS 0
- P10 F01/F02/F07 regressions: PASS 0/0/0
- P11 confirmed critical violations: PASS 0

Directional result:
- F04 improved 0 / equal 11 / worsened 13
- F06 improved 0 / equal 12 / worsened 12

F06 diagnosis:
- 125 Treatment redundant/mergeable scenes had no unique protected contribution.
- all 125 were deferred-only scenes whose open pressure was already preserved by the terminal deferred ledger.

Scientific interpretation:
The unchanged F05 allocator preserves coverage and state-safety, but does not improve symmetric F04 repetition and creates semantically unnecessary physical scenes under symmetric F06. It therefore does not qualify.
