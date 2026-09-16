# RUNTIME / CONTAINER / HUB ATOMIC EXECUTION PROTOCOL R4

Date: 2026-09-16
Project: Literary OS Development
Classification: MANDATORY EXECUTION / RESUME SAFETY PROTOCOL
Supersedes execution orchestration portions of R3; R3 memory-baseline rules remain incorporated.

## 1. ROOT CAUSE OF RECURRING INTERRUPTIONS

The recurring problem was not one corrupted package or one failed tool. It was a systemic execution-pattern defect:

1. **Resource pressure was real but non-fatal.** The runtime cgroup is capped at 4 GiB. During earlier DB64/R53 work `memory.peak` reached the 4 GiB hard limit and `memory.events max` accumulated to 117, while OOM/OOM-kill remained 0. Repeated reconstruction, CRC, hashing, extraction and Library copies in one phase increased page-cache/reclaim pressure and raised transport/runtime-failure risk.
2. **Research work was too monolithic.** Many dependent tool operations were chained before a durable small receipt and Hub pointer were written. If the turn was interrupted, the bytes/results could exist while Hub still pointed to an earlier stage.
3. **Checkpointing was end-loaded.** Research evidence, implementation receipts and CURRENT pointers were often updated after a long sequence instead of after each closed stage. This produced an apparent state-loss or inconsistency on interruption.
4. **Expected control-flow statuses were displayed like failures.** Exact-path 404 before creating a new Hub file, SIGPIPE/status 141 from `pipefail + head`, missing optional utilities such as `xxd`, and unsupported Library raw-materialization are not equivalent to package corruption or infrastructure collapse.
5. **Large immutable evidence was reopened too often.** R53/DB64 had already sealed hashes, but repeated reassurance scans consumed memory/cache and time without adding authority evidence.
6. **Persistent Library presence was conflated with byte-level durable archive verification.** Library upload/list is useful persistent custody, but until raw re-materialization/re-hash is supported in the active Project context it must not be called independent byte-for-byte archive verification.

Therefore the recurring failure class is:

`NON_ATOMIC_LONG_WORKFLOW + LARGE_IO_PRESSURE + LATE_CHECKPOINTING + STATUS_CLASSIFICATION_AMBIGUITY`.

## 2. ATOMIC RESEARCH TRANSACTION RULE

Every substantial research/engineering stage is one transaction:

`PRECHECK -> ONE BOUNDED OPERATION -> LOCAL RECEIPT -> HUB RECEIPT -> POINTER UPDATE -> CLEANUP -> HEALTH DELTA -> NEXT TRANSACTION`

A transaction must be resumable from its Hub receipt without repeating completed large work.

### Required transaction fields
- transaction ID;
- parent authority / parent research receipt;
- exact input hashes or sealed receipt references;
- intended mutation scope;
- memory-events baseline;
- outputs and hashes;
- tests/gates;
- authority impact (`NONE` unless explicitly promoted);
- next exact action.

## 3. LARGE-I/O BUDGET

In a single transaction, perform at most one of:
- multi-hundred-MiB reconstruction;
- full ZIP CRC scan;
- corpus-wide extraction/analysis;
- bulk persistent upload/copy;
- full-package re-hash.

Do not combine them before a checkpoint.

If a sealed hash/CRC receipt already exists and source bytes are unchanged, reuse it. Do not rescan merely for reassurance.

## 4. MEMORY BASELINE / DELTA

Before a heavy transaction record:
- `memory.current`;
- `memory.events max/oom/oom_kill`;
- disk/inodes;
- `/tmp` footprint.

After it, calculate deltas.

Enter `MEMORY_IO_PRESSURE_HOLD` if the current transaction increments `max`, `oom`, or `oom_kill`, or if memory/current/temp does not recover enough for the next heavy phase.

Historical `memory.events max=117` is not itself a new failure. Only the transaction delta matters.

## 5. STATUS CLASSIFICATION

The execution ledger must classify tool outcomes before escalation:

- `EXPECTED_ABSENCE`: exact-path 404 immediately before creation of a new known path;
- `AUDIT_SCRIPT`: status 141 from `head`/SIGPIPE, missing optional utility, grep no-match under `set -e`;
- `CAPABILITY_LIMIT`: unsupported Library raw-byte materialization or unavailable connector action;
- `RUNTIME_TRANSPORT`: client/transport/gateway timeout independent of package bytes;
- `MEMORY_IO_PRESSURE`: positive cgroup pressure delta;
- `PACKAGING_INTEGRITY`: CRC/hash/manifest/reconstruction mismatch;
- `SCIENTIFIC_FAILURE`: only a preregistered experiment/gate fail.

Only `PACKAGING_INTEGRITY` or a scientific gate may invalidate the corresponding evidence. Other failures resume from the last sealed checkpoint.

## 6. HUB WRITE ORDER

For a completed research stage:
1. write the immutable evidence/receipt file first;
2. verify it exists by exact path or commit receipt;
3. fetch CURRENT pointer latest blob SHA;
4. update exactly one CURRENT pointer at a time;
5. fetch and verify the pointer after update;
6. only then begin the next stage.

Do not postpone all pointer writes until the end of a long turn.

For genuinely new paths, a pre-create 404 is `EXPECTED_ABSENCE`, not an error condition.

## 7. SMALL DERIVED EVIDENCE RULE

After a large corpus has been verified, derive small hash-bound packets for future work:
- structural priors;
- intervention fixtures;
- schema contracts;
- regression inputs;
- blind evaluation packets.

The 1GB+ corpus remains provenance authority but is not reopened for every engineering iteration.

## 8. CURRENT UL-16 APPLICATION

UL-16 work now follows this protocol:
- base runtime source hash is sealed;
- Candidate working copy is isolated from R53 physical authority;
- only two runtime files are mutated in the research branch/working package;
- Legacy/Production path is regression-locked;
- research runtime is packaged separately and stored in persistent Library;
- Hub implementation receipt and CURRENT pointer must be written before any next architecture/provider experiment.

## 9. AUTHORITY BOUNDARY

No authority change follows from R4.

Unchanged:
- Physical baseline: `SYNC-R53`;
- Production: `ENG:R47`;
- Candidate Base: `P07-I4H Recovery R3`;
- Runtime DB: `DB59 frozen`;
- DB64: research-support candidate only;
- Formal scored total: 137, latest R138, R140 0/0/0.

## STATUS TOKEN

`RUNTIME_HUB_R4__ROOT_CAUSE_NON_ATOMIC_LONG_WORKFLOW_PLUS_LARGE_IO_PRESSURE__ATOMIC_TRANSACTION_CHECKPOINTING_REQUIRED__EXPECTED_STATUS_CLASSIFICATION__SEALED_RECEIPT_BEFORE_NEXT_STAGE__NO_AUTHORITY_CHANGE`
