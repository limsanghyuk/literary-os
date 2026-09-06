# Literary OS — Session Recovery START HERE R1
Date: 2026-09-06
Purpose: durable recovery authority when a ChatGPT session ends or the local artifact/container backend cannot rebuild the canonical 5-Part / 9-Package delivery.

## 0. Read this first
This document is a recovery pointer, NOT a claim that the current 5-Part / 9-Package binaries have been physically resealed.

Current high-level status:
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores
- Production: ENG:R47 immutable
- P07: active preformal / not complete
- R140: HARD BLOCK
- DB59 frozen reference SHA256: a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9
- Current active re-pretest: RFV3 A/B/C/D Causal Re-pretest, preregistered before outputs
- Current packaging state: 9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE
- Local artifact/container backend was returning ClientError even for minimal health calls; classify as infrastructure HOLD, not experiment FAIL.

## 1. Scientific correction that MUST survive session loss
Claude/CT independently found that the then-current C2 R39 retrieval path repeatedly produced NO_RETRIEVAL, so DB59 bytes were read/hashed but donor semantic content did not reach the LLM semantic planning input. The previous claim that runtime coverage alone proved DB adoption completeness is withdrawn.

Correct adoption standard now required:
Value changes -> Consumer receives -> selected donor/semantic payload changes -> LLM provider input changes -> downstream behavior changes -> Receipt/Trace proves the propagation.

Previous RFV provider-boundary evidence remains valid for malformed response/refusal/model mismatch/hash integrity/retry/fail-closed behavior. Do NOT relabel those mock/local results as Live Provider evidence.

## 2. RFV2 repaired state — must be reverified from bytes before new claims
The working RFV2 repair state had the following observed results before the local backend failure:
- Actual DB59 retrieval source: 1,097 eligible THICK members / 10,784 records.
- Six historical development cases observed USE_RETRIEVAL after retrieval-contract repair.
- Direct DB59 vs Frozen Retrieval Index: six-case semantic retrieval result equivalence observed.
- Selected donor mutation changes semantic provider input.
- Irrelevant unselected donor mutation does not change semantic provider input.
- CASE-01 observed DB59 donor propagation into SEQUENCE_PLAN semantic provider input.
- Frozen Retrieval Index SHA256 observed: d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419
- Index equivalence/tamper audit SHA256 observed: 81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23
- CASE-01 DB59 -> semantic provider input evidence SHA256 observed: ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f
- Nonhistorical regression previously observed: 185/185 PASS.

These are recovery observations, not a substitute for fresh verification after environment restoration.

## 3. CP1 status
CP1 means the first real paired OpenAI live smoke before formal R140, not R140 itself.
- Current R11 rf_live_parity_runner had no successful CP1 branch; it deliberately HOLDed.
- Historical P07 PRE09 material contains an earlier paired CP1/live craft parity runner design.
- Required action is restoration/integration into current RFV2/RFV3 authority, not invention from scratch.
- Official R-F CP1 live outputs/Provider Receipts remain 0 until a new current-authority CP1 is executed.
- CT nonformal live evidence is separate and cannot be relabeled CP1 or Formal R140.

## 4. CT evidence that should be uploaded to a new session
If available, upload these supporting files together with this handoff:
1. CT_TO_GPT_ADDENDUM7_C2R39_VERIFICATION_AND_DEFECT_RECOMMENDATION_20260906.zip
   - reported SHA256: e661d0134af59deeb3ad6e81e62ac17881bce255ed833dcc6714b9f47542ec5f
   - 18 entries, CRC PASS, credential leak 0 according to the verified current-session inspection.
2. CT_TO_GPT_회신_부록7_C2R39검증_결함권고_20260906.md
3. A E.zip — CT live/API experiment bundle. Treat as evidence to inspect, not as automatically authoritative. A new session must verify its internal Provider Receipts, logs, scripts, retrieval state, and script outputs before making claims.

Important CT interpretation:
- CT-17 is nonformal live evidence / pre-repair live baseline, not R-F CP1 and not Formal R140.
- It appears to have exercised recent candidate structures with DB59 semantic retrieval effectively absent; use it as PRE-REPAIR LIVE BASELINE only after file-level verification.

## 5. Current RFV3 preregistration — NO OUTPUTS YET
Authoritative file:
- handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md
- GitHub commit: 07c256a84718c0b8f4017c383c174c4bcf3a8d95

Frozen arms:
A = SUMMARY ONLY
B = PRE-REPAIR ENGINE / NO_RETRIEVAL
C = RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
D = FULL CURRENT CANDIDATE + BIDIRECTIONAL REFINEMENT

Purpose:
- A vs B: runtime information preservation/loss
- B vs C: incremental value of repaired DB59 retrieval
- C vs D: incremental value of bidirectional refinement

