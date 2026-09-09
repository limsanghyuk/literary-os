# P07 FAILURE / INCIDENT RESPONSE PLAYBOOK R1

Date: 2026-09-10
Classification: DEVELOPMENT / PREFORMAL / RECOVERY OPERATIONS
Purpose: convert past failures into deterministic recovery behavior for new sessions. This document is operational guidance. It does not change any historical scientific verdict.

---

## 1. FAILURE CLASS A — EXECUTION TRANSPORT / PLATFORM FAILURE

### Symptoms
- `TransportTimeoutError` on minimal commands such as `/bin/true`, `/bin/echo`, `/usr/bin/env`
- `ClientError` before meaningful byte operations
- `GeneratedFileUploadError` after local filesystem work completes
- private Python / user-visible Python / container execution all fail before trustworthy work

### What this does NOT prove
- It does not prove package corruption.
- It does not prove engine regression.
- It does not prove a scientific FAIL.

### Historical evidence
I4H recovery directly reverified the underlying 9/9 parent packages, C2, B/C/D logical reconstructions and later 258/258 regression, ruling out package corruption as the explanation for the earlier transport symptoms.

### Immediate action
1. stop new research generation;
2. do not fabricate provider/runtime receipts;
3. retain last sealed physical/scientific authority;
4. retry only minimal probes, not large archive operations;
5. if minimal process repeatedly fails, classify `PREOUTPUT_INFRA_BLOCK`;
6. record the recurrence in Hub;
7. resume only in a healthy execution environment.

### Current incident
At I4J fresh-validation start, minimal process execution failed repeatedly. Latest exact classification:
`PREOUTPUT_INFRA_BLOCK__MINIMAL_PROCESS_3_OF_3_TRANSPORT_TIMEOUT__NO_SCIENTIFIC_FAIL__NO_FRESH_OUTPUTS`.

Reference:
`handoff/20260910/P07_I4J_RUNTIME_MINIMAL_PROBE_RECURRENCE_R2_20260910.json`

---

## 2. FAILURE CLASS B — MEMORY / PAGE-CACHE PRESSURE

### Environment observed
- cgroup hard memory limit: 4 GiB
- zero swap
- large sequential archive reads can fill page cache and hit `memory.events max`
- historical healthy recovery showed `oom=0`, `oom_kill=0`

### Risk
A large package read can make runtime unstable or slow without the package itself being corrupt.

### Safe operating rule
`STREAMING_IO__TMP_INTERMEDIATES__CACHE_RELEASE_AFTER_LARGE_READS__FINAL_ONLY_MOVE_TO_MNT_DATA__FAIL_CLOSED_ON_ANY_HASH_TEST_OR_AUDIT_MISMATCH`

### Required practice
- stream hashes/ZIP reads rather than loading giant archives into memory;
- use `/tmp` for intermediate build products when runtime is healthy;
- call `POSIX_FADV_DONTNEED`/equivalent cache-release strategy where available after large reads;
- move only final artifacts to `/mnt/data`;
- inspect cgroup memory/OOM state before and after large archive operations;
- never diagnose corruption from memory pressure alone.

---

## 3. FAILURE CLASS C — C2 MATERIALIZATION TOPOLOGY ERROR

### Historical defect
Recovery Builder R1 assumed combined C2 extracted directly into a root `literary_os_runtime/` project tree.

### Reality
C2 is a multi-overlay archive.

### Correct materialization order
1. `CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY`
2. `P07_I3_BROADCAST_SURFACE_R1/CODE`
3. `P07_I4A_PROVIDER_SHADOW_DELTA_R1`
4. `P07_I4B_SURFACE_INTERFACE_DELTA_R1`
5. `P07_I4D_SURFACE_REALIZATION_MODE_DELTA_R1`
6. `P07_I4H_RUNTIME_RECOVERY_R3_DELTA_R1`

### Rule
If reconstructed tests/files are missing or unexpectedly old, first audit overlay order before assuming archive corruption or rewriting code.

---

## 4. FAILURE CLASS D — FAIL-CLOSED ORDERING DEFECT

### Historical R2 symptom
I4H episode wiring began the first scene bridge before verifying every scene had an intervention profile.

### Why dangerous
Partial child execution can occur before an episode-level prerequisite failure is discovered, violating fail-closed whole-episode semantics.

### Corrective R3 behavior
Validate profile completeness for the whole episode before any bridge/provider call.

### Resolution evidence
- R2 preserved as HOLD 44/45
- corrective R3 preregistered before patch
- 45/45 new tests PASS
- 56/56 targeted PASS
- 258/258 full nonhistorical PASS

### General rule
Episode-level or hierarchy-level prerequisites must be preflighted at the highest required scope before any irreversible lower-level execution.

---

