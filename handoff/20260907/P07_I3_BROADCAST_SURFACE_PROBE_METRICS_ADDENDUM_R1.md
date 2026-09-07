# P07-I3 Broadcast Surface Probe — Frozen Metrics Addendum R1

Date: 2026-09-07
Parent preregistration: `P07_I3_BROADCAST_SURFACE_BIDIRECTIONAL_DEVELOPMENT_PROBE_PREREG_R1.md`
Status: FROZEN BEFORE FIRST FULL SURFACE OUTPUT

## 1. Surface-scale gate
Use existing `BroadcastRenderQualityPreScoreGate` with:
- expected scenes = 50;
- min_chars = 35,000;
- max_chars = 45,000;
- max LONG exact dialogue duplicate ratio = 0.05;
- max long narrative paragraph exact duplicate ratio = 0.05;
- forbidden meta leakage = 0.

The 50-scene target is selected inside the already-preregistered 45–60 scene band before surface output.

## 2. Ensemble-distribution diagnostic
Primary protagonist for this synthetic development fixture: `윤서진`.
Primary protagonist-affiliated group: `구청감사팀`.
Other principal groups: `세입자연대`, `태산개발/가족회사`.

First-pass `ENSEMBLE_DISTRIBUTION_COLLAPSE` fires if BOTH are true:
1. protagonist appears in > 0.70 of scene contracts; and
2. protagonist-affiliated group owns > 0.70 of sequence-level event ownership.

A repaired version clears the targeted diagnostic only if ALL are true:
1. protagonist scene participation <= 0.65;
2. protagonist-affiliated group sequence ownership <= 0.60;
3. at least 4 of 10 sequences are owned by non-protagonist groups in total;
4. at least two non-protagonist groups each own at least one sequence;
5. episode causal/terminal contract remains valid.

These metrics do not claim an optimal artistic distribution. They are development sentinels for protagonist-collapse in this specific ensemble-heavy fixture.

## 3. Responsible ancestor
If the collapse gate fires and the first-pass ENSEMBLE_ECOLOGY_PLAN concentrates ownership in the protagonist group, the minimum responsible ancestor is frozen as `ENSEMBLE_ECOLOGY_PLAN`. The repair must change that plan and then re-lower affected Sequence/Scene descendants. Surface-only rewriting is not sufficient.

## 4. Craft/continuity diagnostics
The repaired output must additionally preserve:
- scene count 50;
- 35k–45k character band;
- no source/future leakage;
- no exact long-dialogue or long-narrative duplication above 0.05;
- no forbidden experiment/meta tokens;
- sequence ordering and episode exit pressure;
- no newly introduced unsupported principal character.

## 5. Development-only status
In-session LLM surface generation is labeled `IN_SESSION_LLM_SURROGATE__NONLIVE`. Passing these metrics is not external craft validation or Live provider evidence.
