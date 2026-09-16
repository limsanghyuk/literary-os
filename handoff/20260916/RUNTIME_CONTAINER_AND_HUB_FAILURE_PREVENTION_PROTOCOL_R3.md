# RUNTIME / CONTAINER / HUB FAILURE PREVENTION PROTOCOL R3

Date: 2026-09-16
Project: Literary OS Development
Classification: **MANDATORY LARGE-I/O SAFETY PROTOCOL**
Supersedes for future execution: `RUNTIME_CONTAINER_AND_HUB_FAILURE_PREVENTION_PROTOCOL_R2.md`

## 1. Why R3 exists

The extended DB64 reconstruction / analysis / Library-copy session produced a new container signal that R2 did not model correctly:

- cgroup `memory.max = 4294967296` bytes (4 GiB);
- `memory.peak` reached exactly `4294967296` bytes;
- `memory.events max` increased to `117`;
- `oom = 0`, `oom_kill = 0`.

This means the runtime encountered hard-limit reclaim/pressure events without an OOM kill. The packages remained readable and no corruption evidence was found, but continuing multiple large operations in the same cache-heavy phase would increase Transport/Client/runtime-failure risk.

Therefore **`memory.events max == 0` is no longer a valid universal precondition** because this counter persists for the life of the cgroup. Future safety decisions use a **baseline-and-delta rule**.

No authority changes follow from this runtime observation.

## 2. Failure-domain rule remains mandatory

Keep separate:
1. `RUNTIME_TRANSPORT`
2. `MEMORY_IO_PRESSURE`
3. `PACKAGING_INTEGRITY`
4. `CUSTODY_DELIVERY`
5. `CONTAINER_DURABILITY`
6. `HUB_CONCURRENCY`
7. `HUB_DISCOVERY`
8. `AUDIT_SCRIPT`
9. `COMPUTE_TIMEOUT`
10. `SCIENTIFIC_FAILURE`

A memory-pressure event is not package corruption and is not a scientific FAIL.

## 3. Mandatory preflight — baseline, not absolute zero

Before every large ZIP/BIN reconstruction, full CRC scan, bulk copy/upload, or corpus-wide extraction, record:
- `memory.current`
- `memory.peak`
- `memory.events:{max,oom,oom_kill}`
- free disk/inodes
- `/tmp` size
- open-file/process limits.

Call this snapshot `IO_BASELINE`.

After each large phase, record the same counters and calculate deltas.

### Hard HOLD conditions
Enter `MEMORY_IO_PRESSURE_HOLD` if any of these occurs:
- `oom` delta > 0;
- `oom_kill` delta > 0;
- `memory.events max` delta > 0 during the current large phase;
- free-space headroom falls below the pre-budgeted reconstruction margin;
- temporary duplicate payloads remain unexpectedly;
- `memory.current` does not materially recover after cleanup/page-cache advice and the next operation is large.

A HOLD means stop additional large work, not fail the package/experiment.

## 4. Required recovery after pressure delta

On `memory.events max` delta > 0 with no OOM:
1. seal already completed hashes/receipts;
2. do not repeat completed full scans;
3. delete completed temporary reconstructions and duplicate work files;
4. `sync` local dirty pages where appropriate, while remembering container fsync is not durable archive proof;
5. apply `POSIX_FADV_DONTNEED` to large sequentially scanned source files when available;
6. re-read `memory.current`, `memory.events`, disk and `/tmp` size;
7. perform only lightweight metadata/Hub work in the same runtime;
8. prefer a fresh runtime/session before another multi-hundred-MiB reconstruction or corpus-wide pass.

## 5. Phase separation rule

Do not combine all of these in one uninterrupted high-I/O phase:
- full split reconstruction;
- full ZIP CRC scan;
- nested package extraction;
- corpus-wide analysis;
- persistent Library copy of many large files;
- second full re-hash of already verified files.

Use phase boundaries:

`PRECHECK -> ONE LARGE READ/RECONSTRUCTION -> RECEIPT -> CACHE/TEMP CLEANUP -> HEALTH DELTA CHECK -> NEXT PHASE`

If a hash has already been sealed and source bytes have not changed, reuse the receipt within the same audit lineage instead of rescanning merely for reassurance.

## 6. Temp-space and duplicate-file rule

`/mnt/data` and `/tmp` share the same overlay capacity in this runtime.

Before large reconstruction:
- compute expected output size;
- reserve explicit free-space headroom;
- name every temporary reconstruction in a run ledger;
- remove it immediately after its receipt is sealed;
- at phase end, audit `/tmp` for unexpected files larger than 16 MiB.

Multiple DB64 reconstructions were found simultaneously during the extended session. They were removed. This did not affect source bytes but unnecessarily amplified file cache/disk pressure.

## 7. Current post-cleanup observation

After removing duplicate DB64/Master temporary files and advising large mounted inputs out of page cache:
- `/tmp` reduced to about 3 MiB;
- `memory.current` reduced to about 1.63 GiB;
- `memory.peak` remains 4 GiB because the peak counter is historical;
- `memory.events max` remains 117 because the event counter is historical;
- `oom = 0`;
- `oom_kill = 0`.

Future sessions must compare **delta from the new preflight baseline**, not the absolute historical value 117.

## 8. Container durability rule remains unchanged

The overlay reports `fsync=volatile` and `/mnt/data` + `/tmp` share the same ephemeral overlay.

Therefore:
- local CRC/SHA/fsync = local integrity evidence;
- it does not prove durable external archive custody;
- final durable archive requires a stable external locator plus re-download/re-hash when the storage surface supports it.

## 9. GitHub / Hub rule remains unchanged

Existing-file update:
`exact path fetch -> current blob SHA -> one sequential update`.

Never infer absence from code-search zero results.

Do not perform same-path writes in parallel.

## 10. Research execution implication

The repaired Showrunner work after UL-14 must avoid repeatedly opening the 1GB+ physical corpus when a smaller derived research packet is sufficient.

Use the persistent Library / sealed DB64 receipts as retrieval anchors and create small, versioned, hash-bound derived datasets for:
- obligation-census statistics;
- intervention fixtures;
- schema conformance;
- blind architecture packets.

This reduces runtime pressure without weakening provenance.

## 11. Authority boundary

Unchanged:
- Physical baseline: `SYNC-R53`
- Production: `ENG:R47`
- Candidate Base: `P07-I4H Recovery R3`
- DB Authority: `DB59 frozen`
- Formal total: `137`
- latest Formal: `R138`
- R140: `0/0/0`
- Operational Level-3: `SUSPENDED`
- Level 4: `NOT_STARTED`

## Status token

`RUNTIME_HUB_SAFETY_R3__MEMORY_EVENTS_BASELINE_DELTA_REQUIRED__MAX_PRESSURE_WITHOUT_OOM_OBSERVED__PHASE_SEPARATION_AND_TEMP_CLEANUP_REQUIRED__NO_AUTHORITY_CHANGE`