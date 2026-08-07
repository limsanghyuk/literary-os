# CT-07R preregistration amendment v1.1 — pre-score control deconfounding

Document ID: `LOS-CT07R-PREREG-AMENDMENT-V1.1`  
Date: 2026-08-07  
Status: `PRE_SCORE_CORRECTION / NO_RENDER_OR_SCORE_OBSERVED`  
Parent preregistration: `CT-07R_2026-08-07_db98_reinforcement_replication_prereg.md`  
Authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1`  
Active schema: `DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1`

## 0. Why this amendment is necessary

The v1.0 negative-control mapping correctly froze a cyclic +1 semantic donor within each work before scoring, but its presentation contract introduced an avoidable confound: the TN arm could expose donor `episode_no`, `seq_id`, `member_scene_nos`, provenance/evidence fields, or an explicit "foreign/mismatched" label. A renderer could therefore discount TN because metadata announces that the packet belongs elsewhere, rather than because the semantic design is wrong for the target.

That would make `T > TN` insufficient evidence for semantic steering.

No renderer output or score has been observed as of this amendment. Therefore the amendment changes only the **presentation/materialization contract**, not works, anchors, semantic donor mapping, metrics, or thresholds.

## 1. Frozen items that do NOT change

The following remain exactly as preregistered in v1.0:

- works: `101번째프로포즈`, `38사기동대`;
- ten target anchors;
- correct thick packets already source-grounded and sealed;
- within-work cyclic +1 donor mapping for TN;
- A/B/T/TN arm meanings;
- primary endpoint and normalization;
- `B-A >= 0.5` validity requirement;
- overall `r_T >= 0.70` requirement;
- both-work positive-signal requirement;
- `TN < T` overall and per work;
- sensitivity reporting;
- no post-hoc anchor deletion or threshold relaxation.

## 2. Corrected renderer-facing contract

### 2.1 Archival packet vs renderer payload

The sealed ThickSequenceExtension is an **audit/provenance artifact**, not a renderer prompt payload.

Renderer-facing T/TN payloads MUST exclude:

- source paths / line ranges;
- `evidence_refs`;
- `source_hashes`;
- `by`;
- donor `work_id`, `episode_no`, `seq_id`, `seq_index`;
- CrossEpisodeEdge / PayoffCandidate IDs;
- any string that says the design is foreign, mismatched, negative, donor, wrong, control, or from another episode.

The renderer receives only intended planning semantics in a target-shaped neutral envelope.

### 2.2 Same target-shaped skeleton

For each target anchor, T and TN receive the same neutral envelope:

```text
target_slot_id
cast
 event
info_shift
plant_payoff
scene_notes[slot_1..slot_N]
```

`target_slot_id` is an opaque experiment ID, not a drama/episode/sequence identifier.

### 2.3 TN donor materialization

The semantic donor remains the v1.0 cyclic +1 packet. Only scene-position identifiers are deterministically remapped to target-relative slots so the renderer cannot identify the control from incompatible numbering.

Rules:

1. Preserve donor semantic text verbatim.
2. Preserve donor cast/event/info/plant-payoff content.
3. Remove donor provenance and identity metadata.
4. Convert donor scene notes to ordered donor slots.
5. Map donor slots to target slots by normalized ordinal rank.
   - donor slot index `i` among `D` notes maps to nearest monotonic target slot among `T` slots using normalized position `(i-1)/(D-1)`; endpoint-preserving; ties resolved to lower unused target slot then next available slot.
   - if `D > T`, multiple donor functional-proposition lists may merge into one target slot in donor order.
   - if `D < T`, unmapped target slots receive an explicit empty proposition list and MUST NOT be backfilled with target semantics.
6. Do not rewrite donor semantic sentences to fit the target.

This keeps the semantic mismatch while removing the metadata mismatch.

## 3. Independent target-function key is mandatory

Before any rendering, an independent key author must create and seal the target-function key for the ten anchor scenes.

Key-author isolation:

- may read target source and target human SceneCard;
- may read the scoring rubric/functional categories;
- MUST NOT read CT-07R correct thick packets, TN donor packets, renderer outputs, or scores;
- produces per-anchor atomic functional elements and a SHA256 seal.

The DB reinforcement author who created the thick packets must not author the scoring key after seeing those packets.

If no independent key author is available, CT-07R remains `PREPARED_NOT_MEASURABLE` and bulk rollout remains blocked.

## 4. Renderer and judge isolation

Renderer:
- sees target context permitted by the arm + sanitized arm payload only;
- never sees target-function key;
- never sees arm label semantics beyond opaque arm IDs;
- never sees another arm's output.

Judge:
- sees rendered candidate and sealed target-function key according to the scoring protocol;
- does not see whether candidate came from T or TN;
- reports raw element judgments before arm unblinding.

## 5. TG route

If TG is executed, the generated-card model receives the same sanitized planning semantics as T, not archival provenance fields. Generated cards are then rendered under the same isolation rules.

## 6. No future-information leakage in renderer payload

`plant_payoff` planning statements may be retained only to the extent needed to steer the target sequence. Renderer payload MUST strip future episode IDs, future SceneCard IDs, and provenance links. This amendment does not change the archival thick record; it changes only experimental presentation.

## 7. Packet defects and corrections

Structural/provenance typos found after sealing are not silently edited in the sealed JSONL. They are recorded in `CT07R_PACKET_AUDIT_AND_CORRECTION_LEDGER_20260807.json` and applied only to validated derived/audit copies as specified there.

## 8. Validity consequence

Any CT-07R score produced using the original v1.0 instruction that explicitly tells the renderer a TN packet is foreign/mismatched, or exposes donor identity/provenance metadata, MUST be labeled `INVALID_CONTROL_PRESENTATION` and cannot authorize DB98 rollout.

Only results produced under v1.0 + this v1.1 amendment may be used for the global rollout gate.

## 9. Change-control statement

This amendment was created before rendering/scoring. It does not alter preregistered success thresholds or donor selection. Its purpose is to remove a measurement confound discovered during packet audit.