## 5. FAILURE CLASS E — SEMANTIC JUDGE PROMPT / VALIDATOR CONTRACT MISMATCH

### Historical symptom
Real OpenAI diagnostic reached SEQUENCE_PLAN then stopped with:
`SEMANTIC_JUDGE_INVALID:POSITIVE_JUDGMENT_CROSS_GROUP_EVIDENCE`.

### Root cause
The validator enforced same-group evidence constraints that were not explicitly communicated to the Judge prompt/payload.

### Correct solution
- attach per-obligation `obligation_group`;
- attach `allowed_evidence_ids`;
- require positive evidence list non-empty and subset of allowed IDs;
- reject unknown/cross-group IDs;
- distinguish malformed Judge packet (`JUDGE_INVALID`) from genuine negative semantic judgment (`VALID_SEMANTIC_HOLD`);
- do not fabricate `unfulfilled_count` when packet validation itself failed.

### Verified virtual behavior
- compliant case reaches SCENE_PLAN
- valid 13-positive/2-negative case remains semantic HOLD
- cross-group malformed packet remains JUDGE_INVALID HOLD
- frozen historical packet remains invalid, not rewritten PASS

### General rule
Every machine-enforced semantic constraint must be visible to the model producing the structured judgment. Hidden validator-only rules create false invalidity, not meaningful semantic quality control.

---

## 6. FAILURE CLASS F — HISTORICAL TEST BODY / CLAIM RECONSTRUCTION RISK

### Historical condition
Some old test labels/results existed while exact historical test source/body was unavailable.

### Forbidden response
Do not invent the missing test body merely to rerun an old number and obtain PASS.

### Correct response
- preserve old result as historical evidence only;
- reconstruct exact parent independently;
- preregister a new test suite against the actual parent;
- report new counts separately.

### Applied precedent
Historical 42/42 and 26/26 labels were not represented as fresh reruns in I4H Recovery R3.

---

## 7. FAILURE CLASS G — HISTORICAL / EXPECTED-FAIL TEST CONTAMINATION

### Symptom
Running an unfiltered pytest set can surface an intentionally preserved historical failure and make the current parent look broken.

### Correct response
- use authority-defined `nonhistorical` regression scope for current engine qualification;
- preserve historical failures separately;
- never delete historical failing evidence merely to make the test count green.

### Applied result
Current parent nonhistorical baseline is 258/258 PASS after I4H Recovery R3 / post-I4I work.

---

## 8. FAILURE CLASS H — PROVIDER-ANALOG HARNESS BOOKKEEPING ERROR

### Observed issue 1
A summary once reported `scene_plan_called=false` even though Sequence→Scene verdicts existed.

### Root cause
Summary projection did not correctly account for multiple Judge results/new list structure.

### Fix
Use provider/server-observed stage-call receipts as the execution truth, and treat summary projection as a derived view that must be tested.

### Observed issue 2
Provider-Analog server process did not terminate after output because a `serve_forever` daemon thread was left alive.

### Fix
Explicit:
- `shutdown()`
- `server_close()`
- `join(timeout=5)`
- assert the thread terminated

### General rule
Harness/process defects must not be promoted into engine-science conclusions. Separate transport/harness validity from model/engine verdict.

---

## 9. FAILURE CLASS I — TRANSIENT BRANCH / PROTECTED-GUARD DRIFT

### Historical incident
A rejected transient branch temporarily altered/removed an RFV2 fail-closed guard during Semantic Alignment work.

### Correct response
- reject transient branch;
- restore last-known-good treatment hash;
- rerun new tests and full regression;
- package only restored canonical state.

### General rule
Protected-scope byte identity must be rechecked after any exploratory branch. A branch is not canonical merely because tests on that branch looked useful.

---

## 10. FAILURE CLASS J — DUPLICATE / NONCANONICAL PACKAGING

### Historical incident
A duplicate Semantic Alignment candidate C2 build omitted two fixtures, producing packaged-only 21/23 despite canonical 23/23.

### Correct response
- discard duplicate build;
- never declare it candidate authority;
- rebuild canonical package with all fixtures;
- rerun 23/23 + 281/281;
- delete duplicate delivery directory where possible;
- mark any accidental Hub duplicate record as `SUPERSEDED ... DO NOT USE`.

### General rule
One passing source tree is not enough. Physical rematerialization must rerun the qualification suite from the package bytes that will actually be delivered.

---

## 11. FAILURE CLASS K — STALE METADATA / PACKAGE-COUNT DRIFT

### Historical pattern
Older package metadata can retain stale regression counts or authority labels after a new runtime closure.

### Risk
A package may contain correct engine bytes but stale documentation that points a new session to the wrong authority or test count.

