# SYNC-R59 B2 Transport Correction R2

Date: 2026-09-19
Status: `CORRECTED__DOWNLOADABLE_TRANSPORT__LOGICAL_CONTENT_UNCHANGED`

## Cause
The original SYNC-R59 Part B2 transport was:
- bytes: `268532511`
- SHA256: `9d9c878cc3c794740b8b0fe4c6a13f6c5fa46c6a1e6b33e7f3631679dfdee0bf`

The ChatGPT attachment boundary is 256 MiB:
`268435456` bytes.

The original B2 exceeded that boundary by:
`97055` bytes.

Therefore the package existed locally and passed ZIP/CRC audit, but could not be attached reliably to the user download surface.

## Correction
Transport-only lossless ZIP recompression was performed.

Corrected B2:
- filename: `LITERARY_OS_CURRENT_PART_B2_P07_I4H_RECOVERY_R3_UPPER_LAYER_SYNC_R59_20260919.zip`
- bytes: `268276811`
- SHA256: `753db03b5c161d3c016ef95388f93e2dfe2c469d2e1eb6182429b3d16cd549e6`
- margin below 256 MiB: `158645` bytes

## Logical equivalence
Compared original vs corrected B2:
- entries: 1805 -> 1805
- member names: identical
- member uncompressed sizes: identical
- member CRC values: identical
- corrected ZIP full CRC: PASS
- duplicate names: 0

Therefore:
`B2_LOGICAL_CONTENT_CHANGE = NONE`
`ENGINE_RUNTIME_CHANGE = NONE`
`RESEARCH_RESULT_CHANGE = NONE`
`OTHER_8_PACKAGES_CHANGE = NONE`

Only the B2 transport bytes/SHA changed.

## Corrected authority
For the current SYNC-R59 delivery set, use:
`B2_SHA256 = 753db03b5c161d3c016ef95388f93e2dfe2c469d2e1eb6182429b3d16cd549e6`

Do not use the pre-correction B2 transport SHA for developer delivery.

Status token:
`SYNC_R59_B2_TRANSPORT_R2__ATTACHMENT_LIMIT_ROOT_CAUSE_FOUND__LOSSLESS_REPACK__LOGICAL_EQUIVALENCE_PASS__DOWNLOADABLE_SIZE__OTHER_PACKAGES_UNCHANGED`
