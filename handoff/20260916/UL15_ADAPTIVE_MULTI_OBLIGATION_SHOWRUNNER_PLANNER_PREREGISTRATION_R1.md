# UL-15 ADAPTIVE MULTI-OBLIGATION SHOWRUNNER PLANNER — PREREGISTRATION R1

Date: 2026-09-16
Project: Literary OS Development
Classification: PREREGISTERED RESEARCH / IMPLEMENTATION PROTOTYPE
Formal experiment count: unchanged
Production authority change: NONE

## 1. PURPOSE

Replace the historically fixed and compressive Episode -> Sequence -> Scene planning topology with an adaptive planner that derives episode architecture from active narrative obligations and preserves multi-character, relationship, information, social/world, causal, and payoff structure through the hierarchy.

UL-15 is not a surface-writing experiment. Plan architecture must qualify before screenplay surface generation is allowed.

## 2. HYPOTHESIS

A planner that represents an episode as an adaptive graph of narrative obligations, permits multi-obligation/multi-owner sequences, and plans state-changing scene transactions without fixed count quotas will preserve more of the source/state-kernel structure and produce less monotonous architecture than the historical fixed-topology planner, without reducing state/continuity fidelity.

## 3. RESEARCH QUESTIONS

RQ1. Can the observed human-authored 61-work episode corpus be represented without fixed sequence or scene counts and without single-owner sequence restriction?

RQ2. Can a forward Candidate planner generate Episode/Sequence/Scene architecture from a frozen state kernel while preserving causal, relationship, information, social/resource, and payoff obligations?

RQ3. Does the adaptive planner reduce template signatures and increase architecture necessity/interdependence under blind plan-only evaluation?

RQ4. Can the generated hierarchy be reverse-reconstructed from the eventual surface without material semantic loss?

## 4. FROZEN INPUT / SOURCE CUTOFF

Research-support source for calibration only:
- DB64 R108 Final Sealed SHA256 `19f3c446a73408045d02d4d99e168251dca42da3bfa00abaff1d8f9159d7ea46`;
- primary sealed cohort: 61 works / 1,160 episodes / 11,213 thick sequences / 73,639 runtime scenes;
- DB64 status remains research-support candidate; A2 remains pending; DB59 remains Production DB authority.

Human-authored distributions are priors/diagnostics only. They are forbidden as generation quotas or answer keys.

Fresh forward experiments must use frozen cutoff-safe state kernels. Hidden future targets, if any, remain unopened until the required selector/judgment freeze.

## 5. EVIDENCE CLASSES

Every output must declare exactly one:

- `SOURCE_REVERSE_ENGINEERED`: analysis/projection from authored source artifacts;
- `VIRTUAL_ANALOG`: same-chat or conceptual simulation, never treated as Candidate execution;
- `CANDIDATE_RUNTIME`: actual UL-15 Candidate code path executed, but not necessarily a live external Provider;
- `LIVE_PROVIDER`: actual fresh isolated Provider execution with response/request/model/usage and input/output hash receipts.

Evidence classes may not be silently promoted.

## 6. NEW CONTRACT STACK

### 6.1 EpisodeObligationGraphPlan.v0.1

Dynamic active obligations. Allowed types:
`EVENT / CHARACTER / RELATIONSHIP / INFORMATION / SOCIAL_ECOLOGY / WORLD_RESOURCE / THREAD_PAYOFF / FUNCTIONAL_THEME`.

Each runtime obligation must carry owners, affected entities where relevant, entry state, required delta, urgency, age where relevant, prerequisites, downstream obligations, and closure policy (`MUST_ADVANCE / MAY_DEFER / MUST_CLOSE / PRESERVE`).

No min/max episode-axis count is used as a narrative topology rule.

### 6.2 SequenceWeavePlan.v0.1

A Sequence may consume multiple obligations and have multiple owners. It records entry pressure, weave intent, state changes, typed edges (`CAUSAL / INFORMATION / RELATIONSHIP / SOCIAL / RESOURCE / PAYOFF / FUNCTIONAL_THEME`), predecessors, downstream sequences, and exit turn.

Sequence count is derived from narrative need. No exact-count requirement is allowed.

### 6.3 SceneTransactionPlan.v0.1

A runtime Scene records participants, obligations, pre-state, physical action, conflict, relationship/information/social-world/payoff transactions where relevant, state delta, exit pressure, downstream consumers, necessity rationale, and merge/split test.

Scene count is derived from necessary state transactions. Fixed slot grammars are prohibited.

## 7. ANTI-TEMPLATE RULES

Forbidden planner requirements/keys include count quotas such as `expected_sequences`, `expected_sequence_count`, `expected_scenes`, `expected_scene_count`, `fixed_sequence_count`, `fixed_scene_count`, and universal `fixed_slots/default_slots` grammars.

A naturally emergent 10-sequence / 50-scene result is not automatically invalid. However, an exact 10x5 signature triggers a topology-hold unless the plan contains explicit narrative justification and passes necessity tests.

Uniform sequence lengths, owner entropy, sequence count, or scene count are diagnostics only and may not be optimized to match corpus averages.

## 8. PLANNING LOOP

1. Cutoff-safe State Kernel.
2. Narrative Obligation Compiler.
3. Multiple counterfactual Episode architecture candidates.
4. Selector / Abstention.
5. Sequence Weaving Graph construction.
6. Scene Transaction planning.
7. Contract validation + necessity/merge/split checks.
8. Responsible-Ancestor Replanner if infeasible.
9. Only after architecture PASS: Surface Renderer.
10. Reverse Reconstruction Auditor.
11. Actual post-surface State Commit / Carry.

