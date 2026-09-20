# R63 Fresh Primary Case Seal R1

Date: 2026-09-20
Status: `FRESH_PRIMARY_CASES_SEALED__TREATMENT_NOT_YET_RUN`

Treatment source was frozen first:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

Fresh case count:
`12`

Canonical uncompressed JSON SHA256:
`5c7f04816c00a2f5afc42a8c2862f5e888000a2fbefde28f9c73f03c1cdb3376`

Canonical JSON bytes:
`34139`

Deterministic gzip (mtime=0) SHA256:
`8b4d9fda5e44fb3cb9fd4afdcdbfaa5221c02058c3afab3f7b8dce19ea7c6b88`

GitHub custody file:
`research/interventions/20260920/R63_FRESH_PRIMARY_CASES_R1.json.gz.b64`

Reconstruction:
1. base64-decode the file;
2. gunzip it;
3. verify the uncompressed JSON SHA256 above.

Input QA before seal:
- exact R58 Control architecture validation: 12/12 PASS;
- each case has 4 due obligations and 1 deferred obligation;
- no Treatment output was generated or inspected before this seal.

The 12 cases use new synthetic domains and do not reuse the R62 C06/C08/C11 story material.

After this seal, case content is immutable for the R63 primary paired experiment.
