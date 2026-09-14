# A2R32 PREREGISTRATION R1

Date: 2026-09-14
Experiment ID: `P07-DATA-A2R32-UTILITY-CONTROLLED-MINIMAL-NOVELTY-PLANNING-QUALIFICATION`
Maturity program: `PRE_LEVEL_3 / LEVEL_3_ENTRY_QUALIFICATION / E2`
Status at seal: `PREREGISTERED__OUTPUTS_0__RUNTIME_HOLD`

## 1. Parent evidence

Immutable parent:
- A2R31 Full Novelty Signature Realization Planning Qualification
- final verdict: **FAIL 6W/2T/4L**
- parent failure may not be relabeled or rescored.

Preserved positive authorities:
- A2R10 rolling research retrieval fuel — PASS
- canonical A2R26 protected-baseline optional advisory + abstention — PASS 10W/2T/0L

Failure diagnosis boundary:
- `handoff/20260914/A2R31_FAILURE_DIAGNOSIS_BOUNDARY_R1_20260914.md`
- exact four Treatment-loss case identities are not guessed while runtime/file-byte verification is unavailable.

## 2. Research question

Can the A2R31 signal-transmission success be converted into a stable full-planning quality improvement by **vetoing case-irrelevant novelty and realizing only a minimal sufficient novelty subset**, while preserving the strong DB59 baseline and abstaining when no safe additive DB64 value exists?

## 3. Hypothesis

A2R31 failed because useful additive signal was transmitted without sufficiently strict utility control. If advisory novelty is filtered by fresh-case relevance, physical affordance, lifecycle coherence, and a fixed novelty-density budget, the Treatment should improve planning more often while reducing harmful novelty injection.

## 4. Fresh frozen input pool

Fresh pool:
`research/20260914/A2R32_FRESH_POOL_24_R1.json`

Git commit seal at pool creation:
`84aee3ecf641ab2ec3ea94e03f591d28797b9bee`

The pool contains 24 new cases A32C01–A32C24. A2R31 cases may not be reused for qualification.

Because runtime is currently unavailable, SHA256 of the pool bytes is pending runtime recovery. The Git commit is the current immutable pre-output custody seal. SHA256 must be computed and attached before any generated planning output is accepted.

## 5. Frozen arms

### Control
Exact protected DB59 baseline directives plus DB59 optional advisory candidates, passed through the same A2R32 utility-control gate and the same planner.

### Treatment
The exact same protected DB59 baseline directives plus DB64-current optional additive advisory candidates, passed through the same A2R32 utility-control gate and the same planner.

Treatment may not replace the protected DB59 baseline.

## 6. Retrieval and data doctrine — unchanged

Preserve the qualified A2R10 doctrine:
- DB64 current native semantic view;
- provenance-bound DB59 compatibility fallback only where DB64 native representation is absent;
- fallback may not overwrite DB64-native meaning;
- no Production DB promotion;
- no threshold reduction.

Retrieval/scorer implementation must be byte-reverified against the previously qualified deterministic scorer before outputs.

## 7. Structured abstraction — unchanged

No raw donor prose, source work title, character identity, DB label, work_id, seq_id, or source_layer may cross into the blind planning boundary.

Use only the identity-free structured functional abstraction already qualified mechanically in the prior lineage.

## 8. A2R32 intervention: Utility-Controlled Minimal Novelty

This experiment changes only the **advisory utility gate and novelty realization policy**.

### 8.1 Baseline protection

- Protected baseline directive count remains 4/4 in both arms.
- Baseline bytes/semantic structure must be identical across paired arms.
- An advisory may supplement but may not replace baseline functions.

### 8.2 Advisory count

- At most ONE optional advisory may be USED per plan.
- All other advisories must be recorded as `ABSTAIN`.
- If no advisory survives every gate below, the plan must use baseline only.

### 8.3 Target-axis gate

An advisory is eligible only if its declared `target_axis` is one of the case’s preregistered `target_axes`.

Otherwise: `ABSTAIN__NON_TARGET_AXIS`.

### 8.4 Case-Relevance Veto

Each novelty atom is scored against frozen case terms using the following token→case-keyword families.

#### CHARACTER_STATE
- REVERSAL → 반전, 뒤집, 변경, 재판단, 오류, 불일치
- BELIEF_CHANGE → 판단, 믿음, 의심, 증거, 확인
- STATE_CHANGE → 역할, 선택, 책임, 결정
- ACCESS_CHANGE → 출입, 접근, 권한, 카드, 열쇠, 문
- ROLE_CHANGE → 역할, 책임, 후계, 담당
- REVEAL → 공개, 증거, 기록, 발견
- CONFIRM → 확인, 검증, 기록, 증거
- PUBLICIZE → 공개, 보도, 정정

