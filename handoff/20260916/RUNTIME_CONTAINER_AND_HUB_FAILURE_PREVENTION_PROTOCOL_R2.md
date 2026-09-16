# RUNTIME / CONTAINER / HUB FAILURE PREVENTION PROTOCOL R2

Date: 2026-09-16
Project: Literary OS Development
Classification: MANDATORY RECOVERY / PACKAGING / HUB SAFETY ADDENDUM
Supersedes for future execution: `RUNTIME_CONTAINER_AND_HUB_FAILURE_PREVENTION_PROTOCOL_R1.md`

## 1. Core rule
Infrastructure/runtime failure, package corruption, custody failure, audit-script failure, compute timeout, and scientific failure are separate domains. Never convert one domain into another without direct evidence.

Current authority remains unchanged:
- Physical baseline: `SYNC-R53`
- Production: `ENG:R47`
- Candidate Base: `P07-I4H Recovery R3`
- DB Authority: `DB59 frozen`

## 2. Failure domains

1. `RUNTIME_TRANSPORT`: TransportTimeoutError, ClientError, tool/backend/DNS/connector failure.
2. `MEMORY_IO_PRESSURE`: cgroup pressure, page-cache accumulation, disk/inode/file-descriptor exhaustion.
3. `PACKAGING_INTEGRITY`: CRC/hash/manifest/chunk/reconstruction/path/symlink/encryption failure.
4. `CUSTODY_DELIVERY`: local file exists but user-visible attachment/download or durable archive is not proven.
5. `CONTAINER_DURABILITY`: ephemeral overlay or volatile-fsync semantics; local fsync/hash does not prove durable external storage.
6. `HUB_CONCURRENCY`: stale blob SHA / 409 conflict.
7. `HUB_DISCOVERY`: code-search/index miss despite exact-path file existence.
8. `AUDIT_SCRIPT`: missing utility, grep/no-match, pipeline, shell arithmetic, filter or dependency error.
9. `COMPUTE_TIMEOUT`: redundant full scans, oversized in-memory transforms, execution-budget exhaustion.
10. `SCIENTIFIC_FAILURE`: only preregistered experiment/evaluation evidence may create scientific FAIL.

## 3. Mandatory preflight before large work

Run in order:
1. minimal process execution;
2. `/mnt/data` and `/tmp` create/write/read/stat/delete;
3. disk and inode headroom;
4. cgroup `memory.max/current/peak/events/high`;
5. file-descriptor/process/file-size limits;
6. filesystem/mount check for `/mnt/data`, `/tmp`, `/dev/shm`;
7. exact GitHub authority/pointer path reads;
8. small archive/member read;
9. only then large SHA/CRC/reconstruction;
10. only after physical health passes may research generation/experiment execution begin.

If minimal execution fails, enter `RUNTIME_INFRASTRUCTURE_HOLD`. Do not infer package corruption or scientific failure.

## 4. Current runtime characteristics and required handling

Observed directly in the 2026-09-16 recovery runtime:
- cgroup hard memory limit: 4 GiB;
- `memory.high = max`;
- peak during full C/D-layer audit: about 2.18 GiB;
- no `memory.events max`, OOM, or OOM-kill events;
- after page-cache advice/cleanup, `memory.current` returned to about 1.0 GiB;
- `/mnt/data` and `/tmp` are the same overlay filesystem/device;
- overlay mount reports `fsync=volatile`;
- `/dev/shm` is tmpfs;
- open-files soft limit: 16384;
- file-size limit: unlimited;
- disk free at final audit: about 28 GiB;
- inode use: about 1%.

Operating rules:
- stream large files; never load multi-hundred-MiB archives wholly into memory;
- hash/CRC sequentially, not concurrently;
- cache already verified hashes within one audit run;
- use `/tmp` for temporary reconstruction so mounted source inputs are not mutated, but do not assume separate disk capacity;
- calculate expected temporary output size plus safety headroom before reconstruction;
- avoid `/dev/shm` for large reconstruction unless deliberately memory-budgeted;
- after large sequential scans, use `POSIX_FADV_DONTNEED` when available;
- delete temporary reconstructions after receipts are sealed;
- successful container-local fsync/hash is only local verification, not durable-archive proof because the mount is ephemeral/volatile.

## 5. ZIP / split-binary safety gate

For each transport:
- outer SHA256;
- CRC/binary integrity;
- duplicate members = 0;
- unsafe absolute/`..` paths = 0;
- unexpected symlinks = 0;
- encrypted entries = 0 unless explicitly expected;
- expected overlay/member set present;
- manifest-listed members re-hashed by size+SHA.

