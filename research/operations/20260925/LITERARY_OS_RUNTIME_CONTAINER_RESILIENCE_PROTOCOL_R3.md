# Literary OS Runtime / Container Resilience Protocol R3

Date: 2026-09-25
Scope: operational recovery only
Authority effect: NONE
Scientific-result effect: NONE

## 1. Core classification rule

A CAAS/container/file-service failure is not an experiment FAIL, engine FAIL, package corruption, or authority change unless the same failure is independently reproduced at the engine/data layer with valid bytes.

When minimal commands fail, classify:
`RUNTIME_TRANSPORT_HOLD`

While this hold is active:
- stop mutation, reseal, promotion, scoring, and new output generation;
- do not increment scientific attempt counts solely because a tool gateway failed;
- preserve the last verified atomic checkpoint;
- resume only the interrupted step after health recovers.

## 2. Mandatory diagnostic order

Use this exact escalation order and stop as soon as the failure boundary is localized.

1. Minimal shell:
   - `/bin/true`
   - `printf/echo`
   - `pwd`
2. Filesystem:
   - list the exact mounted directory
   - read exact supplied sandbox path
   - `/tmp` write/read/delete
3. Minimal Python:
   - one-line subprocess
   - import `hashlib/json/zipfile`
4. File identity:
   - path
   - size
   - SHA256
5. ZIP central directory only:
   - entry count
   - duplicate paths
   - encrypted entries
   - unsafe paths
6. CRC/testzip
7. Only then extraction, rejoin, mutation, or reseal.

Do not start with whole-tree recursive scans or multi-archive extraction.

## 3. Path-specific tool failure

If one execution surface fails but another succeeds, classify the failure to that tool/transport path rather than to the artifact.

Example observed 2026-09-25:
- private Python tool: `ClientError` while opening B1+B2 metadata together;
- immediately afterward container shell + container Python subprocess + /mnt/data + /tmp were healthy;
- per-archive central-directory inspection succeeded.

Response:
- keep the artifact immutable;
- switch to the healthy execution path;
- reduce the call to one artifact / one step;
- verify the prior size/SHA checkpoint before continuing.

## 4. Upload / retention truncation

A visible file object is not authoritative until exact bytes are verified.

After every large transfer or session-to-session retention:
1. expected size;
2. SHA256;
3. ZIP central directory;
4. CRC;
5. required member check.

If size/SHA differs or ZIP is truncated:
- classify `PHYSICAL_UPLOAD_TRUNCATION__NOT_RESEARCH_OR_ENGINE_FAILURE`;
- do not fabricate missing bytes;
- do not promote/reseal;
- recover an exact parent/canonical copy and verify it before resuming.

Historical examples:
- D1 truncated upload: expected 138,011,573 bytes but mounted 132,644,864 bytes;
- SYNC-R60..R63 retained B2 copies later found truncated; rebuilt only from last byte-verified parent.

## 5. Raw-byte materialization authorization boundary

`This Project file does not have an authorized raw-byte materialization path`
means access/materialization failure, not data corruption.

Rules:
- server-side visibility/copy is not equivalent to executable raw custody;
- do not mutate or reseal from metadata-only custody;
- use another independently authoritative byte source only if size/SHA/CRC can be proven;
- otherwise remain on the prior physical authority.

## 6. Large archive / 4 GiB cgroup safety

Avoid simultaneous large extraction/rejoin/recompression.

Preferred:
- one large archive at a time;
- central-directory inspection before payload reads;
- streaming I/O;
- `/tmp` for intermediate/rejoined files;
- move only final audited deliverables to `/mnt/data`;
- hash a large immutable archive once per audit and cache the result;
- after large read, call `POSIX_FADV_DONTNEED` when available;
- inspect `memory.current`, `memory.max`, and `memory.events`;
- distinguish page-cache pressure from OOM. `oom=0/oom_kill=0` means do not call it an OOM failure.

## 7. GeneratedFileUploadError

If filesystem work completes but generated-file upload fails:
- preserve the completed local checkpoint;
- classify delivery/upload boundary separately;
- keep large intermediates in `/tmp`;
- place only final audited artifacts or small receipts/manifests in `/mnt/data`.

