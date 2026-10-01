# START HERE — SYNC-R74 PHYSICAL BASELINE / UL17 EXACT-R69 FAIL / UL18 REPAIR-CANDIDATE QUALIFIED — R17

Date: 2026-10-01

Status:
`PHYSICAL_SYNC_R74__DEVELOPER_HELD_9_OF_9__ACTIVE_EXACT_R69__UL17_STAGE_B_FAIL_IMMUTABLE__UL18_A_B_C_PASS__REPAIR_CANDIDATE_ADOPTION_ELIGIBLE__PHYSICALIZATION_NOT_STARTED`

R17 supersedes R16 for overall session recovery and research interpretation.
R16 remains the canonical record of the pre-execution transport HOLD and developer-held SYNC-R74 baseline.
R14 remains canonical for the frozen PA8 Control1/Treatment0 experiment.

## 1. Authority split — unchanged

Physical Authority remains **SYNC-R74**.

- Developer-held physical set: 9/9
- Active Runtime: exact R69
- exact R69 runtime SHA256: `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Post-R74 physical successor delivered: NONE

Research Overlay does not change Physical Authority.

## 2. Runtime transport HOLD is closed

The prior ClientError/transport HOLD did not recur.

SYNC-R74 C1 was recovered from the user Library and verified:
- 140,403,571 bytes
- SHA256 `3a1880310b7291d832b24c749c47dee2f6862387ddedb8ce3bcb652e0e899f5d`
- CRC PASS

Nested exact R69:
- 19,137,771 bytes
- SHA256 `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- 497 entries
- CRC PASS

Therefore UL17 Stage B obtained a real scientific verdict.

## 3. UL17 exact-R69 Stage B — immutable FAIL

Canonical:
`research/upper_layer/20261001/UL17_STAGE_B_EXACT_R69_CAUSAL_ADOPTION_RESULT_R1.json`

B01 THREAD: PASS  
B02 RELATIONSHIP: PASS  
B03 INFORMATION: PASS  
B04 SOCIAL: PASS  
B05 EVENT/PRECONDITION: PASS  
B06 PAYOFF urgency: **FAIL**  
B07 CHARACTER: PASS  
B08 irrelevant metadata invariance: PASS

B06 exact defect:
source `PAY_TAPE_1 due=false`, but changing `can_defer=true -> false` caused exact R69 to:
- classify it as `SELECTED_DUE`;
- generate a final RESOLVE;
- falsely close an open payoff;
- lose the open debt.

Violations:
- FALSE_SOURCE_DUE_FULFILLMENT
- OPEN_PAYOFF_FALSE_CLOSURE
- LOST_OPEN_PAYOFF_DEBT

Responsible boundary:
`UL16_OBLIGATION_DISPOSITION_AND_SCENE_RESOLUTION_SEMANTICS`

UL17 Stage C/D are **not eligible**.
Do not rewrite UL17 as PASS.

## 4. Root cause

Exact R69 uses:
`due_raw = source_due OR not can_defer`

and then treats every accepted row as fully due/resolvable.

This collapses distinct semantics:
1. source due/closure eligibility;
2. current-episode urgency/nondeferrability;
3. scheduling selection;
4. final resolution.

Existing upstream contracts already contain partial/open-debt semantics.
The missing distinction is at the Adaptive UL16 obligation boundary.

## 5. Bounded repair candidate

Preregistered before implementation:
`research/upper_layer/20261001/UL17_STAGE_B_REPAIR_PREREG_R1.md`

Repair result:
`research/upper_layer/20261001/UL17_STAGE_B_OPEN_DEBT_REPAIR_CANDIDATE_RESULT_R1.json`

Only changed source:
`literary_os_runtime/adaptive_showrunner_ul16.py`

Exact R69 source SHA:
`740cca05a94dbb59eb9a1600e1c7d98cdc887693aa5ab46fec2bd2eaef78d306`

Research repair source SHA:
`f2a22d1156f50152b8de1ae745d16e3189f6731758a83b8cc7dc2b37e8e8553b`

New semantic state:
`SELECTED_OPEN_TOUCH`

Meaning:
- source due=false;
- current episode cannot ignore/defer the pressure;
- obligation must be scheduled and materially touched;
- final resolution is forbidden;
- terminal debt remains OPEN.

## 6. Exact frozen UL17 replay after repair

The same frozen UL17 fixture/matrix were replayed in non-broadcast causal-qualification mode.

Unrelated outputs remained exactly stable:
- BASE hash unchanged
- B01 unchanged
- B02 unchanged
- B03 unchanged
- B04 unchanged
- B05 unchanged
- B07 unchanged
- B08 unchanged