For split binary transports:
1. hash each split independently;
2. reconstruct sequentially;
3. verify size/file type;
4. verify reconstructed SHA and CRC;
5. verify manifests/chunks;
6. remove temporary reconstruction after receipt.

## 6. SYNC-R53 direct recovery checkpoint — 9/9 PASS

Fresh direct verification is complete for:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`.

Transport SHA256:
- CONTROL `f879b9dfde6e55c88dbac0070f5fb3f4e35482e49bdef33b724eed813f084c69`
- A `11e3298aa62706a1e30abc41af4d13b13048aa86523a40a4b0f6b6f84ac98314`
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 `12b6e6dd18c224d5bc98dd6714c6a24e3be7b5531d3546db09f7915c5476b3a0`
- C1 `b2a06fa2add7f66d31d7ebf32a5264be9431e38b56f098b4241a2858e7da8cf4`
- C2-A `aeb14bd4523466445411c8d6c00e38557e4847fce944eb314506ebb19dbc653f`
- C2-B `ee85bab92b3c6ae52ca338ad0f4d5c04582c7fac2491d62e57ccac219b07af2d`
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

C-layer:
- C2 reconstructed size `319254266`, SHA256 `e51da441f932f4bf445ddb09b62cdb0caf940a209a9649d8518075b6f25bffb9`, CRC PASS.
- C1/C2 Candidate runtime overlay identity PASS at SHA256 `d8c622cef4b3b853814efe896208494b7fb2bd6b2399dd6296adde8e498931ef`.
- Narrative Engine Master reconstruction PASS at canonical SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`.

D-layer:
- D1/D2 outer CRC/safety PASS.
- D1 manifest required package + part001 size/SHA PASS.
- D2 manifest required package + part002 size/SHA PASS.
- D1/D2 DB59 corrected authority pointer byte-identical at SHA256 `1e46e1e5cad89841913f2c9881c5aa36e478226ab8e184884c4026d158f4ba2c`.
- DB59 reconstruction size `259756521`, SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`, canonical match PASS, ZIP CRC PASS, 38852 entries, duplicate/unsafe/symlink/encrypted `0/0/0/0`.

Canonical receipt:
`handoff/20260916/R53_DIRECT_9_OF_9_RECOVERY_VERIFICATION_RECEIPT_R1.md`

This is a recovery verification receipt only. It does NOT create a new SYNC authority and does NOT prove durable Hub archive custody.

## 7. GitHub update rule

For every existing Hub file:
1. fetch exact repository contents path;
2. capture current blob SHA;
3. update exactly once using that SHA;
4. never run same-path writes in parallel;
5. on 409, re-fetch exact path and reconcile;
6. never reuse stale SHA from an earlier turn/session.

For new files, exact-path fetch must first return not-found before create.

Code-search/index results are discovery aids only. `0 results != file absent`.

## 8. Audit-script portability

- do not assume optional utilities such as `xxd` exist;
- prefer Python stdlib or POSIX tools such as `od`;
- distinguish expected no-match from command execution failure;
- rerun only the affected audit stage after an audit-script error;
- confirm source bytes were not modified before resuming.

The current session reproduced missing `xxd` as status 127; package SHA work already completed remained valid, and the byte-display step was rerun portably.

## 9. Local file is not durable custody

A local path, successful CRC, canonical reconstruction, or local fsync does not prove future recoverability.

A future SYNC successor is `DEVELOPER_DELIVERY_COMPLETE` only after all 12 custody gates independently pass on that successor, including:
- conversation/file-surface attachment 9/9;
- user-visible download 9/9;
- Hub Physical Package Manifest;
- durable external archive locator;
- archive download/re-hash verification.

R54/R55/R56 remain historical local candidate physicalization attempts and are not physical authority.

## 10. Authority boundary

Unchanged:
- Physical baseline `SYNC-R53`
- Production `ENG:R47`
- Candidate Base `P07-I4H Recovery R3`
- DB `DB59 frozen`
- Formal total `137`, latest `R138`, R140 `0/0/0`
- Operational Level-3 `SUSPENDED`
- Level 4 `NOT_STARTED`
- External UL-13 responses `0`
- Live OpenAI qualification outputs `0`

## Status token

`RUNTIME_HUB_SAFETY_R2__R53_DIRECT_9_OF_9_PASS__ENGINE_MASTER_CANONICAL_PASS__DB59_CANONICAL_PASS__VOLATILE_CONTAINER_NOT_DURABLE_ARCHIVE__DIRECT_PATH_SHA_UPDATES_ONLY__NO_AUTHORITY_CHANGE`