Do not repeat expensive computation merely because attachment registration failed.

## 8. ZIP filename / Unicode warnings

Command-line `unzip` may emit legacy local/central filename warnings for non-ASCII names.

Do not classify archive corruption from that warning alone.

Use:
- exact archive SHA256;
- Python `zipfile` central directory;
- Python `testzip()`;
- duplicate/encrypted/unsafe-path checks.

If those pass, Unicode CLI warnings are transport/tooling warnings, not corruption evidence.

## 9. Mount readiness / exact-path rule

An attachment reference or visible Library object is not proof that the executable path is ready.

Rules:
- use the exact grounded sandbox path supplied by the runtime;
- if the first existence/read check fails, re-list the containing directory before declaring the file missing;
- do not infer alternative filenames/paths;
- distinguish mount-readiness race from missing bytes.

## 10. Timeout after scientific output

If a wrapper timeout occurs after:
- stdout/result is complete,
- the planned output SHA is verified,
- mechanical validation passed,
then classify as tool-wrapper timeout with no scientific effect.

If completion cannot be proven, preserve the attempt as incomplete/hold; do not infer a PASS.

## 11. Custody loss after remount

If secret mapping, donor packet, primary ledger, or frozen input custody is lost:
- do not reconstruct from memory/style/approximation;
- do not guess hidden mapping;
- abort or HOLD the affected experiment;
- preserve the immutable failure/hold record;
- start a fresh successor only under a new preregistration when allowed.

## 12. Atomic checkpoint discipline

For every heavy step, write/checkpoint in this order:
1. output to `/tmp`;
2. close/fsync where applicable;
3. size;
4. SHA256;
5. ZIP central directory;
6. CRC;
7. semantic/mechanical validator;
8. only after all PASS, copy final artifact to durable/user-visible storage;
9. re-read/re-hash the delivered copy when it will become authority.

On any transport failure, resume from the last completed numbered checkpoint rather than restarting the entire experiment.

## 13. B1 / B2 direct verification on 2026-09-25

Directly supplied:
- B1 `LITERARY_OS_CURRENT_PART_B1_SYNC_R72_INHERITED_BYTE_UNCHANGED_FROM_SYNC_R71(6).zip`
  - bytes: 196,427,036
  - SHA256: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
  - entries: 56
  - duplicate/encrypted/unsafe: 0/0/0
  - Python CRC/testzip: PASS
  - exact SYNC-R72 manifest match: PASS
- B2 `LITERARY_OS_CURRENT_PART_B2_P07_POST_R73_DIAGNOSTIC_SYNC_R72_20260922(7).zip`
  - bytes: 268,681,858
  - SHA256: `0807ef0a820a2836349724097481d88301768114ca1ac291a9ef294aa7766ba5`
  - entries: 1,874
  - duplicate/encrypted/unsafe: 0/0/0
  - Python CRC/testzip: PASS
  - exact SYNC-R72 manifest match: PASS

Current cgroup observation during verification:
- memory.max: 4,294,967,296
- initial memory.current observed: ~3.06 GiB
- oom: 0
- oom_kill: 0
- after sequential CRC + DONTNEED: memory.current fell to ~2.58 GiB

Conclusion:
The attached B1/B2 are healthy canonical SYNC-R72 bytes. The reproduced error was an execution-path transport ClientError, not archive corruption.



## 15. R3 additions from C1 / C2 direct audit

### 15.1 Local health does not prove tool-gateway health

Historical C2 evidence `09_CONTAINER_CLIENTERROR_OPERATIONAL_SAFETY_R1.json` classifies recurring ClientError as:
`INTERMITTENT_TOOL_GATEWAY_OR_SESSION_BACKEND_FAILURE__LOCAL_RESOURCE_EXHAUSTION_NOT_SUPPORTED__ROOT_CAUSE_NOT_OBSERVABLE`

Observed facts:
- identical minimal calls later succeeded without engine or package repair;
- disk, inode, open-file and memory exhaustion were not supported by the evidence;
- CAAS orchestration logs, tool-gateway routing logs and backend session-handle state are not visible from inside the container.