### Response
- treat metadata as part of the physical closure;
- update counts/authority pointers;
- recompute hashes after metadata change;
- rebuild/reseal affected transports;
- re-audit C2 split/recombine if C2 changed;
- never call stale metadata harmless if it changes recovery semantics.

---

## 12. FAILURE CLASS L — DB64 SCHEMA GENERATION MISMATCH

### Observed data generations
`unresolved_payoffs` appear as:
- dicts with `thread_id`
- dicts with only `edge_id`
- strings

### Engine expectation
Current R3 NAP consumer expects a compatible dict/thread representation.

### Concrete effects
- 시티헌터/식객: duplicate `THREAD:None` evidence IDs
- 스카이캐슬/스타일/시그널/시크릿가든: exceptions on string rows
- 신사의품격/신의퀴즈1/신화: required EP01 ThreadState missing

### Correct response
Do not normalize silently at runtime and call the candidate adopted.

Repair path:
1. define one Consumer contract;
2. migrate/normalize candidate data with provenance/version record;
3. verify required knowledge members;
4. rerun 63-work/episode compatibility;
5. rerun A1 packet completeness;
6. rerun A2 selected mutation + irrelevant invariance;
7. only then compare DB59 vs DB64 utility.

---

## 13. FAILURE CLASS M — A2 PROVENANCE / SEMANTIC INVARIANCE LEAK

### Symptom
Changing an irrelevant unselected record changed provider-facing payload hash even though selected semantic evidence did not change.

### Root cause
Whole-snapshot provenance hash was injected into provider-facing NAP/payload.

### Important classification
The same behavior reproduced on DB59. Therefore it is an engine packet/provenance design issue, not proof DB64 is uniquely bad.

### Required future research
Separate:
- semantic content that the provider should react to;
- audit/provenance identity that can change without changing semantic provider input.

Then test:
- selected mutation -> semantic/provider input changes
- irrelevant unselected mutation -> semantic/provider input invariant
- audit provenance may still change

---

## 14. FAILURE CLASS N — BYTE COUNT VS UNICODE CHARACTER COUNT

### Historical R1 mistake
An early Control was reported as 71,988 “characters”, but that number was UTF-8 bytes. Actual Unicode characters were only 31,516.

### Why it did not contaminate the experiment
The problem was discovered before Control seal and before Selector profiling. The Control was expanded/revalidated to 35,036 Unicode characters before sealing.

### Rule
For the user's episode floor, always compute Unicode character count on decoded text. File size / UTF-8 byte count is not an acceptable substitute.

### Required pre-seal checks
- Unicode chars >= 35,000
- scene count >= 45
- sequence count >= 9
- exact scene ordering and plan membership

---

## 15. FAILURE CLASS O — SPEAKER / PARTICIPANT VALIDATION

### Historical behavior
Naive validator treated full Korean names and dialogue labels as different people, creating false positives. Separately, actual background speaker labels not present in the frozen participant list were genuine violations.

### Correct response
- canonical alias map: e.g. full-name -> approved dialogue label
- validate alias-normalized speaker against frozen participant list
- independently test presence of planned participants
- remove or convert non-plan background dialogue to stage direction when participant is not frozen
- repair only before seal; after seal a plan/speaker violation triggers HOLD/abort rather than silent rewrite

---

## 16. FAILURE CLASS P — BLIND-MAP INFORMATION LEAKAGE

### Historical R1 incident
First blind map printed A/B file hashes, making mapping inferable from known Control/Treatment hashes. A second unsalted two-state hash remained inferable from the first incident.

### Correct response used
- discard both attempts while scores were still 0
- generate a new secret salted map
- publish only map hash before scoring
- seal score hash
- only then open map

### Rule
Any information that lets the evaluator infer A/B mapping before score seal invalidates that map. Discard at zero score; never “pretend not to know”.

### Evaluation claim boundary
R1/R2 are masked same-agent Development/Preformal evidence. Same agent authored/profiled/treated and evaluated; strict independent policy blindness is not claimed.

---

## 17. FAILURE CLASS Q — R2 FROZEN PLAN MISSING FULL BRIDGE ANCHORS

### Finding
After R2 Control seal, the frozen Scene Plan was found to preserve scene_id, sequence_id, location, time, participants, scene_function, turn, exit_state, thread_ids, but not every field required by current full `SemanticSceneToRendererBridge`, including goal/obstacle/physical_action/information_change/relationship_change/subtext_requirement.

### Forbidden response
Do not infer/rewrite those fields from sealed Control after output exists just to claim a full bridge run.

### Actual response
Because the R2 preregistration did not require full bridge replay as its primary gate, a non-result-changing execution adapter amendment was sealed at Selector=0/Treatment=0/Score=0. Missing anchors were not invented. R2 proceeded with the unchanged R3 Selector/revision boundary and explicitly made no full semantic-bridge claim.

