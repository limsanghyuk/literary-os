# CT-07R preregistration amendment v1.1.1 — equal-density target-slot materialization

Document ID: `LOS-CT07R-PREREG-AMENDMENT-V1.1.1`  
Date: 2026-08-07  
Status: `PRE_SCORE_CORRECTION / NO_RENDER_OR_SCORE_OBSERVED`  
Parent: v1.0 preregistration + amendment v1.1

## 0. Problem found during implementation audit

Amendment v1.1 correctly removed visible donor identity, but its provisional rule allowed empty TN `scene_notes` target slots when donor scene count `D` was smaller than target count `T`.

That creates another non-semantic cue: TN can contain less per-scene design information solely because donor and target sequence lengths differ. In this replication set the mismatch can be large (for example a 3-scene donor applied to a 9-scene target), so `T > TN` could partly measure payload density rather than semantic fit.

No render or score has been observed. The frozen semantic donor mapping and all thresholds remain unchanged.

## 1. Superseded rule

The v1.1 sentence allowing unmapped target slots to contain an empty proposition list is superseded.

## 2. Active equal-density rule

For TN `scene_notes`, every target slot `j=1..T` receives exactly one donor scene-note proposition list selected by nearest normalized position:

```text
if T == 1: donor_index = 1
elif D == 1: donor_index = 1 for every target slot
else: donor_index = 1 + round((j-1) * (D-1) / (T-1))
```

Rules:

- preserve selected donor `functional_propositions` text verbatim;
- repetition is allowed when `D < T`;
- sampling is allowed when `D > T`;
- do not synthesize, summarize, interpolate, or rewrite donor meaning;
- output always contains exactly `T` target-relative `scene_notes` slots;
- T arm uses the same target-relative slot count.

This equalizes per-scene structural coverage while preserving semantic mismatch.

## 3. info_shift / plant_payoff scene-slot mapping

For donor-local scene references, map each donor ordinal `i=1..D` to its nearest target-relative position:

```text
if D == 1: target_slot = 1
elif T == 1: target_slot = 1
else: target_slot = 1 + round((i-1) * (T-1) / (D-1))
```

Deduplicate mapped slots in ascending order. This remaps only indices; semantic text is unchanged.

## 4. Density audit required

Before rendering, materializer must report per target:

- T/TN number of scene-note slots (must be equal),
- T/TN number of nonempty scene-note slots (must both equal target slot count),
- semantic source packet ID retained only in a private orchestration manifest, never renderer payload.

A payload failing these checks cannot be rendered for the confirmatory result.

## 5. Change control

This v1.1.1 amendment is pre-score and removes a structural-density confound. It does not alter works, anchors, donor rotation, semantic donor content, endpoint, thresholds, or decision rules.