Therefore a healthy shell/Python/filesystem snapshot proves only local execution health. It must not be overinterpreted as proof that every tool gateway is healthy.

### 15.2 Authority precedence prevents historical-bootstrap confusion

C1/C2 contain preserved historical bootstrap documents that describe an older 5-logical-part / 8-transport layout.
The current SYNC-R72 snapshot explicitly requires:
`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

Operational rule:
1. CURRENT pointer / latest physical snapshot manifest;
2. latest snapshot READ FIRST;
3. current Trust Root / SHA256SUMS;
4. embedded historical authority documents.

Older embedded bootstrap documents remain provenance/history only and must never override the latest physical snapshot manifest.

### 15.3 Same-name/different-hash authority collision rule

C1 preserves the SYNC-R71 repair note showing that two SYNC-R70 objects with the same authority-style name but different hashes existed.
Do not overwrite, merge, or silently choose between same-name/different-hash objects.

Required response:
- preserve both as historical objects;
- create a fresh uniquely identified successor reseal;
- seal exact parent relationships and hashes;
- update CURRENT pointers only after the successor passes full byte verification.

### 15.4 Preflight completeness before expensive execution

I4H recovery evidence shows a development HOLD caused by validation happening inside the render loop instead of validating profile completeness before any render attempt.

Operational lesson:
- perform deterministic completeness/precondition scans before provider calls, rendering, large generation, or irreversible primary-output creation;
- fail closed before expensive execution;
- preserve the original HOLD and preregister any corrective patch before rerun.

This reduces both scientific ambiguity and repeated container load after a preventable late failure.

### 15.5 Materialization protocol progression is immutable evidence

R72 materialization protocols R1-R4 show a safe evolution pattern:
- freeze exact source and parent preregistration before outputs;
- repair only the declared boundary;
- add eligibility/preflight gates before treatment output;
- do not replace cases after treatment output has been viewed;
- preserve every superseded protocol rather than editing it in place.

Container recovery must respect the same rule: resume from the sealed checkpoint, never rewrite the historical input/protocol record to fit a recovered run.

## 16. C1 / C2 direct verification on 2026-09-25

Directly supplied C1:
- bytes: 140,395,336
- SHA256: `1175f40e8156580f34dad3f4dd3477d4051cc11511582b2f9320d646265d8ecd`
- entries: 91
- duplicate/encrypted/unsafe: 0/0/0
- Python CRC/testzip: PASS
- exact SYNC-R72 manifest match: PASS

Directly supplied C2 split:
- C2-A bytes: 264,039,861
- C2-A SHA256: `a0485cecad46d4437277dc4845a5fd133d686a10ec7707b8dd1b1f6899c77959`
- C2-B bytes: 264,039,860
- C2-B SHA256: `5d73f5d59eda5bce30c7ba6cb1990cdfeb91cec0f00490ed8a58c6b2e154d53d`

Rejoined only in `/tmp`:
- logical bytes: 528,079,721
- logical SHA256: `87b79628a5ffd35b13849009146cf2b8429288befd9d7523a39f7c77af2252a8`
- entries: 4,001
- duplicate/encrypted/unsafe: 0/0/0
- Python CRC/testzip: PASS
- exact SYNC-R72 logical C2 manifest match: PASS
- temporary rejoined file deleted after audit: PASS

Resource evidence:
- memory.max: 4,294,967,296
- start memory.current: ~3.27 GiB
- final memory.current: ~2.58 GiB
- oom: 0
- oom_kill: 0
- mitigation: sequential streaming reads + POSIX_FADV_DONTNEED + temporary C2 only in /tmp

Conclusion:
C1/C2 are healthy canonical SYNC-R72 bytes. No package corruption or engine failure is established.

## 17. Non-negotiable resume rule

When any minimal command fails:
`STOP -> RUNTIME_TRANSPORT_HOLD -> MINIMAL_HEALTH_CHECK -> LAST_ATOMIC_CHECKPOINT_VERIFY -> RESUME_ONLY_FAILED_STEP`

Never convert infrastructure uncertainty into scientific evidence.
