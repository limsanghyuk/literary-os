# R74 Primary Input Custody Hold R1

Date: 2026-09-22

Status:
`PRIMARY_INPUT_CUSTODY_PRESENT__CONTENT_ACCESS_BLOCKED__PRIMARY_OUTPUTS_0`

## What is NOT wrong
This is not:
- DB64 corruption;
- DB64 loss;
- an R74 scientific failure;
- an F05 efficacy result.

The original conversation custody still contains the DB64 R127 split uploads:
- part01: 141,779,367 bytes; expected SHA256 `b033ebf5c00c844634a8180812382d68657d59fd98643d45e8470314ca5994e3`
- part02: 141,779,367 bytes; expected SHA256 `a618f48503afb5b5465f49264259302e4e3c90434ede6ea4c99be700cd4f1785`
- expected logical DB64: 283,558,734 bytes; SHA256 `4703e9a99da2deb66eef08f09b08141db6c4d19bc76f77d1c8159dcb7633d6e7`

## Root cause
The current ChatGPT execution runtime layer repeatedly returns `TransportTimeoutError` even for minimal commands across:
- container execution;
- private Python;
- visible Jupyter.

GitHub Actions successfully bypasses that runtime for repository-resident data, proving the research code path itself is executable.

However the DB64 split uploads are conversation-file custody, not repository-resident files. The available Files materialization route depends on the unavailable local execution runtime, and the raw split files are also >100 MiB each.

## Source-equivalence audit
GitHub contains broad `seqcard_ko` episode artifacts, but no `consumer_ready_r53`, DB64 R127 planner_input/thread_state corpus, or provenance document proving those repository artifacts are byte/provenance-equivalent substitutes for the frozen DB64 R127 consumer-ready source.

Therefore they are NOT substituted for DB64 in R74.

## Freshness boundary
The 17 R73 Stage-A Control-only / Treatment-naive cases remain bridge/metrology reserve only. They do not satisfy the R74 fully-fresh primary efficacy claim.

No R74 primary case has been frozen.
No R74 primary Control output has been generated.
No R74 primary Treatment output has been generated.

## Resume
When DB64 content access is restored:
1. verify part01/part02 SHA256;
2. reconstruct and verify logical DB64 SHA256;
3. enumerate cases under all frozen R74 exclusions;
4. deterministically select exactly 24 fully fresh episodes, >=12 works, max 2/work;
5. seal the full input ledger before any Treatment output;
6. execute exact R69 Control vs unchanged F05 Treatment;
7. score BOTH arms only through qualified R74 R3 bridge;
8. apply preregistered P1-P11 gates.

Do not weaken freshness or replace DB64 with an unverified mirror to bypass infrastructure.