#### RELATIONSHIP_PRESSURE
- BETRAYAL → 배신, 은폐, 조작, 위조
- RESPONSIBILITY → 책임, 인계, 배정, 의무
- ACCESS → 출입, 접근, 권한, 열쇠, 카드, 문
- POWER → 권한, 결정, 지휘
- PROMISE → 약속, 협약, 서약, 계약, 유언
- TRUST → 신뢰, 보호, 불일치
- PROTECTION → 보호, 안전, 가족
- CONTROL → 통제, 제한, 잠금
- COOPERATION → 협력, 공동, 조직, 팀
- DEBT → 보상, 부채, 의무
- SEPARATION → 폐쇄, 철수, 중단
- RECONCILIATION → 재협상, 회복, 화해

#### CAUSAL_ESCALATION
- EVIDENCE → 증거, 기록, 로그, 표본, 검체, 센서
- TIME_PRESSURE → 폭풍, 호우, 긴급, 즉시, 위기, 대피
- FAILURE → 오류, 누락, 고장, 훼손, 분실, 공백
- CONSEQUENCE → 사고, 피해, 위기, 폐쇄, 장애
- DECISION → 결정, 승인, 선택, 중단, 폐기, 철수
- BLOCKER → 보류, 제한, 잠금, 압류, 통관
- INFO_REVEAL → 공개, 발견, 기록, 증거
- INFO_REVERSAL → 불일치, 반전, 뒤집, 다르
- THREAD_ESCALATION → 확대, 위기, 사고
- THREAD_PAYOFF → 회수, 약속, 의무, 협약
- THREAD_REACTIVATION → 다시, 재발, 과거, 약속
- THREAD_REVERSAL → 반전, 의미변화, 뒤집

A novelty atom with zero case-keyword support is rejected unless a later rule below gives an explicit deterministic affordance match.

### 8.5 PHYSICALIZATION affordance veto

Physical novelty is legal only when the novelty token maps to a declared `physical_affordances` item in the fresh case.

Frozen mapping:
- RECORD → record
- DOCUMENT → document
- CAMERA → camera
- PHONE → phone
- KEY → key
- SCREEN → screen
- SEAL → seal
- DOOR → door
- HAND → hand
- STOP → stop or button
- PROP → any non-empty physical_affordances list
- EVIDENCE → record, sample, seal, label, sensor, box, card, document
- GRAB_RELEASE → hand, card, key, document, rope, box, vest, container
- POSITION → door, gate, container, lever
- PHOTO → camera
- FALL → only if case terms explicitly contain fall/collapse/injury equivalents; none may be inferred from generic danger
- BLOOD → only if case terms explicitly require visible blood/injury; the word `혈액` as stored material does not authorize a bleeding action

Unsupported physical novelty: `ABSTAIN__PHYSICAL_AFFORDANCE_MISMATCH`.

### 8.6 PLANT_PAYOFF coherence veto

PLANT_PAYOFF advisory use requires all of the following:
1. case `long_horizon_affordance=true`;
2. novelty includes at least one coherent lifecycle atom from `PLANT`, `PAYOFF`, `COMPLETE`, `CALLBACK`, `REACTIVATION`, or `LONGER_SPAN`;
3. the case terms include an explicit persistent obligation/object relation such as 약속, 협약, 계약, 유언, 서약, 의무, 보상, 보관, 상속, 후원, 기부, 소유, 회수;
4. generic `ESCALATION` alone is insufficient.

Failure of any condition → `ABSTAIN__LIFECYCLE_COHERENCE_FAIL`.

### 8.7 ENSEMBLE_OWNERSHIP gate

Ensemble novelty is legal only when:
- ENSEMBLE_OWNERSHIP is a target axis; and
- the case premise explicitly contains at least three distinct actor groups or institutions.

Only one new ownership/role atom may be realized. Additional role novelty is discarded under the novelty budget.

### 8.8 Novelty Budget / Minimal Sufficient Signature

After all vetoes:
- maximum realized novelty atoms per plan = 2;
- maximum realized novelty atoms in one modified sequence = 2;
- if more than 2 atoms survive, keep the two highest case-relevance scores;
- ties are resolved by the fixed per-axis order listed in Sections 8.4–8.7, never by outcome inspection;
- if only one atom is sufficient to change the target sequence function, realize one and discard the rest;
- every discarded atom is logged.

