# R64 Fresh Primary Input Seal R1

Date: 2026-09-20
Status: `FRESH_PRIMARY_INPUTS_SEALED__TREATMENT_NOT_YET_RUN`

R64 Treatment source was frozen first.

Treatment source SHA256:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

Implementation freeze commit:
`b4392dd5ca3f3a413295f355f95f7a688ed75f1b`

Fresh primary case count:
`12`

Fresh primary JSON SHA256:
`4528cc1af5c3fbbc71c5b301749df47dadd3544ff862886593e3e8c028a9b3f7`

Control-only input QA SHA256:
`203517fb6626e8baafc087e6cbdaf70058f104a54e3ccd997b3c06c900613ed0`

Input seal ZIP SHA256:
`dc1ce1e9465a0383758ef018e016f67f91c4667319955dceb7584cd65c975987`

## Control-only QA before Treatment
Exact R58 Control:
- 12/12 architecture validation PASS;
- each case 4 due + 1 deferred;
- due recoverable PASS;
- due resolved exactly once PASS;
- deferred preserved PASS;
- blocked preserved PASS.

No R64 Treatment output was generated or inspected before this seal.

## Freshness
The 12 synthetic domains are distinct from the R62/R63 primary story material.
R62/R63 failures remain regression-only.

After this seal:
- fresh input bytes are immutable;
- R64 Treatment source is immutable;
- any source or input change invalidates the primary experiment and requires a new revision.

Status token:
`R64_FRESH_PRIMARY_SEALED__4528CC1A__CONTROL_QA_12_OF_12__TREATMENT_NOT_RUN`
