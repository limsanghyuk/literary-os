# UL-16 Operational Error Root Cause & Fix R1

Date: 2026-09-16
Status: CLOSED__OPERATIONAL_CAUSES_CLASSIFIED__NO_PACKAGE_CORRUPTION

## Incident 1 — repeated GitHub `Not Found`
Cause: exact-path existence checks for NEW Hub files returned HTTP 404 before creation. The files were subsequently created successfully. The 404 was expected pre-create state, but the workflow exposed it as if it were a task failure.

Fix:
- classify `PRECREATE_EXACT_PATH_404` as expected when the next operation is create;
- seal create commit in the same stage;
- use directory/current-path reads for existing files;
- never infer Hub corruption from an expected pre-create 404.

UL-14, UL-15 and UL-16 documents were verified by their create commits and exact filenames.

## Incident 2 — shell status 141
Cause: `pipefail + head` caused upstream grep/unzip to receive SIGPIPE after the requested preview lines were produced.
Classification: `AUDIT_SCRIPT`, not runtime/package failure.
Fix: use Python or non-short-circuit listing for structural audits; do not combine `pipefail` with truncating consumers when the upstream exit code is used as integrity evidence.

## Incident 3 — optional utility status 127
Cause: `xxd` was not installed.
Classification: `AUDIT_SCRIPT`.
Fix: use Python stdlib or POSIX `od`; never assume optional shell utilities.

## Incident 4 — cgroup memory pressure
Observed current-session cumulative values after extended 1GB+ ZIP/DB work:
- `memory.max = 4 GiB`;
- `memory.peak = 4 GiB`;
- `memory.events max = 117`;
- `oom = 0`;
- `oom_kill = 0`.

Interpretation: the process/session hit the cgroup hard limit/reclaim boundary repeatedly but was not OOM-killed. This may contribute to latency/tool transport instability. It is not package corruption.

Fix already reflected in Safety Protocol R3:
- record memory-event baseline before each large-I/O phase;
- judge deltas, not lifetime absolute counters;
- a positive `max` delta during a new large phase enters `MEMORY_IO_PRESSURE_HOLD`;
- hash/CRC/reconstruction sequentially;
- avoid repeatedly reopening the 1GB+ physical root when small hash-bound derived artifacts suffice;
- release page cache when possible and use small working copies for engineering iterations.

## Incident 5 — future-source guard raised uncaught exception
Cause: Canonical IR correctly rejected a forbidden future reference, but `run_candidate_canonical_planning` did not catch the compiler `ValueError`.
Impact: safety detection worked, but the public planning API crashed instead of returning a controlled HOLD.

Fix in UL-16 research working copy:
- wrap canonical compilation in fail-closed exception handling;
- return `HOLD / CANONICAL_IR_COMPILE_FAIL` with compile error receipt;
- regression injects a forbidden future marker and requires controlled HOLD.
Result: PASS.

## Incident 6 — wrong assumed integration surface
Cause: the R53 Candidate upper overlay contains validators/gates, but the actual legacy Episode/Sequence/Scene generator is inside `LITERARY_OS_RUNTIME_SOURCE_CURRENT.zip`.
Impact: modifying only the overlay would not repair the actual Main Path.

Fix:
- integrate UL-16 at `literary_os_runtime/canonical_authoring.py` routing and a new adaptive showrunner module in the actual runtime source working copy;
- preserve default `LEGACY_R53` path unchanged;
- route only Candidate research mode through `ADAPTIVE_UL16`.

## Current decision
`OPERATIONAL_INCIDENTS_CLOSED_FOR_CURRENT_STAGE`.

No evidence of R53 or DB64 byte corruption was found. Physical/Production authority remains unchanged.

Status token:
`UL16_OPS__EXPECTED_PRECREATE_404_SEPARATED__PIPE_SIGPIPE_AND_MISSING_UTILITY_CLASSIFIED_AUDIT_SCRIPT__CGROUP_LIMIT_PRESSURE_MANAGED__CANONICAL_EXCEPTION_FAIL_CLOSED__ACTUAL_RUNTIME_INTEGRATION_SURFACE_CORRECTED`
