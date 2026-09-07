# P07-I4B Scene Plan -> Surface Realization Interface Redesign — Preregistration R1

Date: 2026-09-07
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Parent authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4A_PROVIDER_SHADOW_PASS_SURFACE_REPAIR_HOLD_R1`
Parent Package Set SHA256: `e0bb95184f6ca841e491ef287507d88c07385982af72db9a8df4c61cbdb3563d`
Parent reconstructed C2 SHA256: `496d396096630bf36e3c273becc954a8710989df0896586a90ac4cae5ef6c9c7`
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Formal scored count before probe: 137
R140 attempts/outputs/scores before probe: 0/0/0
Real OpenAI Live evidence eligibility: FALSE unless a trusted live receipt exists.

## 1. Problem statement
P07-I4A proved that prompt-level Literary Compression/Voice repair did not generalize: calibrated human blind baseline was Human 12 / Candidate 0 / Tie 0; six-scene repair was Human 5 / Candidate 1 / Tie 0 and failed the preregistered non-loss gate. Therefore P07-I4B may not relax the blind threshold and may not merely add more prose directives. It must redesign the information interface between `SCENE_PLAN` and `SURFACE_REALIZATION`.

Primary diagnosed failure: `INTERNAL_NARRATIVE_CONTROL_LOGIC_TO_SURFACE_EXPOSITION_LEAK` — engine-internal evidence/provenance/verification logic is too directly verbalized by characters, producing long procedural dialogue, weak character-specific voice, reduced subtext and lower dramatic compression.

## 2. Hypothesis
A structured `LiterarySurfaceContract` inserted between `SCENE_PLAN` and the renderer will improve literary realization while preserving semantics if it explicitly separates:
- what the scene must accomplish semantically;
- what each character wants/tactically does now;
- what information may/must be spoken versus only implied/acted;
- relationship-specific public posture/private pressure;
- character-specific voice state;
- subtext/physicalization carriers;
- scene rhythm/exit pressure;
- internal engine logic that is forbidden from direct surface verbalization.

## 3. Research questions
RQ1. Does the new interface causally reach renderer/provider input rather than merely exist as schema?
RQ2. Does selected mutation of interface fields change downstream payload/surface while irrelevant metadata mutation remains invariant?
RQ3. Does the redesigned interface beat the exact P07-I3 control surface on the same frozen scenes?
RQ4. Does it improve human-competitive blind performance without weakening the I4A threshold?
RQ5. Can it reduce procedural-exposition leakage without changing frozen scene/sequence facts, ownership, relationship movement, or exit state?

## 4. Frozen scenes
Exactly eight P07-I3 scenes are used, selected before treatment output:
`S11, S14, S19, S21, S28, S33, S37, S50`.

Rationale strata:
- S11/S14: tenant discovery + procedural/social interaction;
- S19: family/authority conflict;
- S21: corporate bookkeeping/internal pressure;
- S28: midpoint multi-party pressure;
- S33: tenant evidence ownership;
- S37: internal-company fracture;
- S50: convergence/episode exit pressure.

Six of these overlap the failed I4A repair probe so improvement can be directly compared; S19 and S28 are held-out functional strata for generalization.

## 5. Frozen control and treatment
CONTROL: exact sealed P07-I3 final surface excerpts for the eight scenes, unchanged.

TREATMENT: same frozen P07-I3 scene/sequence semantics, but renderer input includes `LiterarySurfaceContractR1`.

Upstream invariants:
- episode trajectory unchanged;
- sequence ownership unchanged;
- scene order unchanged;
- allowed speakers unchanged;
- scene function unchanged;
- required information/relationship change unchanged;
- exit state unchanged;
- no future/source leakage;
- no new principal character/event/world fact.

## 6. LiterarySurfaceContractR1 frozen fields
Each treatment scene must carry:
1. `semantic_invariants`
   - scene objective
   - obstacle
   - information change
   - relationship change
   - turn/pressure
   - exit state
2. `character_play_state` per speaking principal
   - immediate want
   - tactic
   - status move
   - withheld/avoided direct statement
   - current pressure modulation
3. `dialogue_information_budget`
   - `must_say` factual propositions (0-2 preferred; hard max 3)
   - `may_imply`
   - `must_not_verbalize`
   - `procedural_concept_cap` hard max 2 unless the scene's explicit dramatic conflict is the procedure itself
   - `consecutive_exposition_line_cap` = 1
4. `relationship_surface_map`
   - dyad/public posture
   - private pressure
   - leverage/vulnerability
   - directness forbidden/allowed boundary
5. `voice_state`
   - source/caller-authorized baseline voice profile where available
   - scene-local sentence-length modulation
   - directness/avoidance
   - humor/aggression
   - status speech
   - vocabulary pressure
6. `subtext_physicalization`
   - latent pressure
   - authorized object/spatial/timing/silence carrier
   - explicit emotion explanation forbidden unless dramatically necessary
7. `rhythm_contract`
   - entry pressure
   - escalation/pivot
   - exit pressure
   - no explanatory echo after turn
8. `surface_firewall`
   - engine/research/provenance/verification rationale must remain internal unless it is an explicit story-world fact required by the scene
   - no analytic terminology leakage
   - `functional_truth != spoken_explanation`

Python may validate/route/hash these fields but must author zero literary prose.

## 7. Treatment generation boundary
The structured LiterarySurfaceContract and treatment prose may be authored by the in-session foundation LLM for development-only evidence. Label: `IN_SESSION_LLM_SURROGATE__NONLIVE`.
Human-anchor text from DB59 must not be inspected during treatment generation. Human anchors are selected/masked only after all treatment scenes are sealed.

## 8. Causal adoption gates
G1 Contract validation PASS for all 8 scenes.
G2 Contract is physically present in renderer/provider payload for all 8 scenes.
G3 Selected mutation test: changing one selected literary field (`tactic`, `must_not_verbalize`, or `relationship_surface_map`) changes provider-input hash.
G4 Irrelevant mutation test: changing non-consumed metadata leaves provider-input literary payload hash invariant.
G5 Semantic invariants remain byte-equivalent/canonically equivalent across control/treatment planning input.
G6 No unsupported/future-source truth is introduced.

## 9. Mechanical surface gates
Across the 8 treatment scenes:
- no unauthorized speaker;
- procedural-control vocabulary density must fall by >=50% versus the exact P07-I3 control excerpts;
- mean non-empty line length must fall by >=20% versus control OR remain <=45 Unicode chars;
- no exact long-dialogue duplicate ratio >0.05;
- no forbidden engine/meta leakage;
- required scene exit state preserved.

These are diagnostics/gates, not a substitute for blind craft evaluation.

## 10. Blind evaluation design
### Stage A — Treatment vs exact P07-I3 control
Create 8 anonymous left/right pairs, randomized after treatment sealing. Judge mapping remains sealed until judgments are written.
PASS requires:
- Treatment wins >=6/8;
- Treatment losses <=2/8;
- zero critical semantic/continuity violation.

### Stage B — Treatment vs fresh human broadcast-script anchors
Only if Stage A passes.
Use fresh DB59 human anchors selected by scene function from multiple works; do not reuse the exact I4A six-pair anchors where feasible. Mask titles/names/source identifiers and randomize sides after treatment sealing.

Human-competitive development signal requires BOTH:
- Candidate wins >=2/8;
- Candidate wins + ties >=4/8.

This is not weaker than I4A: the non-loss fraction remains 50%, while the required Candidate wins increase from >=1 to >=2.

If Stage B fails: `HOLD__INTERFACE_REDESIGN_NOT_HUMAN_COMPETITIVE__NO_FULL_EPISODE_RERENDER`.
If Stage A fails: `HOLD__INTERFACE_REDESIGN_INSUFFICIENT__NO_HUMAN_STAGE__NO_FULL_EPISODE_RERENDER`.

## 11. Evaluation axes
Forced pairwise judgment prioritizes:
1. dialogue naturalness;
2. character voice differentiation;
3. subtext/implication;
4. physicalization/action specificity;
5. relationship/power specificity;
6. exposition discipline;
7. pacing/line economy;
8. scene turn and exit pressure;
9. emotional progression;
10. semantic/continuity fidelity.

## 12. Promotion rule
No full 50-scene rerender and no active engine promotion unless both Stage A and Stage B pass plus causal/mechanical gates pass.
If passed, P07-I4B may promote the new interface contract/bridge/renderer wiring and then physically reseal changed bytes into the canonical 5 Parts / 9 Packages.
If failed, interface code remains research evidence only and P07-I4A remains Current Physical Authority except for separately justified non-literary engineering fixes.

## 13. Regression and physical rule
Any promoted code must pass exact packaged-C2 fresh-extraction nonhistorical regression with exit code 0. If promoted, changed packages receive new bytes/new SHA and unchanged packages remain byte-identical; CRC/duplicate/unsafe/nested/secret/cross-package reconstruction/Manifest/Trust Root must all PASS.

## 14. Non-claims
A development PASS does not establish real OpenAI Live parity, external human consensus, Production promotion, RFV3, CP1 Live, official R-F/R-G, or Formal R140.
