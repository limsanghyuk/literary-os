# R73 — F05 High-Pressure Ceiling / Effect-Target Diagnostic

Date: 2026-09-22

Status: `PREREGISTERED__OUTPUTS_0__CONTROL_CENSUS_0__TREATMENT_OUTPUTS_0`

Frozen JSON SHA256:
`593814b54719e202056463cb16b7b2ad0c7ef0fecf3efe0cecbbc5b7f3bb90bb`

## Core diagnostic
R72 G9 assumed high pressure should expose forced-compression/overload headroom. R72 fresh primary data instead had 0/8 old-G9 headroom while showing economy/repetition headroom. R73 tests that mismatch on fresh cases without changing R72.

## Stage A — Control-only census
Use every fresh DB64 HIGH-tertile case after exclusions. Exact R69 only; Treatment calls = 0.

- A1: old-G9 headroom prevalence <=25%
- A2: economy/fragmentation headroom prevalence >=50%
- A3: >=24 economy-headroom cases across >=12 works

Only A3 permits Stage B.

## Stage B — unchanged F05 allocator
Deterministically freeze 24 fresh HIGH economy-headroom cases before any Treatment output.

- Economy improvement >=18/24
- Economy non-worsening >=23/24
- Old-G9 non-regression 24/24
- Required-atom and visible-carrier coverage 100%
- Critical violations 0

Raw scene count is descriptive only; fewer scenes are not automatically better.

## Claim boundary
Planning/allocation diagnostic only. R73 cannot retroactively pass R72, qualify Production F05, restore Level-3, or establish screenplay-surface quality.
