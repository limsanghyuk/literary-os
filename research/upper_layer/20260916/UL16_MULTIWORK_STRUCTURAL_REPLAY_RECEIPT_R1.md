# UL-16 Multi-work Cutoff-Safe Structural Replay Receipt R1

Date: 2026-09-16
Status: `PASS__12_OF_12__STRUCTURAL_METROLOGY_REPLAY_ONLY__NO_AUTHORITY_CHANGE`
Parent: `research/upper_layer/20260916/UL16_MAIN_PATH_INTEGRATION_RECEIPT_R1.md`
Execution protocol: `handoff/20260916/RUNTIME_CONTAINER_HUB_TURN_BOUNDED_EXECUTION_PROTOCOL_R5.md`

## 1. Purpose
Run one R5-bounded multi-work structural replay against the integrated `ADAPTIVE_UL16` Candidate route using only small hash-bound derived evidence. The full DB64 physical corpus was not reopened.

## 2. Evidence boundary
Inputs used:
- UL-16 research runtime package SHA256: `c1dfda09c97771f56aa88adc402c8fe05a03c0fd2b93205b83dafdc8d2101441`.
- 61-work Learning Bundle SHA256: `288a901bd1096e789bc914b810e0b2713bcb8403af2a9746e9fd897b166bf197`.
- Quality-evaluation member: `DB_MIRROR/DB64_R108_PRINCESS_MAN_61WORK_QUALITY_EVALUATION_R7_20260912.json`.

The replay used only these work-level structural fields:
`work_id / episodes / sequences / runtime_scenes / cast_entries / thread_axes / thread_endpoints / quality_score`.

Forbidden:
- target episode event content;
- target dialogue or scene text;
- hidden future plot content;
- post-cutoff semantic donors.

Therefore this is a **STRUCTURAL/METROLOGY replay**, not a semantic historical continuation replay and not literary-quality evidence.

## 3. Frozen preregistration
Selected 12-work stratified panel:
1. 공주의남자
2. 대물
3. 식객
4. 마지막전쟁
5. 신사의품격
6. 38사기동대
7. 미생
8. 성균관스캔들
9. 검사프린세스
10. 가을동화
11. 1프로의어떤것
12. 닥터챔프

Selection was frozen before Candidate outputs to cover low/medium/high structural profiles in sequence density, scene density, cast density and thread-axis burden.

Prereg object hash:
`1ff5e1bc476fe9582da3043879707d8df9e71197f79229bd7b50996c83e3820f`

Prereg file SHA256:
`25b1f0e89a32cf5b92e37a8e70afaafba36b1fcff4c6d4de36ebaaab1622f369`

Primary gates were frozen as:
- 12/12 work PASS;
- Canonical IR PASS 12/12;
- Adaptive validation PASS 12/12;
- total due loss = 0;
- total deferred loss = 0;
- false deferred fulfillment = 0;
- future-source use = 0;
- at least 3 distinct output sequence counts;
- at least 6 distinct output scene counts;
- Spearman correlation between source-derived structural workload and Candidate scene budget >= 0.60;
- broadcast sequence floor >= 9 for every fixture;
- broadcast scene floor >= 46 for every fixture.

## 4. Fixture derivation
Each work produced an abstract cutoff-safe current-state fixture. No drama-specific future semantics were synthesized.

Deterministic workload shaping:
- owner count from cast-per-episode;
- open-thread count from log-scaled thread-axis burden;
- information obligation count from sequence density;
- payoff count from thread endpoints per episode;
- relationship-pair count from owner burden;
- due/defer counts from sequence and thread burden.

All statements were neutral abstract placeholders keyed only by fixture IDs. The `ADAPTIVE_UL16` automatic current-state obligation compiler was used; final Episode/Sequence/Scene plans were not manually supplied.

Fixture-manifest object hash:
`d491edf3a22299b9d8704aab1aa57928ff0eec96147478417c34638d0357d404`

