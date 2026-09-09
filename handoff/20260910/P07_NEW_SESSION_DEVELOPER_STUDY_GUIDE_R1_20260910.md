# P07 NEW SESSION DEVELOPER STUDY GUIDE R1

Date: 2026-09-10
Purpose: teach a fresh session/developer the current Literary OS state, why the current rules exist, and how to resume without repeating prior mistakes.

## MODULE 1 — LEARN THE AUTHORITY MODEL FIRST

Read:
1. `START_HERE_P07_NEW_SESSION_MASTER_HANDOFF_R2_20260910.md`
2. `CURRENT_DEVELOPER_HUB_AUTHORITY.md`
3. `P07_I4I_R2_FRESH_REPLICATION_CLOSURE_AND_PHYSICAL_SYNC_R2_20260910.md`

Learn these distinctions:
- Physical Package Authority != Active Engine Authority != Candidate Authority != Production Authority.
- Current physical research-sync may contain newer research evidence while the Active Engine remains I4H Recovery R3.
- Semantic Alignment Virtual R1 is qualified virtually but not Live-qualified and not active.
- DB64 is a candidate under HOLD, not the DB authority.
- Research FAIL/HOLD is preserved, not rewritten when a later repair succeeds.

Checkpoint questions:
- What is the current nine-file material SHA?
- What is the active C2 SHA?
- Why is DB59 still authority?
- Why are I4I R1/R2 still FAIL?

Correct answers are in the master handoff/authority docs.

## MODULE 2 — LEARN FAILURE CLASSIFICATION BEFORE DEBUGGING

Read:
`P07_FAILURE_INCIDENT_RESPONSE_PLAYBOOK_R1_20260910.md`

Core lesson:
Do not call every failure an engine bug.

Separate at least:
1. platform execution transport;
2. memory/page-cache pressure;
3. package/materialization topology;
4. engine integration/fail-closed ordering;
5. model prompt/validator semantic contract;
6. Provider-Analog harness bookkeeping;
7. physical packaging/rematerialization;
8. DB schema/Consumer contract;
9. A2 provenance-vs-semantic invariance;
10. experiment measurement/blinding/frozen-plan defects.

The first debugging question is always:
`Which failure class owns this symptom?`

Do not patch Literary OS code before answering that question.

## MODULE 3 — LEARN THE EXPERIMENT GOVERNANCE METHOD

All prospective experiments must freeze before outputs:
- Hypothesis
- Purpose / Research Question
- Parent Authority
- Frozen Input / Source Cutoff
- Control / Treatment or arms
- generation order
- evaluation axes
- pass/fail thresholds
- critical fail conditions
- claim boundary
- physical packaging rule

Completed-experiment recovery chain:
Preregistration -> Frozen Inputs -> Control/Seal -> Selector/Profile Freeze -> Treatment/Integrity -> Provider/Runtime Receipts if claimed -> Blind Map Hash -> Blind Scores -> Unblind -> Final Result -> Post Regression -> Package Impact -> Changed Physical Packages.

Important learned examples:
- I4H R2 44/45 remains HOLD even though R3 fixed it.
- I4I R1 +0.2833 remains FAIL even though scene-level signal is positive.
- I4I R2 +0.1667 remains FAIL and cannot be pooled with R1.
- J0 endpoint analysis is knowledge-only and cannot retroactively alter R1/R2.

## MODULE 4 — LEARN THE OPEN RESEARCH TRACKS

### Track A — I4J active next experiment
`P07-I4J-R1-FRESH-COVERAGE-ENDPOINT-VALIDATION`
Current outputs all 0 because runtime preflight is failing.

Goal:
prospectively test whether conservative I4H surface effects are better measured as target-axis improvement plus separate protection hard gates, and test dose/coverage behavior with ARM_0/ARM_50/ARM_100.

### Track B — Semantic Alignment
Virtual candidate already passes deterministic/provider-analog qualification. Next valid promotion evidence requires genuine OpenAI Live confirmation against the exact frozen candidate.

### Track C — DB64 / 9-Contract
Repair schema generations, missing ThreadState/knowledge members and engine A2 provenance/semantic separation, then requalify. Only after qualification may DB59-vs-DB64 utility comparison run.

### Later governance
Fresh independent/human/live gates and Formal R140 remain future work. Formal count remains 137.

## MODULE 5 — LEARN THE EXACT RESUME PROCEDURE

Current block is infrastructure, not science:
`PREOUTPUT_INFRA_BLOCK__MINIMAL_PROCESS_3_OF_3_TRANSPORT_TIMEOUT__NO_SCIENTIFIC_FAIL__NO_FRESH_OUTPUTS`

Do not begin with prose generation.

Resume checklist:
1. minimal process succeeds;
2. filesystem read/write/stat succeeds;
3. cgroup memory/OOM state is safe;
4. a small archive member can be read;
5. current Research Sync R2 identities are verified;
6. I4J prereg commit is confirmed;
7. fresh complete plan is created and frozen with every runtime-required semantic anchor;
8. scale floors validated before Control;
9. Control generated once and sealed;
10. unchanged R3 Selector runs only after Control seal;
11. revisions generated once;
12. coverage arms assembled deterministically;
13. arm identities/hashes sealed before scoring;
14. masked scoring then unblind;
15. post-258 regression;
16. package-impact calculation;
17. every changed transport physically rebuilt/audited/delivered.

If step 1 fails, STOP and record infrastructure recurrence only.

## MODULE 6 — CREATIVE RULES THAT ARE PART OF THE SYSTEM CONTRACT

- Dialogue should not explain the story/feeling directly.
- Stage direction may be detailed and explanatory.
- Emotion should be embodied through action/stage direction before dialogue.
- whole episode >=35,000 Korean Unicode characters; no upper cap.
- 9-10 sequences / 45-50 scenes are minimum reference scale, not a fixed ceiling.
- lower-layer craft failure can require Responsible-Ancestor backpropagation and relowering.
- Python is for tests/validation/hash/package/metadata, not literary prose authorship.

## FINAL LEARNING TEST

A new session is ready to work only if it can answer:
1. What is the active engine vs current physical research-sync authority?
2. Why is Semantic Alignment not active despite 281/281?
3. Why is DB64 still HOLD?
4. Why are R1/R2 both still FAIL?
5. What did J0 establish and what did it NOT establish?
6. Why are all J1 outputs still 0?
7. What does `TransportTimeoutError` mean scientifically?
8. What is the exact next action after runtime recovery?

If any answer is uncertain, return to Master Handoff R2 and Failure Playbook before generating new outputs.