B06 alone changed.

Repaired B06:
- disposition = SELECTED_OPEN_TOUCH
- source due remains false
- PAY_TAPE_1 stays in open debt
- scene phases = ACTIVATE_PAYOFF -> ADVANCE_KEEP_OPEN
- final resolve = false
- open_touch_preserved = true
- lost deferred/open debt = 0
- false fulfilled deferred/open = 0
- validation PASS

This is a repair candidate result, not a rewrite of exact R69.

## 7. UL18 successor qualification

Preregistration:
`research/upper_layer/20261001/UL18_OPEN_DEBT_SEMANTIC_SUCCESSOR_QUALIFICATION_PREREG_R1.md`

Frozen fresh adversarial suite:
`research/upper_layer/20261001/UL18_OPEN_DEBT_ADVERSARIAL_SUITE_R1.json`

Final qualification:
`research/upper_layer/20261001/UL18_OPEN_DEBT_SUCCESSOR_QUALIFICATION_RESULT_R1.json`

### Stage A — PASS
- runtime compile 45/45 PASS
- unaffected UL17 architecture hashes exactly preserved
- R58B diverse-material whole architecture output bit-identical between exact R69 and repair
- R66/R67/R68/R69 immutable result receipts recovered and checked as historical evidence
- their fresh executable runners are not present in the recovered runtime bundle, so project-wide executable regression is still required before physicalization

### Stage B — PASS 8/8
Fresh cases:
1. TRUE_DUE_NONDEFERRABLE
2. OPEN_NONDEFERRABLE
3. OPEN_DEFERRABLE
4. BLOCKED_TRUE_DUE
5. BLOCKED_OPEN_TOUCH
6. MULTIPLE_OPEN_TOUCH
7. OPEN_TOUCH_WITH_DUE_INTERSECTION
8. IRRELEVANT_METADATA_SENTINEL

All 8 PASS.

Hard gates:
- future-source leakage 0
- false due fulfillment 0
- false open-touch fulfillment 0
- lost open debt 0
- blocked-precondition false fulfillment 0
- metadata semantic change 0
- validation errors 0

### Stage C — PASS 3/3 applicable
Selected-open-touch cases were passed through:
Scene Contract -> semantic commit packet -> dual ledgers -> next-episode Adaptive Showrunner consumption.

Verified:
- canonical state = OPEN only;
- planner-only metadata retained separately;
- factual_access_forbidden=true;
- source episode does not mark the obligation fulfilled;
- next episode reconsumes it with provenance `PLANNER_UNREALIZED_OBLIGATION`.

## 8. What this means

The current evidence does **not** say that exact R69 passed UL17.
It did not.

The evidence says:
- exact R69 has a bounded open-debt disposition defect;
- the responsible boundary is localized;
- a minimal repair fixes the defect;
- the repair generalizes beyond B06;
- unaffected upper-layer decisions remain stable in the tested regressions;
- dual-ledger carry remains legal.

Therefore the repair candidate is:
`ADOPTION_ELIGIBLE__RESEARCH_ONLY`

It is not yet:
- Active Runtime;
- C1;
- C2;
- Physical Authority;
- Production.

## 9. Exact next transaction

Do not proceed to the old UL17 Stage C/D with the patched candidate.
The Treatment identity changed and the old Stage-C/D path was frozen for exact R69.

Next:
1. recover/run the broader project-wide executable regression against the repaired candidate;
2. if PASS, assign a new successor Candidate runtime identity;
3. bind it into C1/C2;
4. reseal CONTROL/A/B1/B2/C1/C2-A/C2-B/D1/D2;
5. audit SHA256/CRC/logical C2/Trust Root/custody;
6. deliver all nine physical packages;
7. only after physicalization create a **fresh unseen** multi-strand fixture;
8. rerun current upper-layer causal/architecture qualification and independent J01/J02/J03 architecture-only blind;
9. only after that PASS descend to full >=40K provider screenplay.

## 10. Parallel tracks

PA8 remains frozen:
`CONTROL_1__TREATMENT_0__CONTROL_STRUCTURAL_PASS__CONTROL_CONTINUITY_HEADROOM_ESTABLISHED`

Dialogue baseline remains preregistered.
No dialogue-share numeric quota is authorized yet.

## 11. Physicalization rule

No actual post-R74 Candidate runtime/C1/C2 package binding has been performed in this research transaction.

Therefore:
**Physical Authority remains SYNC-R74.**

Do not provide or claim a new 5-Part / 9-Package successor until the project-wide regression + binding + reseal chain is complete.
