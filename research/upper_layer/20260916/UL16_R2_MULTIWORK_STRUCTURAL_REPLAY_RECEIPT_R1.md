# UL-16 R2 Multi-work Cutoff-Safe Structural Replay Receipt R1

Date: 2026-09-16
Status: `PASS__12_OF_12__CURRENT_UL16_R2__STRUCTURAL_METROLOGY_REPLAY_ONLY__NO_AUTHORITY_CHANGE`
Parent: current UL-16 R2 Main-Path research integration authority.
Execution protocol: R5 turn-bounded transaction with R4 atomic checkpoint rules retained.

## 1. Purpose
Qualify one narrow property of the **current** UL-16 R2 Candidate research runtime: whether structurally diverse cutoff-safe workloads from multiple works are preserved as variable Episode/Sequence/Scene architectures instead of collapsing to a fixed 9-sequence / fixed-scene template.

This transaction did not reopen the full DB64 physical corpus.

## 2. Current runtime and evidence boundary
Current UL-16 R2 research runtime:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`

SHA256:
`7f71484cd2687262d18104b3a9a5cfe727d003d7ed4b616ce8d64702b2da2ca8`

Small Learning Bundle SHA256:
`288a901bd1096e789bc914b810e0b2713bcb8403af2a9746e9fd897b166bf197`

Only work-level structural fields were consumed:
`work_id / episodes / sequences / runtime_scenes / cast_entries / thread_axes / thread_endpoints / quality_score`.

No target episode event content, dialogue, scene text, future plot content, or post-cutoff semantic donor was used.

Classification:
`STRUCTURAL_METROLOGY_REPLAY__NOT_SEMANTIC_HISTORICAL_REPLAY__NOT_LITERARY_QUALITY_EVIDENCE`.

## 3. Frozen panel and gates
The same panel, fixture derivation and thresholds used in the superseded-input R1 attempt were retained **without modification** after discovering R2 authority:

Panel:
`공주의남자 / 대물 / 식객 / 마지막전쟁 / 신사의품격 / 38사기동대 / 미생 / 성균관스캔들 / 검사프린세스 / 가을동화 / 1프로의어떤것 / 닥터챔프`.

Frozen gates:
- work PASS 12/12;
- Canonical IR PASS 12/12;
- Adaptive validation PASS 12/12;
- due obligation loss total = 0;
- deferred loss total = 0;
- false deferred fulfillment total = 0;
- future-source use count = 0;
- >=3 distinct output sequence counts;
- >=6 distinct output scene counts;
- source-derived structural workload vs Candidate scene-budget Spearman rho >= 0.60;
- every broadcast fixture sequence count >=9;
- every broadcast fixture scene count >=46.

R2 prereg object hash:
`ef756b7ad5f21a8e1a7541269dafd64379c234e6cc028f94bc19a94131503b81`

R2 prereg file SHA256:
`1b5015771625a7f2697b5cfb46c8ded20fc88def32b080cb594a0490e2608492`

## 4. Fixture integrity
Fixture derivation was unchanged from the frozen design:
- owner burden from cast-per-episode;
- open-thread burden from log-scaled thread-axis count;
- information burden from sequence density;
- payoff burden from thread endpoints per episode;
- relationship burden from owner count;
- due/defer burden from sequence/thread profile.

All fixture statements were abstract IDs and structural placeholders only.

R2 fixture-manifest object hash:
`fd74a802533939ea5fac94e23599dd4489b6030864d028f8cbe5417c535dbcd5`

R2 fixture file SHA256:
`676ea0b643c8e5f6b148b76914fae980b5132423384d77755666d0378c146a3f`

## 5. Result — all frozen gates PASS
Aggregate:
- works: 12;
- work PASS: 12/12;
- due loss: 0;
- deferred loss: 0;
- false deferred fulfillment: 0;
- future-source use: 0;
- unique sequence counts: `9, 10, 11, 12, 13, 17, 19`;
- unique scene counts: `77, 79, 81, 83, 86, 91, 101, 103, 105, 115, 135, 138`;
- sequence range: 9..19;
- scene range: 77..138;
- structural-load vs scene-budget Spearman rho: **0.8392**;
- Canonical validation errors: 0 across all 12 fixtures.

Per-work:
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

R2 result object hash:
`89b3e708dcf949b8524756ffb3508de802778605e6e2e8242e1b4be2f50dbe68`

R2 result file SHA256:
`9627c1492a93a44de532f6f976eeec319e211ec68335477b6cd87aa11194f70f`

## 6. Runtime health
Before R2 replay:
- `memory.events max = 117`;
- OOM = 0;
- OOM-kill = 0.

After R2 replay:
- `memory.events max = 117`;
- delta = 0;
- OOM = 0;
- OOM-kill = 0.

No `MEMORY_IO_PRESSURE_HOLD` was triggered.

## 7. Interpretation
This result closes a structural adoption question for current UL-16 R2: the integrated Candidate reacts to materially different multi-work structural burdens and does not collapse them into one fixed Episode/Sequence/Scene grid.

It also preserves due/defer accounting and Canonical IR validity across all 12 abstract cutoff-safe fixtures.

This does **not** establish semantic/dramatic architecture quality. Because the fixtures deliberately exclude target semantics, the next bounded transaction must inspect whether relationship, social-ecology, ensemble, information and Scene Transaction semantics are meaningfully preserved rather than merely counted.

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
`UL16_R2_MULTIWORK_REPLAY__12_OF_12_PASS__SEQ_9_TO_19__SCENES_77_TO_138__RHO_0_8392__DUE_DEFER_ZERO_LOSS__FUTURE_SOURCE_ZERO__NEXT_SEMANTIC_ARCHITECTURE_AUDIT__NO_AUTHORITY_CHANGE`