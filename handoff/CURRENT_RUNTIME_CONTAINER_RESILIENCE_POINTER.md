# CURRENT RUNTIME / CONTAINER RESILIENCE POINTER
Last updated: 2026-10-06

Canonical Protocol(정본 프로토콜):
`research/operations/20261001/LITERARY_OS_RUNTIME_CONTAINER_RESILIENCE_PROTOCOL_R6.md`

Mandatory rule:
`STOP -> RUNTIME_TRANSPORT_HOLD -> MINIMAL_HEALTH_CHECK -> LAST_ATOMIC_CHECKPOINT_VERIFY -> RESUME_ONLY_FAILED_STEP`

Current recovery:
`handoff/20261006/START_HERE_NEW_SESSION_MASTER_RECOVERY_R26.md`

Current Physical Authority: **SYNC-R77**
Research Treatment: **UL22AB_INTEGRATED_RESEARCH_SUCCESSOR_RUNTIME_R1**

## Latest runtime incident / 최신 런타임 사고
At UL23 first execution:
- candidate runtime preflight -> ClientError
- minimal shell -> ClientError
- minimal Python -> ClientError
- trivial shell remained ClientError

Classification:
`CAAS_EXECUTION_SURFACE_FAILURE__RUNTIME_TRANSPORT_HOLD__NOT_ENGINE_OR_SCIENTIFIC_FAILURE`

## New-session prevention / 새 세션 예방
Before any large artifact:
1. minimal shell PASS;
2. minimal Python PASS;
3. /mnt/data read/write PASS;
4. /tmp read/write PASS;
5. materialize one artifact only;
6. size -> streaming SHA -> ZIP directory -> CRC;
7. continue sequentially.

Never:
- parallel-unzip multiple large packages
- rejoin C2/DB in memory
- use /dev/shm for large rebuild
- declare missing after a single mount-readiness miss
- print giant recursive trees/registries
- interpret output truncation or GeneratedFileUploadError as engine failure

If ClientError recurs on minimal health:
STOP and remain in RUNTIME_TRANSPORT_HOLD. Use another fresh execution surface; optional remote execution is allowed only after exact candidate byte verification.
