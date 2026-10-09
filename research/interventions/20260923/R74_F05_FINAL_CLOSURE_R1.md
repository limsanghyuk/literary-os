# R74 — F05 Symmetric Semantic-Transaction Measurement Bridge — Final Closure R1

Date: 2026-09-23

Final status:
`CLOSED_FAIL__R4_SYMMETRIC_MEASUREMENT_VALID__F05_NOT_QUALIFIED`

Closure artifact SHA256:
`9e8b30d0afa8b470ea05d76caf7f8223435670a03fbce79d07094f66f53bc035`

Recovery/closure evidence bundle SHA256:
`63f87dbfcc7586bfd1d57851bfb2deb1bcd4191e9682647cbb55d225e132217a`

## Final scientific result
R4 repaired the R73/R74 measurement comparability problem and passed independent qualification, but the unchanged F05 Adaptive Pressure Allocator failed efficacy gates.

- P3 FAIL: F04 improvement 0/24
- P4 FAIL: F04 non-worsening 11/24
- P5 CEILING: Control F06 headroom 0/24, efficacy not scored
- P6 FAIL: F06 non-worsening 12/24
- P7-P11 PASS

Therefore:
`F05_NOT_QUALIFIED`

R72 remains FAIL.
R73 remains diagnostic-only.
R74 closes FAIL as an efficacy experiment.
R4 remains a qualified measurement repair.

## Authority consequences
Unchanged:
- Physical Authority: SYNC-R72
- Active Runtime: exact R69
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- DB64 adopted: false
- Operational Level-3: SUSPENDED / REQUALIFICATION REQUIRED
- Formal R140: NOT STARTED

Research Overlay advances to:
`R74_CLOSED_FAIL__F05_NOT_QUALIFIED__R4_MEASUREMENT_QUALIFIED`

## Next research
Do not continue a chain of F05 micro-repairs.

Next priority:
`DB64-R128 Causal Schema Consumption Qualification`

For the subsequent broadcast-scale integrated experiment, keep F05 disabled/unqualified and use the safe current distribution behavior.
