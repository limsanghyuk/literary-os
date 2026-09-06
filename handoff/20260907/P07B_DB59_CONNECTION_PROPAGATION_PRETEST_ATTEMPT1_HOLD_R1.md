# Literary OS — P07-B DB59 Connection & Propagation Pretest Attempt 1 HOLD R1
Date: 2026-09-07
Classification: NONFORMAL_PREFORMAL_CONFIRMATORY_MECHANICAL_REVALIDATION
Preregistration: `handoff/20260907/P07B_DB59_CONNECTION_PROPAGATION_PRETEST_PREREG_R1.md`
Prereg commit: `8dc5fe14ce2163e4a0bbb621ce6127d6808977bb`
Starting authority: `CURRENT_PHYSICAL_AUTHORITY__P07A_RFV2_CONTROLLED_RECOVERY_R1`
Formal count delta: 0
R140 attempts delta: 0

## Attempt-1 verdict
`HOLD__RUNTIME_BATCH_RETRIEVAL_DONOR_SELECTION_DRIFT`

## Fresh PASS observations before HOLD
- all 9 current package SHA256 values reverified against current Manifest/Trust Root;
- C2-A || C2-B streamed reconstruction matched current C2 SHA256 `1a9355169650d66af0a3f44fb867bad1c00e5dc643e8f28443d1b2f6c6cde62d`;
- D1/D2 internal DB59 split reassembled to exact frozen DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`;
- fresh Direct DB59 index: 1,097 eligible THICK members / 10,784 records;
- fresh Direct Index body hash `3bb3ba9b9d94ddca32b1e25d68cae8990340d4d97c61edd5f427ef31f8c0b215`;
- fresh Direct Index file SHA256 `e13b55f940ad3395e6db2a63829cc70e4754acd7438104ee2aba1ee07b0905cb` exactly matched the currently packaged Frozen Retrieval Index file SHA;
- six sealed E9 semantic fixtures regenerated the expected six query SHA256 values exactly;
- Direct `retrieve_many()` 6/6 decisions = `USE_RETRIEVAL`;
- Frozen `retrieve_many()` 6/6 decisions = `USE_RETRIEVAL`;
- Direct/Frozen `retrieve_many()` decision + donor IDs + literary payload hashes matched 6/6.

## HOLD defect discovered
The actual semantic runtime path `run_verified_hierarchical_semantic_planning()` calls `rfv2_retrieval.retrieve()`, while six-case/batch evidence uses `rfv2_retrieval.retrieve_many()`.

These two functions currently implement different donor reranking:
- `retrieve()` ranks all sequence candidates from the selected top works in one combined local TF-IDF/cosine space;
- `retrieve_many()` builds a separate local vectorizer per selected work, keeps the best two per work, then globally chooses top donors.

The per-work two-donor quota is not part of the frozen historical recovery wording. On CASE-01, the sealed batch donor set and actual runtime donor set differ.

Sealed batch CASE-01 donors begin:
- `...101번째프로포즈_05...::11`
- `...시크릿가든_19...::3`
- `...101번째프로포즈_01...::10`
- `...스타일_13...::2`

Actual runtime CASE-01 donor payload previously sealed in provider-input evidence begins:
- `...101번째프로포즈_05...::11`
- `...101번째프로포즈_02...::4`
- `...시크릿가든_19...::3`
- `...101번째프로포즈_02...::8`

Therefore the prior six-case batch evidence cannot by itself stand as proof of the exact runtime donor-selection path.

## Scientific interpretation
- DB59 physical connection/binding is supported.
- `USE_RETRIEVAL` decision-level connection is supported.
- Runtime/batch donor-selection parity is NOT supported in Attempt 1.
- P07-B cannot close on Attempt 1.
- No threshold, field, donor, prompt, or rubric was tuned in response to this result.

## Required next action
Preregister a repair that unifies runtime and batch/pretest retrieval around one canonical donor-selection implementation, then rerun the full pretest from the same sealed DB59/current-authority inputs. Any repair must be propagated into the canonical 5 Parts / 9 Packages before P07-B can be declared physically closed.
