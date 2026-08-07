# DB98 Reinforcement Authority Correction V1.0.2

Correction ID: `DB98_REINFORCEMENT_AUTHORITY_CORRECTION_V1_0_2`  
Date: `2026-08-07`  
Status: `ACTIVE_NONDESTRUCTIVE_CORRECTION`  
Supersedes for current interpretation: `AUTHORITY_CORRECTION_V1_0_1.md`  
Parent authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1` / method version `1.0.0`

## 0. Purpose

This correction keeps the sealed Master Authority intact while updating two items discovered before CT-07R rendering/scoring:

1. the active CT-07R control-presentation contract now includes preregistration amendment 02;
2. CT-07 metric interpretation is fixed explicitly so absolute scores and normalized `r` values are never conflated in DB98 rollout rationale.

The global Thick Sequence rollout gate remains blocked until a valid independent CT-07R result is measured and accepted by the developer.

## 1. Active reinforcement schema

The active exact reinforcement schema remains:

`schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json`

The schema hotfix history in V1.0.1 remains valid. This correction does not change Stage01–04 schemas, canonical 9-key SceneCard, or CT-07R success thresholds.

## 2. CT-07 metric interpretation — fixed terminology

The Master Authority's CT-07 table is the controlling numeric record. The following meanings must be preserved verbatim in future design/rollout documents:

- no design `A = 0.000`;
- human SceneCard `B = 1.425`, normalized anchor `r = 1.00`;
- thick → generated SceneCard → render `L2-G = 1.150`, normalized `r = 0.807`;
- thick direct render `L2-D = 2.325`, normalized `r = 1.63`;
- maximum functional-proposition design `L3 = 4.900`, normalized `r = 3.44`.

Therefore:

- `0.807` is **not** an absolute SceneCard score; it is the normalized `r` for the L2-G route.
- The absolute L2-G score is `1.150`.
- `1.63` is the normalized `r` for direct thick render L2-D; its absolute score is `2.325`.
- The measured loss from direct thick design to the generated-card route is `2.325 → 1.150` on the absolute scale, a difference of `1.175`.
- On the normalized `r` scale the same route change is `1.63 → 0.807`, a difference of approximately `0.823`.
- Human SceneCard `B` remains the normalization anchor at `r = 1.00`; it is not the same experimental arm as L2-G.

Forbidden shorthand in future authority/design documents:

> “SceneCard compression gives 0.807”

unless it is expanded to state that this refers specifically to **thick → generated SceneCard → render L2-G normalized r**, not the human SceneCard arm.

## 3. CT-07R preregistration change control

The original CT-07R preregistration §5 required TN to be explicitly presented as foreign/mismatched context. Packet audit showed that this can become a one-sided rejection cue rather than a semantic mismatch test.

The controlling pre-render/pre-score experiment chain is now:

1. `docs/tracks/confirmatory/CT-07R_2026-08-07_db98_reinforcement_replication_prereg.md`
2. `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1.md`
3. `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1_1.md`
4. `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_02_neutral_context_and_equalized_control.md`
5. `docs/tracks/confirmatory/CT07R_RENDER_PAYLOAD_CONTRACT_V1_0_2.json`
6. `tools/experiments/build_ct07r_sanitized_payloads.py`
7. `docs/tracks/confirmatory/ct07r_packets/CT07R_PACKET_AUDIT_AND_CORRECTION_LEDGER_20260807.json`

Amendment 02 explicitly supersedes only the original §5 **renderer presentation sentence**. The frozen within-work cyclic +1 TN semantic donor mapping remains unchanged.

## 4. T/TN neutral-context rule

Both T and TN must receive the same literal notice:

`이 설계 맥락은 검증되지 않았을 수 있다.`

No renderer-facing text may identify either arm as correct, foreign, mismatched, wrong, donor, negative, or from another episode.

At the same time, this is not deception of the audit system: the true target/donor/arm mapping remains sealed in the private orchestration manifest and is used only after blind rendering/scoring.

## 5. T/TN equal-density rule

For a given target anchor:

- T and TN must use the same target-shaped envelope;
- both must have exactly the target sequence's `N` scene-note slots;
- all scene-note slots must be nonempty;
- donor semantics may be repeated/sampled by the frozen normalized-position rule when donor and target scene counts differ;
- donor semantic prose may not be rewritten to fit target meaning.

Thus `T > TN` is intended to test semantic fit rather than payload length, scene-slot count, or visible source identity.

## 6. Independent target-function key state

The developer reports that isolated local target-function keys have been authored and sealed under:

`C:\claude\CT07R_run_20260807\keys\`

with reported SHA256 prefixes:

- `f456a957…`
- `16719be5…`

These files are **not hub-sealed evidence** until their exact bytes are uploaded and full SHA256 values are recorded in the repository. The DB reinforcement/thick-packet author must not recreate or paraphrase them from chat or memory.

Until upload, hub state must distinguish:

`LOCAL_REPORTED_COMPLETE / HUB_UNSEALED`

from

`HUB_SEALED_INDEPENDENT_KEY`.

## 7. Short-anchor sensitivity

The developer reports a separately sealed local amendment/analysis:

`C:\claude\CT07R_run_20260807\CT-07R_amendment_01_short_anchor_sensitivity.md`

The hub must not invent its contents. Once uploaded, it becomes part of the CT-07R reporting chain. The already stated sensitivity categories are retained as reported requirements, but the exact local document remains external until byte-for-byte ingestion.

Anchor reselection is not authorized.

## 8. Next authoritative action

The next action is:

```text
INGEST_LOCAL_INDEPENDENT_KEYS_AND_SHORT_ANCHOR_AMENDMENT
→ verify full SHA256 and provenance
→ run materializer under render contract V1.0.2
→ seal sanitized T/TN payload SHA256
→ prepare A/B/T/TN 40-render blind batch
→ independent blind render
→ shuffle
→ independent 3-judge scoring
→ unblind
→ apply unchanged preregistered thresholds
→ report mandatory sensitivity analyses
→ developer accepts PASS/FAIL
```

No full 98-work Thick Sequence semantic rollout is authorized before valid PASS + developer acceptance.

## 9. New-session precedence

For DB98 reinforcement, current read order is:

`root pointer → Master Authority → Authority Correction V1.0.2 → active exact schema → schema changelog → execution/validation → CT07R current status → work index → bootstrap`.

`AUTHORITY_CORRECTION_V1_0_1.md` remains historical and audit-readable but is superseded for current interpretation by this document.
