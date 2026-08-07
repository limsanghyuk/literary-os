# CT-07R preregistration amendment 02 — neutral context symmetry for T/TN

Document ID: `LOS-CT07R-PREREG-AMENDMENT-02`  
Date: 2026-08-07  
Status: `PRE_RENDER_PRE_SCORE_DESIGN_CHANGE / NO_RENDER_OR_SCORE_OBSERVED`  
Parent preregistration: `CT-07R_2026-08-07_db98_reinforcement_replication_prereg.md`  
Related pre-score amendments: `CT-07R_2026-08-07_prereg_amendment_v1_1.md`, `CT-07R_2026-08-07_prereg_amendment_v1_1_1.md`

## 0. Why amendment 02 is required

The original preregistration §5 required the TN runner to present the mismatched thick packet explicitly as foreign/mismatched context. That protected against pretending a known-false plan was a valid target plan, but it creates a measurement confound: a renderer can discount TN from the label alone without testing the semantic content.

A second pre-render audit also confirmed large source packet scene-note count differences (for example, 3 notes versus 14 notes). If T and TN reach the renderer with unequal target-slot coverage or information density, `T > TN` can measure quantity rather than semantic fit.

No render and no score have been observed. Therefore this is a preregistered design change before measurement, not a post-hoc threshold or sample change.

## 1. Frozen items that do not change

The following remain exactly frozen:

- two works;
- ten anchors;
- A/B/T/TN arm definitions;
- source-grounded correct thick packets;
- within-work cyclic +1 TN semantic donor mapping;
- target-function scoring concept;
- batch validity `B-A >= 0.5`;
- overall `r_T >= 0.70`;
- both-work positive-signal requirement;
- `TN < T` overall and per work;
- no post-hoc anchor deletion;
- all preregistered sensitivity reporting;
- decision thresholds and rollout consequence.

## 2. Supersession of original §5 presentation sentence

The original §5 sentence requiring the runner to present TN **explicitly as foreign/mismatched design context** is superseded for renderer presentation only.

The semantic fact remains true in the private orchestration record: TN is the frozen cyclic +1 mismatched donor. The renderer must not receive a one-sided label that reveals that fact.

## 3. Symmetric neutral notice

T and TN MUST receive the same literal neutral notice before the planning payload:

> 이 설계 맥락은 검증되지 않았을 수 있다.

Rules:

1. The sentence must be byte-identical for T and TN.
2. No additional text may identify T as correct or TN as foreign, mismatched, wrong, negative, donor, or from another episode.
3. The notice does not authorize the renderer to ignore the design; it only prevents asymmetric truth-status signaling.
4. The private blind/orchestration map retains the actual arm and donor identities and is never exposed to the renderer.

This satisfies the original anti-deception intent without creating a one-sided rejection cue.

## 4. Equalized target-shaped payload

T and TN must be materialized into the same target-shaped structure and target scene-slot count.

Required renderer-facing design fields:

- identical neutral notice;
- opaque `target_slot_id`;
- `cast`;
- `event`;
- `info_shift`;
- `plant_payoff`;
- `scene_notes[slot_1..slot_N]`.

For each anchor:

- T and TN have exactly the same `N` target slots;
- every slot contains a nonempty functional-proposition list;
- donor identity/provenance is removed from both renderer payloads;
- TN semantic sentences are not rewritten to fit target meaning;
- when donor and target scene counts differ, use the already preregistered nearest-normalized-position repetition/sampling rule from amendment v1.1.1.

Thus the control comparison is intended to differ in **semantic fit**, not label, source identity, scene numbering, or payload density.

## 5. Short-anchor sensitivity remains mandatory

Anchor selection is not reopened. Re-selecting anchors after discovering short source spans would be post-selection and is forbidden.

The previously frozen short-anchor sensitivity protocol must be reported with the main result when its sealed document/key is ingested to the hub. At minimum the report must preserve the already defined analyses:

- 6-line-or-longer subset;
- leave-one-out minimum/maximum result;
- within-scene versus placement/neighbor-relation functional-element decomposition;
- all ten anchors in the primary result regardless of sensitivity findings.

This amendment does not alter the primary PASS/FAIL thresholds.

## 6. Independence and key ingestion

The independent target-function keys reportedly authored in the isolated local session are not considered hub-sealed until the exact files are uploaded without semantic transformation and their full SHA256 values are recorded in the hub status/manifest.

The thick-packet author must not recreate, paraphrase, or fill missing key content from memory.

## 7. Validity rule

A CT-07R measurement is invalid for rollout authorization if any of the following occurs:

- T and TN receive different truth-status notices;
- TN is explicitly identified as mismatched/foreign/wrong to the renderer;
- T/TN target-slot count or nonempty scene-note coverage differs for the same anchor;
- the renderer receives donor/source/provenance identifiers that reveal arm identity;
- the target-function key is authored or repaired by the thick-packet author after seeing the thick packets;
- any preregistered threshold is changed after observing render or score results.

## 8. Change-control statement

Amendment 02 is sealed before any render or score. It changes presentation symmetry and density control only. It does not change semantic donor mapping, anchors, endpoints, thresholds, or the global rollout gate.
