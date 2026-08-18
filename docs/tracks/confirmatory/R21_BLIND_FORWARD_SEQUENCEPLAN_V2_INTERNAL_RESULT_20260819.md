# R21 Blind Forward SequencePlan V2 — Internal Result (2026-08-19)

**Status:** `PASS_INTERNAL_BENCHMARK_WITH_LIMITATIONS`  
**Not:** independent causal certification / formal CT PASS.

Drama data/method authority is `limsanghyuk/v1700-literary-os` R21. This engine-side note records the planning result and its implications.

## Design
Fresh valid targets: 강남엄마따라잡기 EP09, 굿캐스팅 EP09, 녹두꽃 EP09. Target SOURCE/target Plan were hidden until 9 outputs were SHA-frozen.

Arms:
- B: N-1 state -> SequencePlan direct.
- C: N-1 state -> autonomous EpisodeSynopsisPlanLite -> SequencePlans.
- D: C + top-5 cross-work EpisodePlan retrieval, abstract/recombine before planning.

One initial 뉴하트 target was discarded before valid generation because it surfaced in another target's retrieval. Raw R5 target path/hash references also triggered blind guard before generation; these non-semantic references were removed while holdout remained sealed. Final three targets all passed blind guard.

## Scores
- B median 71
- C median 76
- D median 77
- C-B +5
- D-B +6
- D-C +1
- D >= B on 3/3 targets

Preregistered internal pilot rule passed.

Deterministic diagnostics:
- mean absolute Sequence-count error: B 1.00 -> C 0.33 / D 0.33
- exact canonical thread F1: B .427 -> C .442 -> D .394
- high-specificity retrieval story/event/dialogue copy: 0

## Interpretation
The clearest gain is **EpisodeSynopsisPlan-first hierarchy**, not retrieval itself. C improves B by +5 median and sharply reduces Sequence-count error. D passes the combined-stack pilot but adds only +1 over C and worsens exact thread F1.

Important misses:
- 강남엄마따라잡기: the actual high-cost choice `교육비 압박 -> 노래방 도우미 노동 -> hidden-labor emotional cost` was not selected.
- 녹두꽃: the actual escalation `artillery -> night sniper -> decoy -> brother shooting encounter` was replaced by a plausible but lower-escalation post-victory governance design.

This identifies two next bottlenecks:
1. high-cost / irreversible choice candidate generation,
2. escalation-level prediction.

## Historical relation
Do not compare old 2026-08-11 SequencePlan score 86 numerically to current D median 77; targets, schema and rubric differ. The new evidence is the within-experiment B->C/D improvement on three new blind targets.

## Next
- improve retrieval representation around state/debt/function/escalation/relationship transition,
- run 0/5/10/20/38-work retrieval scaling on fresh targets,
- independent scorer separation,
- then 3-episode rollout.

Full report/machine verdict are in `v1700-literary-os`:
- `R21_BLIND_FORWARD_SEQUENCEPLAN_V2_RESULT_20260819.md`
- `R21_BLIND_FORWARD_SEQUENCEPLAN_V2_VERDICT_20260819.json`
