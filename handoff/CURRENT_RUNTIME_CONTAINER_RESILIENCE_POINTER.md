# CURRENT RUNTIME / CONTAINER RESILIENCE POINTER
Last updated: 2026-10-01

## CANONICAL PROTOCOL
`research/operations/20261001/LITERARY_OS_RUNTIME_CONTAINER_RESILIENCE_PROTOCOL_R6.md`

## CURRENT INCIDENT AUDITS
`research/operations/20261001/RUNTIME_CONTAINER_RESILIENCE_SYNC_R74_B1_B2_CURRENT_ATTACHMENT_AUDIT_R2.json`

`research/operations/20261001/RUNTIME_CONTAINER_RESILIENCE_SYNC_R74_C1_C2_CURRENT_ATTACHMENT_AUDIT_R2.json`

## NON-NEGOTIABLE RULE
`STOP -> RUNTIME_TRANSPORT_HOLD -> MINIMAL_HEALTH_CHECK -> LAST_ATOMIC_CHECKPOINT_VERIFY -> RESUME_ONLY_FAILED_STEP`

## DIAGNOSTIC ORDER
For each artifact independently:
1. exact grounded path + stat;
2. expected size comparison;
3. only if size matches, streaming SHA256;
4. ZIP central directory;
5. CRC/testzip;
6. required nested members;
7. only then extraction/rejoin/mutation/reseal.

Never begin with grouped multi-archive open/extraction.
A truncated sibling upload does not contaminate the verdict of a healthy artifact.

## AUTHORITY EFFECT
NONE. Physical Authority remains SYNC-R74.
