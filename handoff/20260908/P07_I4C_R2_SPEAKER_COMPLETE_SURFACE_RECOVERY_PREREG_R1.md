# P07-I4C R2 Speaker-Complete Surface Recovery — Preregistration R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Parent physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4B_LITERARY_SURFACE_CONTRACT_R1`
Recovery source: P07-I4C R1 HOLD result commit `7acf0d35fa931f8927cc8402907cc82fe4502af8`
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Formal scored count: 137
R140 attempts/outputs/scores: 0/0/0 HARD BLOCK
Real OpenAI Live evidence eligibility: FALSE.

## 1. Purpose
Recover P07-I4C without weakening any literary or mechanical threshold after R1 was correctly HOLDed for one pre-render contract-completeness defect: S14 direct-speaking principal `박정숙` was omitted from `character_play_state` even though she spoke in the frozen P07-I3 control and R1 surface.

## 2. Root-cause hypothesis
The failure is caused by an incomplete fail-close validator, not by the whole-episode architecture. If the Scene Plan -> LiterarySurfaceContract bridge enforces speaking-principal completeness before renderer/provider input, then the invalid S14 contract can be corrected before generation, S14 alone can be re-rendered, and the other 49 already-valid R1 final scenes can remain byte-identical.

## 3. Frozen recovery design
- R1 final treatment SHA256 before recovery: `c7865bfd3fe0c5925fcad429cf8c115f52fe689e6af7075db50bec75e4fe089e`.
- Exactly 49 scenes are protected and must remain byte-identical to R1 final: all scenes except S14.
- Only S14 may receive a corrected contract and new Surface output.
- S14 semantic invariants, scene objective, obstacle, information change, relationship change, turn/exit state, sequence ownership, scene order, and principal cast set remain frozen.
- S14 corrected contract must add `박정숙` to speaking-principal `character_play_state` and `voice_state` before any new prose is generated.
- No new plot event, character, world fact, source/future information, or sequence change is allowed.

## 4. New fail-close guard
Before any R2 Surface output, the active research runtime must implement and test a speaker-completeness guard:
- input: contract + frozen Scene Plan allowed/direct-speaking-principal set;
- every direct-speaking principal must have `character_play_state`;
- every direct-speaking principal must have `voice_state`;
- missing required principal -> fail closed before provider/renderer payload;
- functional/local roles may be explicitly classified separately and need not be treated as principal characters;
- guard must not author literary prose.

Pre-output gates:
- focused guard tests PASS;
- all 50 R1 contracts audited;
- exactly the known critical S14 omission is identified under principal classification before correction;
- corrected 50-contract set passes speaker completeness 50/50 before S14 prose generation.

## 5. Recovery generation boundary
Only after the corrected contract set is sealed may the in-session foundation LLM generate a new S14 Surface. Label `IN_SESSION_LLM_SURROGATE__NONLIVE`.
Human DB59 anchors must not be inspected during corrected-contract construction or S14 generation.

## 6. Whole-episode recovery gates
After replacing only S14:
- exactly 50 scenes;
- 35,000-45,000 Unicode characters;
- protected 49 scenes byte-identical to R1 final;
- unauthorized speakers = 0;
- speaker-complete LiterarySurfaceContract = 50/50;
- critical semantic/continuity violations = 0;
- source/future leakage = 0;
- exact long-dialogue duplicate ratio <=0.05;
- exact long-narrative duplicate ratio <=0.05;
- procedural/control vocabulary density <=12 / 1,000 chars;
- mean non-empty line length <=45 chars OR >=20% reduction vs P07-I3;
- protagonist scene share <=0.65;
- protagonist-group sequence ownership <=0.60;
- non-protagonist-owned sequences >=4;
- non-protagonist owner groups >=2.

## 7. State rule
R1 did not commit state. R2 may create a surface-bound State Commit receipt only after all R2 mechanical/semantic/blind gates pass. The canonical semantic carry itself must remain the existing P07-I3 semantic carry unless a new semantic change is explicitly demonstrated; no silent semantic state mutation is allowed.

## 8. Stage A whole-episode blind
Only after R2 final screenplay is sealed:
- use the same preregistered I4C 12-strata design, sampled across the whole episode;
- compare R2 final Treatment vs exact P07-I3 control anonymously;
- R2 Stage A PASS requires Treatment wins >=9/12, losses <=3/12, zero critical semantic/continuity violation.

No R1 blind outcome exists and none may be imputed.

## 9. Stage B fresh-human blind
Only if Stage A passes, select 12 fresh DB59 human broadcast anchors after R2 treatment sealing. Do not knowingly reuse exact I4B Stage B passages where feasible.
Human-competitive whole-episode development signal requires BOTH:
- Candidate wins >=3/12;
- Candidate wins + ties >=6/12;
- zero critical semantic/continuity violation.

## 10. Regression / promotion rule
If R2 passes all gates, promoted code is the speaker-completeness validator/bridge guard only; no treatment prose may be hardcoded.
Focused tests and exact final packaged-C2 fresh-materialization nonhistorical regression must PASS with pytest exit code 0.
Only then may changed bytes be physically resealed into canonical 5 Parts / 9 Packages with full CRC/duplicate/unsafe/nested/secret/cross-package/Manifest/Trust Root audit.

## 11. Fail rule
Any failure of corrected 50-contract completeness, 49-scene byte stability, Stage A, Stage B, state rule, or regression -> HOLD. No threshold relaxation and no silent third mutation of R1.

## 12. Non-claims
R2 PASS would remain development-only and would not establish real OpenAI Live parity, external multi-human consensus, human-writer equivalence, RFV3, CP1 Live, official R-F/R-G, Production promotion, or Formal R140.