# ADR-025: Plan→Build→Gate Calibration Policy

**Status:** Accepted  
**Date:** 2026-05-17  
**Versions:** V535+  

---

## Context

Gate26 and Gate27 thresholds (V530, V534) are currently hand-tuned defaults.
As Literary OS processes real manuscripts, empirical data will accumulate on
which risk scores actually predict post-edit quality regressions. This ADR
establishes the policy for how gate thresholds will be calibrated over time.

---

## Decision

### Calibration cadence
Gate thresholds are reviewed every **50 manuscripts processed** or **quarterly**,
whichever comes first.

### Calibration inputs
1. `NarrativeImpactReport.risk_score` vs. observed quality delta (human rating)
2. `StagePatchImpact.combined_risk` vs. post-edit NIL loop reward signal
3. False-positive rate (gates that blocked a safe edit)
4. False-negative rate (gates that approved an edit that degraded quality)

### Threshold adjustment rules
- Lower a threshold only if false-negative rate > 5% over the calibration window.
- Raise a threshold only if false-positive rate > 20% over the calibration window.
- Weight adjustments (_W_NARRATIVE, _W_COUPLING) require sign-off from at least
  two architecture reviewers.

### Override mechanism
Individual projects may override default thresholds at `SceneChangePreGate` and
`Gate27` instantiation. Overrides must be documented in the project's `config.yaml`
under `gate_overrides:`.

### Risk formula coefficient freeze
The current risk score formula coefficients (ADR-023, ADR-024) are frozen until
the first calibration review. No ad-hoc adjustments are permitted during the
V535–V540 development window.

---

## Consequences

- Provides a structured path to empirically grounded gate thresholds.
- Prevents premature optimisation of coefficients before data is available.
- Per-project overrides allow flexibility without polluting global defaults.

---

## Related ADRs

- ADR-023: NarrativeGraphIntelligence
- ADR-024: CodeDependencyGraph
