# ADR-023: Narrative Graph Intelligence (Phase 4 GIG — SP1)

**Status:** Accepted  
**Date:** 2026-05-17  
**Deciders:** Literary OS Architecture Board  
**Versions:** V526 ~ V530  

---

## Context

Phase 3 (V498–V525) introduced the Numerical Interaction Engine (NIE v2.0), completing
the mathematical self-reinforcement loop (NIL). The system can now generate and evaluate
scenes with physics-grounded reward signals, but it lacks **narrative causal awareness**:
it cannot anticipate how modifying a scene ripples through the story graph before
executing the change.

The "진화 방향 제시.docx" evolution document (2026-05-17) analysed the GitNexus /
OpenCode architecture and proposed applying knowledge-graph intelligence to Literary OS:
build a **Narrative Graph**, calculate a **Narrative Blast Radius** before any scene
modification, and enforce a **Plan → Build → Gate** protocol analogous to GitNexus's
code-change impact analysis.

---

## Decision

Introduce the `literary_system/graph_intelligence/` package (Phase 4 GIG — Sub-Phase 1)
comprising five LLM-0 compliant modules:

| Module | Version | Role |
|--------|---------|------|
| `narrative_graph_schema.py` | V526 | 10 node types, 10 edge types, `NarrativeImpactReport` |
| `narrative_graph_store.py`  | V527 | In-memory BFS graph with adj/radj indexes |
| `narrative_graph_indexer.py`| V528 | Translates NIL loop output (`IndexInput`) → graph mutations |
| `narrative_impact_analyzer.py` | V529 | Computes blast radius + risk score |
| `scene_change_pre_gate.py`  | V529b | Gate26 — Plan→Build approval gate |

**LLM-0 rule (ADR-015):** All five modules contain zero LLM calls. Graph traversal,
risk scoring, and gate decisions are pure Python.

---

## Node and Edge Taxonomy

### Node types (10)
`CHARACTER` · `SCENE` · `EVENT` · `SECRET` · `REVEAL` ·
`MOTIF` · `RELATIONSHIP` · `EMOTION_PRESSURE` · `TIME_DELTA` · `DIALOGUE_INTENT`

### Edge types (10)
`CAUSES` · `KNOWS` · `HIDES` · `REVEALS` · `DEPENDS_ON` ·
`CONTRADICTS` · `ESCALATES` · `RELIEVES` · `FORESHADOWS` · `ECHOES`

---

## Risk Scoring Formula

```
risk_score = min(
    direct_count   × 0.20
  + indirect_count × 0.08
  + reveal_count   × 0.30
  + foreshadow_breaks × 0.25,
  1.0
)
```

| Level    | Threshold | Decision       |
|----------|-----------|----------------|
| critical | ≥ 0.80    | hold           |
| high     | ≥ 0.55    | split_required |
| medium   | ≥ 0.30    | review         |
| low      | < 0.30    | proceed        |

Weight rationale:
- **Reveals (0.30)** carry the highest weight because a reveal's payoff is binary —
  once its setup scene changes, the payoff collapses entirely.
- **Foreshadow breaks (0.25)** are nearly as costly: a broken foreshadow is
  invisible to readers until the missing payoff scene, making it hard to diagnose.
- **Direct impacts (0.20)** are significant but recoverable via targeted edits.
- **Indirect impacts (0.08)** are weighted lightly; they are often buffered by
  intermediate nodes.

---

## Gate26 Thresholds

| Check  | Metric                   | Threshold |
|--------|--------------------------|-----------|
| G26-1  | `direct_impact_count`    | ≤ 15      |
| G26-2  | `reveal_count`           | ≤ 3       |
| G26-3  | `foreshadow_break_count` | ≤ 2       |
| G26-4  | `risk_score`             | ≤ 0.75    |

All four checks must pass for the gate to return `approved=True`.
Thresholds are overridable at `SceneChangePreGate` instantiation.

---

## Plan → Build → Gate Protocol

```
PLAN   → NarrativeImpactAnalyzer.analyze(scene_id)
BUILD  → (only if Gate26 approved) execute scene modification
GATE   → SceneChangePreGate.evaluate(scene_id) post-verification
```

This mirrors the GitNexus Plan→Build→Deploy protocol applied to narrative structure
instead of code deployments.

---

## Indexer Design

`NarrativeGraphIndexer` accepts `IndexInput` (a structured DTO mirroring NIL loop
outputs) and applies idempotent upserts to `NarrativeGraphStore`. Key properties:

- **Idempotent:** indexing the same `IndexInput` twice produces no duplicate nodes
  or edges.
- **Incremental:** callers may stream scene-by-scene as the NIL loop runs.
- **Edge deduplication:** checked by `(src_id, dst_id, edge_type)` triple before
  inserting.

---

## Consequences

### Positive
- Scene modifications are gated by quantified narrative risk before execution.
- The graph is incrementally populated from existing NIL loop outputs — no separate
  ingestion pipeline required.
- LLM-0 compliance keeps gate latency under 5 ms for graphs up to 10 000 nodes.
- Gate26 thresholds are tunable per project without code changes.

### Negative / Trade-offs
- Graph is in-memory only (V526–V530); persistence is deferred to SP2 (V531–V535).
- Risk formula coefficients are hand-tuned; empirical calibration against real
  manuscripts is future work (ADR-024).
- BFS at depth-2 may miss long causal chains in serialised narratives; depth is
  configurable but defaults to 2 for performance.

---

## Alternatives Considered

| Alternative | Rejected because |
|-------------|-----------------|
| Skip impact analysis entirely | Blind scene edits create hidden continuity errors |
| Use LLM to estimate blast radius | Violates ADR-015 LLM-0; adds latency and cost |
| Reuse GDAP `blast_radius.py` (V350) | Targets code-dependency graph; node/edge semantics differ |

---

## Related ADRs

- ADR-015: LLM-0 Compliance Policy
- ADR-022: NIL Loop Stability (Gate25)
- ADR-014: SceneNecessity Policy