Same work/source cutoff/surface settings/generation-size contract across arms. Actual EP06 forbidden. No result-informed threshold/prompt/donor/rubric tuning. Python literary prose generation = 0.

## 6. Atomic checkpoint already sealed
Authoritative checkpoint:
- handoff/20260906/RFV3_TASK01_PREREG_AND_9PACKAGE_ATOMIC_CHECKPOINT_R1.md
- GitHub commit: a1e6ca0e2f84eedef3ae4ce188cecf5dc3857079

Status at checkpoint:
RFV3_TASK01_PREREGISTERED__LOCAL_ARTIFACT_BACKEND_HOLD__9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE

No RFV3 generation output existed at that checkpoint.

## 7. Mandatory canonical delivery structure
Every scientifically meaningful completed task must be propagated into the canonical 5-Part / 9-Package structure before the following task is considered physically closed:
1. CONTROL
2. PART-A
3. PART-B1
4. PART-B2
5. PART-C1
6. PART-C2-A
7. PART-C2-B
8. PART-D1
9. PART-D2

PART-C is exactly C1 + C2-A + C2-B. C2-A || C2-B must reconstruct the current C2 authority byte-for-byte and match its declared SHA256.

If package rebuilding is impossible because of infrastructure failure:
- DO NOT fabricate new package SHAs.
- DO NOT claim physical closure.
- Seal/update this handoff + an atomic task checkpoint externally.
- Mark 9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE.
- Package reconstruction/audit is the first action after infrastructure recovery.

## 8. Minimum handoff set when binary packages cannot be produced
A new ChatGPT session should receive, at minimum:
1. This SESSION_RECOVERY_START_HERE_R1.md or its GitHub path/commit.
2. RFV3 preregistration file/commit 07c256a84718c0b8f4017c383c174c4bcf3a8d95.
3. RFV3 atomic checkpoint file/commit a1e6ca0e2f84eedef3ae4ce188cecf5dc3857079.
4. CT Addendum 7 ZIP + Markdown if available.
5. A E.zip if the CT live evidence is needed for comparison.
6. The most recent physically sealed 5-Part / 9-Package binaries that the user still possesses, even if they predate the current pending repair; they must be labeled PREVIOUS_PHYSICAL_BASELINE and never silently treated as current repaired authority.
7. Any new task-specific preregistration/amendment/checkpoint produced after this file; newest checkpoint wins only for status, not for missing binary claims.

This minimum set is enough to understand the scientific state and resume safely, but it is NOT enough to execute the engine unless the required runtime/database binaries are also available.

## 9. Complete handoff set for executable recovery
For actual engine work, additionally provide:
- all current 5-Part / 9-Package files once physically available;
- delivery manifest + Trust Root;
- Current/START_HERE pointer;
- DB59 authority or accessible package containing it, with SHA verification;
- current RFV2/RFV3 runtime overlay/source bytes;
- Frozen Retrieval Index if still part of current authority;
- regression/equivalence/tamper evidence;
- CP1 restoration code/checkpoint once implemented;
- Provider Receipts only for actual live calls, with secrets removed.

## 10. New-session resume order
1. Read this file and latest atomic checkpoint first.
2. Confirm Formal count 137 and R140 0/0/0 unless a later sealed checkpoint proves otherwise.
3. Verify no completed task after the latest checkpoint is being claimed without artifacts.
4. Recover/verify the latest physical 5-Part / 9-Package baseline.
5. If packaging was pending, complete package propagation/audit BEFORE beginning the next scientific task.
6. Freshly reverify RFV2 retrieval state from bytes.
7. Continue RFV3 strictly under the preregistered A/B/C/D protocol.
8. Do not start Formal R140. Required high-level path remains current-authority preformal validation -> R-F real paired live validation -> R-G freeze -> fresh formal sample -> revised R140 preregistration -> new G0 -> Formal R140.

## 11. Session continuity operating rule from now on
At the START of each meaningful task:
- update or create a prereg/checkpoint with exact starting authority and pending package state.
At the END of each meaningful task:
- seal results/status;
- attempt immediate 5-Part / 9-Package propagation;
- audit SHA/CRC/unsafe/duplicate/nested ZIP/reassembly as applicable;
- update the recovery pointer/checkpoint;
- only then call the task physically closed.

If a session may end before physical packaging finishes, the session must leave a durable checkpoint stating exactly:
- what changed;
- what was verified;
- what was not verified;
- formal count/R140 counters;
- changed code/data/artifact hashes if known;
- package propagation status;
- exact next action.

## 12. Claim boundary
This recovery document preserves continuity. It does not itself certify scientific PASS, Live Provider execution, package integrity, or production promotion. Those require their own evidence and physical audits.
