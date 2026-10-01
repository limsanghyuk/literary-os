# UL18 — Open-Debt Semantic Separation / Repaired Upper-Layer Successor Qualification — Preregistration R1

Date: 2026-10-01
Status: PREREGISTERED__BEFORE_UL18_PRIMARY_OUTPUTS__NO_AUTHORITY_CHANGE

## Parent finding

UL17 exact-R69 Stage B is immutable FAIL at B06 PAYOFF urgency.

Exact R69 conflates:
- source due/closure eligibility,
- nondeferrable current-episode urgency,
- scheduling selection,
- final resolution.

The bounded research repair introduces `SELECTED_OPEN_TOUCH` so a source `due=false, can_defer=false` obligation can be scheduled and materially advanced without false closure.

Parent evidence:
- `research/upper_layer/20261001/UL17_STAGE_B_EXACT_R69_CAUSAL_ADOPTION_RESULT_R1.json`
- `research/upper_layer/20261001/UL17_STAGE_B_ROOT_CAUSE_AUDIT_R1.json`
- `research/upper_layer/20261001/UL17_STAGE_B_REPAIR_PREREG_R1.md`
- `research/upper_layer/20261001/UL17_STAGE_B_OPEN_DEBT_REPAIR_CANDIDATE_RESULT_R1.json`

## Authority boundary

Physical Authority remains SYNC-R74.
Active Runtime remains exact R69.
Production remains ENG:R47 / LEGACY_R53.
Runtime DB remains DB59 frozen.

The repair candidate is research-only until this qualification closes PASS and the project explicitly adopts/physicalizes it.

## Research question

Can the bounded open-debt semantic repair:
1. fix the UL17 B06 false-closure defect,
2. preserve all unaffected exact-R69 upper-layer behavior,
3. preserve R66 transaction-family semantics,
4. preserve R67 dual-ledger state carry legality,
5. preserve R68 semantic-repetition validation,
6. preserve R69 counterfactual scene-necessity validation,
7. generalize beyond the single B06 example,
without future-source leakage, false fulfillment, debt loss, or unrelated architecture drift?

## Frozen implementation identity

Allowed changed runtime file:
`literary_os_runtime/adaptive_showrunner_ul16.py`

Research candidate patched source SHA256:
`f2a22d1156f50152b8de1ae745d16e3189f6731758a83b8cc7dc2b37e8e8553b`

Patch diff SHA256:
`2ec2e9e334dfae83fa4d496ab77359707e6de38d20d838670c7c64718baaab08`

No additional runtime source change is allowed after UL18 primary cases begin. If a new defect requires code change, freeze this attempt and preregister a new repair revision.

## Stage A — Regression / invariance qualification

Required:
- 45/45 runtime Python modules compile.
- UL17 BASE, B01-B05, B07, B08 architecture hashes are byte-semantically identical to canonical exact-R69 Stage-B hashes.
- R58B diverse-material fixture full architecture output is identical between exact R69 and repaired candidate.
- Recover and check R66/R67/R68/R69 qualified invariants from existing frozen receipts; where executable fixture bytes exist, rerun them. Where only immutable receipts exist, mark historical-evidence-only rather than inventing executable PASS.

Hard FAIL:
- any unrelated architecture drift;
- altered transaction-family selection outside open-touch cases;
- altered repetition/necessity verdict on unchanged inputs.

## Stage B — Fresh open-debt adversarial suite

Freeze before execution the following semantic cases, each using new IDs/text not copied from UL17 B06:

1. TRUE_DUE_NONDEFERRABLE
   - due=true, can_defer=false
   - must schedule and may resolve normally.

2. OPEN_NONDEFERRABLE
   - due=false, can_defer=false
   - must schedule/touch, must not resolve, must remain open debt.

3. OPEN_DEFERRABLE
   - due=false, can_defer=true
   - must remain DEFERRED and unscheduled unless independently related as deferred pressure.

4. BLOCKED_TRUE_DUE
   - due=true with missing prerequisite
   - must be BLOCKED_PRECONDITION and get no resolving scene.

5. BLOCKED_OPEN_TOUCH
   - due=false, can_defer=false with missing prerequisite
   - must be BLOCKED_PRECONDITION, not selected merely because urgent.

6. MULTIPLE_OPEN_TOUCH
   - two unrelated open nondeferrable obligations
   - both scheduled/touched, neither resolved, both carried open.

7. OPEN_TOUCH_WITH_DUE_INTERSECTION
   - one due + one open-touch sharing owners/group/event relation
   - weaving may occur, but only true-due may resolve.

8. IRRELEVANT_METADATA_SENTINEL
   - metadata-only change
   - semantic architecture hash must remain invariant.

Stage-B hard gates:
- future_source_leakage = 0
- false_due_fulfillment = 0
- false_open_touch_fulfillment = 0
- lost_open_debt = 0
- blocked_precondition_false_fulfillment = 0
- unrelated_metadata_semantic_change = 0
- validation errors = 0 for non-broadcast causal qualification mode.

## Stage C — State Commit / Carry integration

For each selected-open-touch obligation:
- generated scene contract must expose an observable current-episode touch;
- canonical commit packet must record OPEN evidence, not fulfilled evidence;
- planner-unrealized ledger may retain planning metadata with factual_access_forbidden=true;
- next-episode planning must be able to consume the open obligation again;
- no rich planner-only claim may enter established factual state.

PASS requires exact dual-ledger legality and no false canonical fact.

## Stage D — Adoption decision

Only after A/B/C PASS:
- classify the repair candidate as eligible for Candidate-runtime adoption.
- Do not call it exact R69.
- Assign a new successor runtime identity during physicalization.
- run the project-wide regression and C1/C2 binding process.
- reseal CONTROL/A/B1/B2/C1/C2-A/C2-B/D1/D2.
- verify SHA256, CRC, logical C2, Trust Root and custody.
- only then deliver a new 5-Part / 9-Package successor and move Physical Authority.

## Stage E — Fresh upper-layer quality requalification after physicalization

The old UL17 Stage-C/D fixture and mapping are historical after the repair because the Treatment identity changed and its design is now exposed.

A fresh multi-strand fixture must therefore be sealed before successor architecture output.
Then rerun:
- causal-adoption audit,
- architecture-only generation,
- SINGLE_CAUSAL_SPINE diagnostic,
- independent J01/J02/J03 architecture-only blind,
- mapping reveal only after 3/3 first valid judgments are sealed.

Only a PASS here can restore current upper-layer quality qualification.

## Stop rules

- UL17 exact-R69 FAIL is never rewritten.
- No Stage C/D result from exact-R69 UL17 transfers automatically to the repaired successor.
- No physical package successor is claimed from research-only local ZIPs.
- If broader regression fails, stop before physicalization.