No plan may display the entire raw novelty signature merely because it is available.

### 8.9 Realization contract

The selected minimal novelty may alter only the preregistered sequence function for its target axis:
- CHARACTER_STATE → S5 decision/state reversal
- RELATIONSHIP_PRESSURE → S2 relationship/access condition
- CAUSAL_ESCALATION → S4 cause→pressure→decision link
- ENSEMBLE_OWNERSHIP → S4/S6 decision-owner allocation, one ownership change only
- PHYSICALIZATION → S3 visible verification action
- PLANT_PAYOFF → S1 obligation/plant + S6 payoff/handoff

Realization must change an event function or visible action, not append bracketed labels or token names to otherwise identical prose.

## 9. Eligibility and selection

A case is qualification-eligible only if:
1. Treatment retrieval contains additive DB64-native exposure;
2. protected baseline is identical across arms;
3. after A2R32 veto/budget rules, Control and Treatment effective advisory decisions differ canonically in either USE/ABSTAIN, target axis, or minimal realized novelty set;
4. both plans pass the mechanical contract.

Select the **first 12 eligible cases in frozen A32C01→A32C24 order**.

If fewer than 12 cases are eligible: `FAIL_PREBLIND__INSUFFICIENT_ELIGIBLE_CASES`.

No replacement case may be chosen based on quality judgment.

## 10. Mechanical gates before blind evaluation

Required:
- 12 selected pairs exactly;
- 24 plans exactly;
- 6 sequences per plan;
- protected baseline identity 4/4 for every pair;
- at most 1 USED advisory per plan;
- novelty budget violations = 0;
- physical-affordance violations = 0;
- lifecycle-coherence violations = 0;
- source/identity leaks = 0;
- critical state/causal contradiction = 0;
- materially distinct plan pairs >= 9/12.

Failure → close PREBLIND; do not create mapping.

## 11. Blind protocol

Only after plan bytes and mechanical receipt are immutable:
1. create a fresh balanced 6/6 Treatment-A/Treatment-B secret mapping;
2. do not expose mapping contents;
3. build A/B packet stripped of source identities and internal utility scores;
4. judge 12 pairs using the same planning-quality rubric family used by A2R31;
5. allow TIE; do not force a winner;
6. seal blind judgment bytes before opening mapping;
7. unblind only after judgment seal verification.

## 12. Planning-quality rubric

Blind preference considers:
- causal coherence;
- case-specific event organicness;
- character-state continuity;
- relationship pressure;
- ensemble decision ownership;
- escalation clarity;
- future-thread sustainability;
- physical playability;
- absence of abstract novelty clutter;
- absence of case-unsupported action injection.

## 13. Frozen PASS gate — unchanged

A2R32 PASS requires all:
- Treatment wins >= 7/12
- Treatment nonloss >= 10/12
- Treatment losses <= 2/12
- mechanical gates all PASS
- critical provenance/identity violation = 0

Thresholds may not be lowered after outputs.

## 14. Claim boundary

A PASS would qualify the **internal full-planning DB64 interface** under this utility-control policy as one Level-3 Entry Qualification sub-gate.

It would NOT by itself:
- enter Level 3;
- promote DB64 to Production DB;
- promote Active Engine;
- promote ENG:R47;
- increment Formal count;
- complete E3/E4/E5/E6;
- authorize Level 4.

## 15. Runtime / custody rule

Current runtime state at preregistration: repeated `TransportTimeoutError` in container and Python execution layers.

Therefore status is:

`PREREGISTERED__OUTPUTS_0__RUNTIME_HOLD`

No retrieval output, plan output, secret mapping, blind packet, judgment, or result may be created until:
1. runtime executes a minimal command successfully;
2. fresh pool bytes are SHA256-sealed;
3. this preregistration is SHA256-sealed;
4. implementation code is frozen and hashed;
5. all frozen parent scorer/abstraction components are byte-reverified.

The Git commit containing this preregistration is the pre-runtime immutable custody record. A SHA256 seal must be added after runtime recovery and before scientific outputs.

## 16. Fail-closed rule

If runtime fails again after outputs begin, stop at the last physically sealed boundary. Do not reconstruct missing mappings or judgments from memory.

Status token:

`A2R32_PREREGISTERED__OUTPUTS_0__PRE_LEVEL3_E2__UTILITY_CONTROLLED_MINIMAL_NOVELTY__RUNTIME_HOLD`
