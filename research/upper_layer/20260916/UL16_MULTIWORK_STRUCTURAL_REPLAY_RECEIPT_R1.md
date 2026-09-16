# UL-16 Multi-work Cutoff-Safe Structural Replay Receipt R1

Date: 2026-09-16
Status: `NON_AUTHORITATIVE__SUPERSEDED_RUNTIME_INPUT__PRESERVED_FOR_AUDIT_ONLY`

## Correction
This replay was executed against UL-16 research runtime **R1** SHA256 `c1dfda09c97771f56aa88adc402c8fe05a03c0fd2b93205b83dafdc8d2101441`.

Before any CURRENT pointer was advanced, the Hub exact-path authority check showed that current research execution had already moved to UL-16 **R2**:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`
SHA256 `7f71484cd2687262d18104b3a9a5cfe727d003d7ed4b616ce8d64702b2da2ca8`.

Therefore the R1 replay cannot qualify the current Candidate and must not be used as current research evidence.

The R1 run is retained only to document the detection path. Its structural outputs happened to pass the frozen gates, but that does not override the superseded-input boundary.

R1 historical hashes:
- prereg object: `1ff5e1bc476fe9582da3043879707d8df9e71197f79229bd7b50996c83e3820f`
- fixture object: `d491edf3a22299b9d8704aab1aa57928ff0eec96147478417c34638d0357d404`
- result object: `d5bab230faf54922f567137475b567bc7706dee5205bb43fd21b167e429f02e4`

No physical, Production, DB or Formal authority changed.

Current authoritative replay receipt:
`research/upper_layer/20260916/UL16_R2_MULTIWORK_STRUCTURAL_REPLAY_RECEIPT_R1.md`

Status token:
`UL16_MULTIWORK_R1__NON_AUTHORITATIVE_SUPERSEDED_INPUT__POINTER_NEVER_ADVANCED__R2_RERUN_REQUIRED_AND_PERFORMED`