Fixture file SHA256:
`27e62a034f077920feb6b1d01a06186bc2ea060e19d66673931ddde97bc1b520`

## 5. Result
Overall: **PASS — all preregistered gates passed.**

Aggregate:
- works: 12;
- work PASS: 12/12;
- due loss: 0;
- deferred loss: 0;
- false deferred fulfillment: 0;
- future-source use: 0;
- unique sequence counts: `9, 10, 11, 12, 13, 17, 19`;
- unique scene counts: `77, 79, 81, 83, 86, 91, 101, 103, 105, 115, 135, 138`;
- output sequence range: 9..19;
- output scene range: 77..138;
- source-structural-load vs Candidate scene-budget Spearman rho: **0.8392**;
- Canonical validation errors: 0 across all 12 fixtures.

Per-work output:
| Work | Seq | Scenes | Weaving | Scene range | Result |
|---|---:|---:|---:|---:|---|
| 공주의남자 | 12 | 101 | 0.833 | 4..11 | PASS |
| 대물 | 9 | 86 | 0.778 | 6..12 | PASS |
| 식객 | 9 | 79 | 0.667 | 4..11 | PASS |
| 마지막전쟁 | 10 | 81 | 0.700 | 4..11 | PASS |
| 신사의품격 | 11 | 91 | 0.545 | 4..11 | PASS |
| 38사기동대 | 11 | 103 | 0.727 | 4..12 | PASS |
| 미생 | 17 | 135 | 0.765 | 4..11 | PASS |
| 성균관스캔들 | 19 | 138 | 0.579 | 4..12 | PASS |
| 검사프린세스 | 13 | 115 | 0.692 | 6..12 | PASS |
| 가을동화 | 13 | 105 | 0.538 | 4..12 | PASS |
| 1프로의어떤것 | 9 | 77 | 0.778 | 5..11 | PASS |
| 닥터챔프 | 11 | 83 | 0.636 | 4..10 | PASS |

Result object hash:
`d5bab230faf54922f567137475b567bc7706dee5205bb43fd21b167e429f02e4`

Result file SHA256:
`18cb39ca54c97e81707c20bc5df2dd0882dff5c97b4ed90b4c81cebff24acd53`

## 6. Runtime health delta
R5 precheck:
- cgroup `memory.events max = 117`;
- OOM = 0;
- OOM-kill = 0.

After replay:
- `memory.events max = 117`;
- delta = 0;
- OOM = 0;
- OOM-kill = 0.

No new memory-pressure HOLD was triggered.

## 7. Interpretation
This closes one specific uncertainty: the integrated UL-16 planner does not collapse diverse structural workloads back into one 9-sequence/fixed-scene template. It responds to the frozen structural burden across multiple works while preserving due/defer integrity and Canonical IR validity.

It does **not** prove that the resulting Episode/Sequence/Scene content is dramatically good. The fixtures intentionally contain no target semantics. Therefore the next required transaction is a semantic architecture audit of relationship/social-ecology/ensemble preservation and Scene Transaction quality using cutoff-safe, hash-bound inputs.

## 8. Authority impact
None.

Unchanged:
- Physical baseline: `SYNC-R53`;
- Production: `ENG:R47`;
- Candidate Base authority: `P07-I4H Recovery R3`;
- DB runtime authority: `DB59 frozen`;
- DB64: research-support candidate only;
- Formal total: 137; latest R138; R140 0/0/0.

## STATUS TOKEN
`UL16_MULTIWORK_REPLAY__12_OF_12_PASS__SEQ_9_TO_19__SCENES_77_TO_138__WORKLOAD_RESPONSE_RHO_0_8392__DUE_DEFER_ZERO_LOSS__FUTURE_SOURCE_ZERO__NEXT_SEMANTIC_ARCHITECTURE_AUDIT__NO_AUTHORITY_CHANGE`