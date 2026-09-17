# R7 Small-Source Research Lane

Date: 2026-09-17
Status: `MANDATORY_FOR_POST_R57_RESEARCH`

## Problem this closes
Repeated session interruptions were not a single engine defect. They were caused by the combination of:
1. repeated reads/reconstruction of 100MB-300MB package transports inside a 4GiB cgroup, producing page-cache pressure and tool transport instability;
2. brittle audit-shell assumptions (`head`/SIGPIPE, `printf` option parsing, out-of-range source line reads, optional utilities);
3. mixing research, large physical packaging, archive upload, and pointer updates in one long turn;
4. re-opening sealed package bytes when a small verified runtime source/fixture/receipt would have been sufficient.

Historical evidence: `memory.events max` rose from 117 to 1574 and later 7045 during large-package work, with OOM/OOM-kill still 0. This is memory/page-cache pressure, not evidence of package corruption.

## Mandatory lane
For research after a physical SYNC has been SHA-synchronized:
- extract/use only the smallest verified runtime source and hash-bound fixtures needed for the experiment;
- do not repeatedly reconstruct C2, Engine Master, DB59, or all nine packages during ordinary research;
- package physically only after a research repair has a closed receipt and a deliberate physicalization decision;
- use Python stdlib for bounded source inspection and archive verification; avoid shell pipelines that can generate SIGPIPE or line-range false failures;
- classify script/transport errors separately from scientific failure;
- checkpoint every bounded research unit as `prereg -> result -> receipt -> pointer`, before starting another unit;
- if `memory.current` is high, reclaim page cache / delete large temporaries before any further archive read;
- never alter the current sealed physical authority in place. Research works in a copy and remains research-only until a new SYNC successor is built and fully audited.

## Current application
R58/R58B/R58C were executed only in a small working runtime derived from SHA-verified physical SYNC-R57. No R57 transport was modified.

## Status token
`R7__SMALL_SOURCE_RESEARCH_LANE__NO_REPEATED_LARGE_PACKAGE_SCANS__BOUNDED_PYTHON_AUDIT__RESEARCH_AND_PHYSICALIZATION_SEPARATED`