### Future prevention
I4J fresh Scene Plan must include every runtime-required semantic anchor before Control output 1.

---

## 18. FAILURE CLASS R — PRE-FREEZE PLAN VALIDATION DEFECTS

### Example pattern
A draft fresh plan may contain collective pseudo-participants, incorrect scene distribution, missing required fields, or inconsistent sequence membership.

### Correct response
Detect and repair before `COMPLETE_PLAN_FROZEN` and before Control generation.

### Rule
Plan validation belongs before literary prose. It is not result contamination to repair a plan before the plan is frozen and before Control output 1; it is contamination to change the frozen plan after observing treatment/evaluation results.

---

## 19. FAILURE CLASS S — WORKING-FILE / PERMISSION / TRANSIENT STORAGE FAILURE

### Pattern
A local working-file write or `/tmp` permission/storage incident can interrupt a draft before seal.

### Response
- do not classify as science FAIL;
- preserve durable pre-seal checkpoint in `/mnt/data` when possible;
- never treat a partial write as sealed Control;
- resume from the latest checksum-verified checkpoint;
- after seal, never regenerate the artifact from memory unless the exact sealed bytes can be recovered.

---

## 20. FAILURE CLASS T — ENDPOINT / MECHANISM MISALIGNMENT

### Evidence
I4I R1 and R2 both showed:
- positive/nonharmful scene-level intervention effects
- 12/12 whole-episode axis nonloss
- historical equal-weight 12-axis primary delta below +0.30

R1: +0.2833
R2: +0.1667

### J0 interpretation
A conservative surface intervention is designed to improve certain craft axes while keeping semantic/continuity axes nonloss. Equal-weight averaging can dilute the target-axis signal.

### Critical rule
This insight does NOT retroactively change R1/R2 FAIL.

### Current prospective research
I4J tests a candidate future endpoint:
- target-axis mean delta >= +0.30
- protection/mixed axes treated as separate hard gates
- coverage ladder ARM_0 / ARM_50 / ARM_100

Endpoint adoption requires fresh prospective validation and later replication/governance; one favorable J1 run is insufficient.

---

## 21. NEW-SESSION QUICK TRIAGE TABLE

If minimal process fails -> Class A -> STOP research / PREOUTPUT_INFRA_BLOCK.

If memory near cgroup max but no OOM -> Class B -> stream/cache-release; do not call corruption.

If runtime files/tests missing after extraction -> Class C -> audit overlay order.

If partial child work occurs before episode prerequisite discovery -> Class D -> add whole-scope preflight.

If Judge output is invalid because of hidden validator rule -> Class E -> align prompt/payload/validator contract.

If old test source missing -> Class F -> never recreate it as exact historical rerun.

If a historical expected failure appears in regression -> Class G -> use frozen nonhistorical scope, preserve history.

If provider server receipt and summary disagree -> Class H -> trust raw provider/server call receipts and fix summary projection.

If experimental branch touched protected code -> Class I -> restore canonical hashes and rerun.

If packaged regression differs from source-tree regression -> Class J/K -> discard noncanonical package and rematerialize/reseal.

If DB candidate fails NAP packet construction -> Class L -> HOLD candidate, normalize and requalify.

If irrelevant DB mutation changes provider input -> Class M -> separate semantic input from provenance hash.

If char floor seems suspiciously high -> Class N -> count decoded Unicode chars.

If speaker validator explodes -> Class O -> alias normalization plus exact participant audit.

If blind mapping is inferable -> Class P -> discard map at score 0 and reseal secret salted map.

If frozen plan lacks runtime anchors -> Class Q -> do not invent post-output fields; amend only if prereg permits, otherwise HOLD.

If draft plan has structural defects before freeze -> Class R -> repair before freeze.

If draft file write fails before seal -> Class S -> restore checkpoint; no science verdict.

If scene-level effect is positive but aggregate endpoint repeatedly fails -> Class T -> prospective endpoint study; never rewrite old FAIL.

---

## 22. CURRENT SAFE RESUME POINT

Current prospective experiment:
`P07-I4J-R1-FRESH-COVERAGE-ENDPOINT-VALIDATION`

Outputs: all zero.

Resume only after healthy runtime preflight. Exact order is specified in:
`handoff/20260910/START_HERE_P07_NEW_SESSION_MASTER_HANDOFF_R1_20260910.md`

## STATUS TOKEN
`FAILURE_PLAYBOOK_R1__TRANSPORT_MEMORY_MATERIALIZATION_FAILCLOSED_SEMANTIC_CONTRACT_PROVIDER_HARNESS_PACKAGING_DB_CONSUMER_A2_MEASUREMENT_SPEAKER_BLIND_PLAN_STORAGE_ENDPOINT_CLASSES_CATALOGUED__I4J_PREOUTPUT_BLOCK`
