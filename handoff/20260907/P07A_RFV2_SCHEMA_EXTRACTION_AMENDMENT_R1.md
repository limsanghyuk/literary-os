# Literary OS — P07-A RFV2 Bounded THICK Profile Field Extraction Amendment R1
Date: 2026-09-07
Classification: PREFORMAL RECOVERY AMENDMENT / PRERESULT FREEZE
Depends on: `P07A_RFV2_CONTROLLED_RECOVERY_REIMPLEMENTATION_SPEC_R1.md`

## Purpose
The interrupted-session durable record preserves `bounded THICK-derived functional profile` but does not preserve byte-identical source proving the exact field extractor. This amendment resolves that ambiguity BEFORE reconstructed retrieval results are run.

This is not result tuning. No RFV2 reconstructed six-case result has been viewed before this field contract is frozen.

## Frozen DB59 membership contract
- Frozen archive SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- Canonical source layer: `seqcard_ko/reinforcement_v1/thick_sequence/` only.
- Development target works: `101번째프로포즈`, `토마토`, `좋은사람`, `신의퀴즈1`, `스위치`, `파리의연인`.
- For these six target works, only EP01-EP05 THICK members are eligible.
- For all other works, all DB59 THICK members are eligible.
- Expected membership reference only: 1,097 member files / 10,784 JSONL records. Fresh measurement is required.
- Actual/post-cutoff target material is prohibited.

## Frozen work/sequence retrieval representation
For every eligible THICK JSONL record, retrieval representation may use ONLY the following source-safe functional fields:
1. `event` string.
2. Each `info_shift` item: `mode`, `before`, `after`.
3. Each `plant_payoff` item: `kind`, `statement`.

Explicitly excluded from retrieval vectorization/profile text:
- `scene_notes` and its prose;
- `evidence_refs`;
- `source_hashes`;
- raw source text/dialogue;
- `member_scene_nos`;
- character-name lists and cast identity fields;
- `cast.character`;
- `cast.desire_or_function`;
- record/path/authority hashes and diagnostics.

The selected donor semantic payload may retain the exact allowed functional fields above plus non-literary provenance/binding in receipts, but retrieval score/confidence/margin MUST NOT enter the literary semantic conditioning payload.

## Frozen query representation for the six development cases
Use the already-sealed E9/PRE09 development fixtures, not actual EP06 source.
Query text is deterministic concatenation from target EP06 fixture planning fields only:
- EPISODE_ALLOCATION row for episode 6: `dramatic_function`, `main_event`, `character_movement`, `relationship_movement`, `thread_movement`, `turn`, `ending_pressure`.
- EPISODE_PLAN episode 6 when present: `episode_goal`, `main_event`, `active_threads`, `required_turns`, `terminal_contract`.

No actual EP06/post-cutoff source text may be used.

## Frozen retrieval architecture
Two-stage restored R37/R38-compatible retrieval:
1. Aggregate bounded functional record profiles per work.
2. TF-IDF with `analyzer="char_wb"`, `ngram_range=(2,5)`; cosine similarity; top 4 works.
3. Re-rank eligible THICK sequence-record profiles inside those top-4 works using the same query and TF-IDF/cosine concept.
4. Select top 4 donor sequence records globally from the top-work candidate pool.
5. Confidence = top work-level cosine similarity.
6. Fit margin = top1 work score minus top2 work score; diagnostic only.
7. HIGH >= 0.13; MEDIUM >= 0.10 and < 0.13; LOW < 0.10 -> `NO_RETRIEVAL`.
8. No hard margin gate.

## Causal stability contract
- Selected donor mutation must change the literary semantic provider input when the mutated semantic donor remains selected.
- An irrelevant unselected donor mutation must not change literary semantic provider input when the selected donor set/payload is unchanged.
- Diagnostic ranking metadata is excluded from literary provider input for this negative-dependency test.

## Frozen-index contract
A Frozen Retrieval Index must be deterministically derived from the verified DB59 membership above and bind:
- DB59 SHA256;
- membership file list and per-member SHA256;
- record count and record semantic hashes;
- work profiles and donor record profiles;
- extractor version/field contract;
- index artifact hash.

Direct DB59 retrieval and Frozen Index retrieval must be compared on the six frozen development cases. Historical 6/6 is an observation, not a target.

## Result rule
Any FAIL/HOLD after this freeze is preserved. Do not change fields, thresholds, query fields, target works, or source cutoff after viewing reconstructed results.

Status token:
`RFV2_BOUNDED_THICK_PROFILE_FIELD_EXTRACTION_FROZEN_PRERESULT__NO_RESULT_INFORMED_TUNING_ALLOWED`
