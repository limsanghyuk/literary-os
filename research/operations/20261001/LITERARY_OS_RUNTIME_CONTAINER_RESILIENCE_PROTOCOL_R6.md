# Literary OS Runtime / Container Resilience Protocol R6

Date: 2026-10-01
Scope: operational recovery only
Authority effect: NONE
Scientific-result effect: NONE

R6 supersedes R5 for future runtime/container/file-transfer recovery procedure. R5 remains immutable historical protocol evidence.

## 1. Core rule

Infrastructure uncertainty is never scientific evidence.

ClientError, TransportTimeoutError, GeneratedFileUploadError, mount-readiness failure, raw-byte materialization denial, or truncated upload does **not** establish experiment FAIL, engine FAIL, package corruption, DB failure, or authority change unless the same failure is independently reproduced at the engine/data layer with valid authoritative bytes.

On minimal-command failure:
`STOP -> RUNTIME_TRANSPORT_HOLD -> MINIMAL_HEALTH_CHECK -> LAST_ATOMIC_CHECKPOINT_VERIFY -> RESUME_ONLY_FAILED_STEP`

During HOLD:
- no mutation;
- no reseal;
- no promotion;
- no new scoring/generation;
- no attempt-count increment solely for tool failure.

## 2. Strengthened mandatory diagnostic order

R6 adds one crucial rule learned from the 2026-10-01 B1/B2 audit: **never begin by opening multiple archives in one grouped loop.**

For each artifact, independently:

1. Minimal local health
   - /bin/true
   - minimal Python import
   - exact supplied path exists
2. Exact grounded path + stat
3. Compare exact expected byte size **before ZipFile open**
4. If size mismatches:
   - classify transfer/retention truncation;
   - STOP that artifact;
   - do not waste I/O on canonical SHA/CRC claims;
   - do not let its BadZip contaminate judgment of other files.
5. Only for size-matched artifact:
   - streaming SHA256
6. ZIP central directory
   - entries
   - duplicate paths
   - encrypted entries
   - unsafe paths
7. CRC/testzip
8. Required/nested member checks
9. Only then extraction, rejoin, mutation, reseal, or physicalization.

A grouped `BadZipFile` only proves that at least one grouped input cannot be opened. It does not identify the failing artifact and does not prove container death.

## 3. Current concrete incident — SYNC-R74 B1/B2

B1 uploaded copy:
- expected bytes: 196,427,036
- actual bytes: 42,958,848
- shortfall: 153,468,188
- only ~21.87% of expected bytes present
- PK local-file header exists
- end-of-central-directory absent
- ZipFile open fails
- classification:
  `PHYSICAL_UPLOAD_TRUNCATION__NOT_RESEARCH_OR_ENGINE_FAILURE`

This uploaded B1 copy is **not authority** and must not be repaired by invention or used for reseal.

B2 uploaded copy:
- bytes: 296,011,084
- SHA256: `5462a1c9d355f01a41ce9a52302fce28241d2af1ef5065fdb6fec08c5d107dd0`
- entries: 1,893
- duplicate/encrypted/unsafe: 0/0/0
- Python CRC/testzip: PASS
- exact SYNC-R74 manifest match: PASS

Therefore one truncated sibling upload does not imply corruption of the healthy B2.

## 4. Upload / retention truncation

Visible presence is not byte custody.

After every large transfer/retention:
1. expected size;
2. SHA256;
3. central directory;
4. CRC;
5. required member check.

If size mismatches:
- `PHYSICAL_UPLOAD_TRUNCATION__NOT_RESEARCH_OR_ENGINE_FAILURE`
- do not fabricate missing bytes;
- do not promote/reseal;
- recover another independently authoritative exact copy;
- verify before use.

Historical D1 and current B1 show the same failure class at different truncation points.

## 5. ClientError / path-specific gateway failures

A healthy local shell proves only local health, not tool-gateway health.

If one execution surface fails and another succeeds:
- localize to that path/tool;
- keep artifacts immutable;
- switch only to a healthy grounded path;
- reduce to one artifact / one step;
- resume from prior verified checkpoint.

Never infer OOM without `memory.events` evidence.

## 6. 4 GiB cgroup / page-cache safety

- one large archive at a time;
- streaming reads;
- no parallel extraction/recompression;
- /tmp for intermediates;
- POSIX_FADV_DONTNEED after large immutable reads when available;
- inspect memory.current/max/events;
- `oom=0, oom_kill=0` means do not label OOM.

2026-10-01 current audit:
- memory.max = 4,294,967,296
- memory.current after B2 CRC ≈ 1.25 GiB
- oom = 0
- oom_kill = 0

## 7. Split/rejoined authorities

C2 and DB59-style split carriers must be validated layer-by-layer:
outer carrier -> split member -> logical rejoin -> nested required package.

Never flatten multi-overlay C2 topology or assume a single-root archive.
Rejoin only in /tmp and verify exact logical size/SHA/CRC.

## 8. Generated-file and raw-materialization boundaries

GeneratedFileUploadError after proven local completion is a delivery failure, not recomputation mandate.

Raw-byte materialization denial is an authorization/access boundary, not corruption.
Metadata visibility is not executable byte custody.

## 9. Mount readiness

Use only runtime-supplied grounded sandbox paths.
If first access fails, recheck exact directory/path before declaring missing.
Never invent alternate paths from filenames.

## 10. Archive warnings

Legacy CLI Unicode/path warnings alone do not establish corruption.
Use exact SHA + Python central directory + testzip + duplicate/encrypted/unsafe checks.

## 11. Authority precedence

Current external physical Manifest / Trust Root / READ FIRST / Hub CURRENT pointers outrank nested historical CURRENT_* files.

A byte-healthy historical packet can still be procedurally stale.

Current B2 example:
the embedded R77-H1 six isolated launch packets are preserved provenance and must not be rerun as current experiment inputs merely because their bytes are intact.

## 12. Same-name/different-hash collision

Never overwrite or silently choose.
Preserve both, quarantine ambiguity, and create a uniquely named verified successor only after full parent/hash audit.

## 13. Custody loss

Never reconstruct hidden mappings, frozen inputs, or donor packets from memory.
HOLD/abort affected experiment and preserve evidence.

## 14. Atomic checkpoint discipline

For heavy work:
1. output to /tmp;
2. close/fsync;
3. size;
4. SHA256;
5. central directory;
6. CRC;
7. semantic/mechanical validator;
8. move only final audited artifact to durable/user-visible storage;
9. re-read/re-hash delivered authority copy.

Resume from the last completed numbered checkpoint after any infrastructure failure.

## 15. Physical authority effect

None.

Current Physical Authority remains **SYNC-R74**.
This protocol changes recovery procedure only; it does not mutate Candidate runtime, C1/C2, DB59, Production, formal count, or scientific verdicts.
