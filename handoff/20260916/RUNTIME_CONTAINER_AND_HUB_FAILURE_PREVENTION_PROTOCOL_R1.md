# RUNTIME / CONTAINER / HUB FAILURE PREVENTION PROTOCOL R1

Date: 2026-09-16
Project: Literary OS Development
Classification: MANDATORY RECOVERY / PACKAGING / HUB SAFETY ADDENDUM

## 1. PURPOSE

This protocol separates infrastructure/runtime faults from package corruption, custody failure, packaging failure, and scientific/experimental failure. A tool or transport error must never be promoted into a scientific FAIL without independent evidence.

Current physical root remains `SYNC-R53`; this document does not change Production, Candidate, DB, Formal, or physical authority.

## 2. FAILURE DOMAINS — NEVER COLLAPSE THEM

1. `RUNTIME_TRANSPORT`: `TransportTimeoutError`, `ClientError`, tool gateway/session backend failure, DNS/network connector failure.
2. `MEMORY_IO_PRESSURE`: cgroup memory pressure, page-cache growth from repeated large ZIP/BIN scans, inode/disk/file-descriptor exhaustion.
3. `PACKAGING_INTEGRITY`: ZIP CRC failure, duplicate paths, unsafe traversal paths, symlink/encryption surprises, C2 reconstruction mismatch, manifest/hash mismatch.
4. `CUSTODY_DELIVERY`: local file exists but conversation attachment/download surface is missing; durable archive missing; user-visible 9/9 not established.
5. `HUB_CONCURRENCY`: GitHub update attempted with stale blob SHA, producing a 409 conflict.
6. `HUB_DISCOVERY`: code-search/index returns zero even though the exact path exists in repository contents.
7. `AUDIT_SCRIPT`: expected grep/search no-match treated as shell failure, directory filter mistake, shell arithmetic/pipeline error.
8. `COMPUTE_TIMEOUT`: redundant full-corpus recomputation or oversized in-memory transform exceeding execution budget.
9. `SCIENTIFIC_FAILURE`: only a preregistered experimental gate or evaluation result may create a scientific FAIL.

## 3. MANDATORY PREFLIGHT BEFORE LARGE FILE WORK

Run in this order:

1. minimal process execution (`/bin/true`, Python/version);
2. `/mnt/data` and `/tmp` create/write/read/stat/delete;
3. disk + inode availability;
4. cgroup `memory.max`, `memory.current`, `memory.peak`, `memory.events`;
5. small archive/member read;
6. exact authority/pointer path reads;
7. only then large-package SHA/CRC/reconstruction;
8. only after physical health passes may research generation or experimental execution begin.

If even minimal process execution fails, stop at `RUNTIME_INFRASTRUCTURE_HOLD`. Do not attempt to diagnose package corruption from the failed runtime.

## 4. MEMORY / PAGE-CACHE RULES

Observed in this session:

- cgroup `memory.max = 4 GiB`;
- no OOM / OOM-kill events observed;
- large sequential ZIP reads materially increase file page cache;
- after advising scanned archives `POSIX_FADV_DONTNEED`, `memory.current` fell from about 1.81 GiB to about 1.14 GiB without any OOM/max event.

Required operating rules:

- hash/CRC large archives sequentially, not concurrently;
- do not repeatedly hash invariant large files; cache verified hashes within the audit run;
- avoid full extraction when targeted member reads or ZIP central-directory inspection are sufficient;
- use streaming I/O rather than reading large ZIP/BIN payloads into Python memory;
- after one-pass large sequential scans, use `posix_fadvise(..., POSIX_FADV_DONTNEED)` when available;
- use `/tmp` for large temporary/reconstruction bytes; keep `/mnt/data` for mounted inputs and final evidence/deliverables;
- before a new large operation, HOLD if OOM/OOM-kill has incremented, memory.events `max` is incrementing, or available headroom is unsafe;
- never treat page-cache growth by itself as package corruption.

## 5. ZIP / BINARY SAFETY CHECK

For every transport package before modification:

- outer SHA256;
- ZIP CRC / binary integrity;
- duplicate member names = 0;
- unsafe absolute/`..` traversal paths = 0;
- symlink surprises = 0 unless explicitly expected;
- encrypted entries = 0 unless explicitly expected;
- expected authority overlay/member set present;
- only then inspect or append overlays.

Do not recursively unpack all nested archives merely to prove integrity when streaming/member-level verification is sufficient.

## 6. CURRENT SESSION R53 DIRECT CHECKPOINT

Directly reverified in the healthy 2026-09-16 runtime:

- CONTROL SHA256 `f879b9dfde6e55c88dbac0070f5fb3f4e35482e49bdef33b724eed813f084c69` — ZIP CRC PASS.
- A SHA256 `11e3298aa62706a1e30abc41af4d13b13048aa86523a40a4b0f6b6f84ac98314` — ZIP CRC PASS.
- B1 SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98` — ZIP CRC PASS.
- B2 SHA256 `12b6e6dd18c224d5bc98dd6714c6a24e3be7b5531d3546db09f7915c5476b3a0` — ZIP CRC PASS.
- All four: duplicate=0, unsafe path=0, symlink=0, encrypted=0.
- `research_sync_r53` overlay in CONTROL/A/B2: 8/8 files same path set and byte-identical.
- 32 MiB `/tmp` write -> fsync -> atomic rename -> read/hash probe: PASS.
- repeated random-offset reads of current B2: stable.
- current disk headroom at audit: about 29 GiB; inode use about 1%.
- cgroup audit after probes: `memory.events max=0`, `oom=0`, `oom_kill=0`.

This is a `4/9 DIRECTLY REVERIFIED` checkpoint, not a new 9/9 physical authority declaration.

## 7. GITHUB CONTENTS / POINTER UPDATE RULE

For every existing Hub text-file update:

1. read the exact repository contents path directly;
2. capture the latest returned blob SHA;
3. update exactly once with that SHA;
4. do not run writes to the same path in parallel;
5. on `409 Conflict`, fetch the exact path again and reconcile before retrying;
6. never reuse an old SHA from a previous turn/session.

For a new file, first direct-read its exact path and require 404/not-found before create.

## 8. SEARCH INDEX IS NOT EXISTENCE AUTHORITY

Current-session reproduction:

- GitHub code search returned zero results for `CURRENT_DEVELOPER_HUB_AUTHORITY`;
- direct repository contents listing showed the file and its current blob SHA.

Therefore:

- `search 0 results != file absent`;
- existence, current contents, and update preconditions must use exact-path repository contents reads;
- code search may be used only for discovery, never as the final authority for file existence or freshness.

## 9. LOCAL FILE != DELIVERED FILE

A container path, successful local ZIP build, or SHA receipt does not prove developer custody.

A future SYNC may be declared developer-delivery-complete only after the existing 12-step physical-custody gate, including:

- conversation/file-surface attachment 9/9;
- user-visible download 9/9;
- durable archive locator;
- Hub Physical Package Manifest;
- download/re-hash verification where the archive surface permits it.

R54/R55/R56 remain historical local attempts; do not reuse them as physical authority.

## 10. SHELL / AUDIT SCRIPT RULES

- expected `grep`/search no-match must be handled explicitly and must not be confused with command failure under `set -e`;
- distinguish `0 records found` from `tool execution failed`;
- prefer small independently checkable Python audit steps over long fragile shell pipelines for package inventories and comparisons;
- record scope next to every regression count so numbers from different candidate trees/suites are not treated as contradictory;
- after any audit-script error, rerun only the affected audit stage and confirm source bytes were not modified.

## 11. RECOVERY AFTER ANY INFRA ERROR

On Transport/Client/DNS/tool timeout:

1. do not modify authority;
2. do not increment formal/scored count;
3. do not mark the experiment FAIL;
4. preserve the last sealed checkpoint/hash receipt;
5. retry only minimal runtime health in a fresh call/session;
6. resume from the last sealed physical/scientific boundary;
7. if custody evidence was incomplete, classify it as `CUSTODY_HOLD` even if local build tests passed.

## 12. CURRENT AUTHORITY BOUNDARY

Unchanged:

- Physical baseline: `SYNC-R53`.
- Production: `ENG:R47`.
- Candidate Base: `P07-I4H Recovery R3`.
- DB Authority: `DB59 frozen`.
- Formal scored total: `137`; latest Formal `R138`; R140 `0/0/0`.
- Operational Level-3: `SUSPENDED`.
- Level 4: `NOT STARTED`.
- External UL-13 responses: `0`.
- Live OpenAI qualification outputs: `0`.

## 13. STATUS TOKEN

`RUNTIME_HUB_SAFETY_R1__FAILURE_DOMAINS_SEPARATED__DIRECT_PATH_SHA_UPDATES_ONLY__SEARCH_NOT_EXISTENCE_AUTHORITY__STREAMING_LARGE_IO__PAGE_CACHE_MANAGED__4_OF_9_R53_REVERIFIED__NO_AUTHORITY_CHANGE`