## 9. CONTROL / TREATMENT FOR FORWARD QUALIFICATION

Control: reconstructed historical R53 planning path with its frozen legacy topology behavior. It must be labeled `LEGACY_CONTROL`; it is not treated as a competent Candidate merely because it exists in the Production-era master.

Treatment: UL-15 Adaptive Multi-Obligation planner contracts and actual Candidate execution path.

Both arms receive the same cutoff-safe state kernel and source cutoff. Provider/model/effort parameters must be matched where a Provider is used. Contexts must be fresh and isolated; no `conversation` carry or `previous_response_id` reuse for qualification.

## 10. PRE-REGISTERED GATES

### A0 — Structural Representability (engineering precheck; already executed)

Purpose: prove the new topology is not too restrictive for the sealed human-authored corpus.

PASS condition: all 1,160 episodes can be represented with dynamic sequences/scenes and cross-linked obligations without fixed count quotas.

Result: `1160/1160 PASS`.

Observed A0 diagnostics:
- sequence count mean 9.666, median 9, p10 6, p90 14, range 2..29;
- scene count mean 63.482, median 62, p10 46, p90 about 81.1, range 6..182;
- obligation count per episode mean 40.862, median 39, p10 25, p90 60, range 9..97;
- obligation links per sequence mean 10.407, median 10, range 2..34;
- multi-owner sequence rate 0.9265;
- episodes with at least one relationship obligation 0.8198;
- exact 10x5 requirement: false.

A0 is `SOURCE_REVERSE_ENGINEERED` only. It is NOT generation-quality evidence, NOT A2, and NOT Provider evidence.

### A1 — Candidate Implementation Integrity

Before any quality comparison:
- all three schemas meta-validate;
- quota-key linter PASS;
- cross-contract reference integrity PASS;
- Candidate output must contain no undeclared obligations/sequences/scenes;
- architecture gate fail-closed;
- surface generation blocked on architecture FAIL;
- Responsible-Ancestor Replanner boundary test PASS;
- evidence class receipt present.

Current prototype precheck: 8/8 implementation tests PASS; schema meta-validation PASS; synthetic Candidate contract examples 3/3 PASS. This is engineering evidence only.

### A2 — Fresh Plan-Only Provider Qualification (NOT YET RUN)

Sample: 12 fresh/counterfactual episode tasks, frozen before output.

Evaluation happens on Episode/Sequence/Scene plans only; no screenplay prose is shown.

At least three independent blind judges score:
- obligation preservation;
- multi-character/relationship/event diversity;
- causal and information interdependence;
- social/world specificity where source state warrants it;
- sequence necessity and re-entry;
- scene necessity / merge-split quality;
- escalation and turn architecture;
- topology naturalness / anti-template quality;
- state/continuity fidelity.

Hard critical violations: future-target leakage, source-cutoff breach, continuity contradiction, fabricated required state, forced quota topology, or plan/surface evidence-class mislabeling.

Provisional preregistered pass rule: Treatment paired-majority win on >=8/12 tasks, win+tie >=10/12, and zero critical violations. If the exact external-judge protocol changes before first output, this preregistration must be versioned/resealed before generation.

### A3 — Full Surface Qualification (blocked until A2 PASS)

Generate a full broadcast episode only after plan architecture qualifies. Surface target remains >=35,000 Korean characters with no fixed upper bound. Sequence/scene counts emerge from the plan.

Two-stage external blind:
1. Surface-only reverse reconstruction, responses sealed.
2. Reveal frozen plans and score hierarchical recoverability / plan-to-surface fidelity.

### A4 — Long-Horizon State Carry

Verify actual post-surface state deltas propagate into subsequent episode planning, including relationships, information, social ecology, resources, open threads, and payoff debt.

## 11. IMPLEMENTATION PRECHECK HASHES

Research prototype hashes:
- `EpisodeObligationGraphPlan.v0.1.schema.json`: `43f69ebf36b010201f91cdf472c6311d4d9edb60a868aff320c09510d9a33c3e`
- `SequenceWeavePlan.v0.1.schema.json`: `aac9675420f593a477ff84571263d0f819e3e0f54a0d9650ac2a64af9bb0820d`
- `SceneTransactionPlan.v0.1.schema.json`: `bddffbfb78791eb1f29b84ab11b39e44ecd417b417fd104e2fd5aa746c47cfae`
- `adaptive_multi_obligation_planner_r1.py`: `bdfc115cf60d237791adbb1e49148478befeca583fc68c25173b89daa4e14172`
- A0 result JSON: `b21839dfba65e9675293798800534c2bb127799482425970eb23247a6435f0d8`
- implementation precheck: `857a1be191374b24e0dd15ae29ce07d2e4fcbaf30f0bdb6f47b4c9d8975323e8`
- schema precheck: `523db3414b97c11913bfcd88431f03383ff984b7acaeaeb742572b7fa5488ff0`

## 12. CLAIM BOUNDARY

UL-15 currently establishes a repaired research contract and A0/A1 engineering evidence only.

It does NOT establish:
- superior literary quality;
- A2 PASS;
- live OpenAI Provider PASS;
- external blind PASS;
- Candidate Production readiness;
- DB64 Production adoption;
- a new physical SYNC authority.

## 13. STATUS TOKEN

`UL15_PREREG_R1__ADAPTIVE_MULTI_OBLIGATION_CONTRACTS_DEFINED__NO_FIXED_TOPOLOGY__A0_1160_OF_1160_PASS__A1_PROTOTYPE_PRECHECK_PASS__A2_NOT_STARTED__SURFACE_BLOCKED_UNTIL_PLAN_QUALIFIES__NO_AUTHORITY_CHANGE`
