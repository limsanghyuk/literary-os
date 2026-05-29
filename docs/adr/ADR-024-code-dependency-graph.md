# ADR-024: CodeDependencyGraph — Script-Level Coupling Analysis (Phase 4 GIG SP2)

**Status:** Accepted  
**Date:** 2026-05-17  
**Versions:** V531 ~ V534  

---

## Context

Phase 4 SP1 (V526–V530) introduced the NarrativeGraphStore and Gate26, which analyse
the *story-level* blast radius of a scene change (character arcs, reveals, foreshadows).
However, SP1 does not model *script-level coupling* — the structural dependencies that
arise from two scenes sharing characters, locations, props, or plot threads in the
screenplay.

A script revision tool needs both layers:

1. **Narrative graph** — does this scene change break story causality?
2. **Code dependency graph** — does this scene change require edits to other structurally
   coupled scenes?

---

## Decision

Introduce `literary_system/graph_intelligence/sp2/` with four modules:

### V531 — CodeDependencyGraph (`code_dependency_graph.py`)
Infers scene-to-scene coupling from structured metadata:

| Coupling source       | Weight per occurrence | Cap  |
|-----------------------|-----------------------|------|
| Shared character      | +0.30                 | 0.60 |
| Same location         | +0.20                 | —    |
| Shared prop           | +0.10                 | 0.20 |
| Shared plot thread    | +0.30                 | 0.60 |
| Explicit dependency   | 1.00 (override)       | —    |

`build()` is idempotent. Querying before `build()` raises `RuntimeError`.

### V532 — StagePatchImpactCalculator (`stage_patch_impact_calculator.py`)
Combines narrative risk (NarrativeImpactAnalyzer) and coupling risk (CodeDependencyGraph)
into a single `StagePatchImpact`:

```
combined_risk = min(
    narrative_risk × 0.60
  + coupling_risk  × 0.40,
  1.0
)
```

Patch type multipliers: EDIT=1.0, DELETE=1.5, REORDER=0.6, INSERT=0.2

### V533 — PlanBuildProtocol (`plan_build_protocol.py`)
Orchestrates the three-phase workflow:

```
PLAN  → StagePatchImpactCalculator (abort if combined_risk >= abort_threshold)
BUILD → Gate26 + Gate27 pre-check (abort if either fails)
GATE  → build_fn() + post-verify (re-run both gates after build)
DONE
```

`build_fn` is injected by the caller, keeping the protocol LLM-0 and
independent of any specific scene editor implementation.

### V534 — Gate27 (`gate27.py`)
Code dependency gate (complements Gate26):

| Check  | Metric                    | Threshold |
|--------|---------------------------|-----------|
| G27-1  | `direct_coupled_count`    | ≤ 10      |
| G27-2  | `max_coupling_score`      | ≤ 0.80    |
| G27-3  | `coupling_risk`           | ≤ 0.70    |

---

## Consequences

### Positive
- Scene modifications are now gated by both story causality (Gate26) and
  structural coupling (Gate27) before execution.
- `PlanBuildProtocol` provides a single entry point for the full approval chain.
- All four modules are LLM-0 compliant.
- `CodeDependencyGraph.build()` runs in O(n²) pairs — acceptable for typical
  drama episode scene counts (<200 scenes).

### Negative / Trade-offs
- Coupling inference is metadata-driven; it cannot detect semantic coupling
  (two scenes that thematically echo each other without sharing characters).
- `CodeDependencyGraph` is in-memory; persistence deferred to SP3+.
- The 60/40 narrative/coupling weighting is hand-tuned; empirical calibration
  is future work (see ADR-025).

---

## Related ADRs

- ADR-023: NarrativeGraphIntelligence (Gate26, SP1)
- ADR-015: LLM-0 Compliance Policy
- ADR-014: SceneNecessity Policy
