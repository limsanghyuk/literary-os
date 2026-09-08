# P07-I4G — Performance Direction / Dialogue–Direction Allocation Causal Probe — Preregistration R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA

## 0. Parent authority
Active engine authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`
Active C2 SHA256: `1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`
Current cumulative physical research authority before I4G: `CURRENT_PHYSICAL_RESEARCH_AUTHORITY__P07_I4D_ACTIVE__I4C_I4E_I4F_EVIDENCE_SYNC_R2`.
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
Formal scored count remains 137. R140 remains 0/0/0 HARD BLOCK. Real OpenAI Live evidence eligibility remains FALSE.

## 1. New craft doctrine being tested
A scene is not dialogue alone. Surface realization is `Action/Direction + Dialogue`.

Dialogue should primarily perform interpersonal action (question, evade, attack, defend, persuade, trade, conceal, reveal, refuse, joke, connect). Dialogue should not be used merely to explain the character's current emotion, relationship state, plot state, or internal engine logic to the audience.

Action/Direction may carry:
- place/time/environment and scene-entry state;
- actor blocking, movement, distance, gaze, silence and interruption;
- prop/object interaction;
- playable/filmable emotional manifestations;
- delivery context immediately before/around dialogue;
- beat transition and scene-exit pressure.

Direct emotional statements are not prohibited when motivated as character action. The prohibited pattern is exposition whose principal function is audience explanation.

Direction may be detailed. It should prefer playable/filmable information over novelistic non-observable psychological narration.

## 2. Broadcast scale doctrine for future whole-episode work
This probe is scene-scale and does not itself rerender a whole episode, but it freezes the new future scale rule:
- whole-episode character count: minimum >= 35,000 Unicode characters; no fixed maximum;
- 9–10 sequences and 45–50 scenes are minimum broadcast reference floors, not fixed targets or maxima;
- larger sequence/scene counts are allowed when episode architecture requires them;
- excess length is judged by redundancy, repetition, non-playable exposition, pacing collapse and craft waste, not by a hard maximum.

## 3. Purpose
Determine whether explicitly separating Performance/Direction information from Dialogue improves scene craft while preserving semantic invariants, compared with the current I4D surface interface.

This experiment precedes the next conservative Selector/Abstention experiment because I4F could not distinguish two causes of MODE failure:
1. the scene did not need intervention; versus
2. intervention was appropriate but the generated surface under-realized action/direction or overburdened dialogue.

## 4. Research questions
RQ1. Does a `PerformanceDirectionContractR1` reduce explanatory/emotion-label dialogue without reducing semantic fidelity?
RQ2. Does it increase playable/filmable direction and subtext externalization?
RQ3. Does it avoid merely moving explanation from dialogue into novelistic psychological narration?
RQ4. Does it improve blind pairwise craft preference on fresh prospective scenes?
RQ5. Are benefits present across more than one scene-function stratum?

## 5. Intervention
Add a research-only `PerformanceDirectionContractR1` after `LiterarySurfaceContractR1` and optional `SurfaceRealizationModeR1`, before final surface realization.

Canonical fields:
1. `environment_state`
2. `actor_action_chain`
3. `performance_cues`
4. `subtext_carriers`
5. `dialogue_delivery_context`
6. `beat_transitions`
7. `exit_direction`
8. `direction_firewall`

`direction_firewall` must prohibit:
- internal engine terminology;
- unsupported new semantic facts;
- novelistic omniscient interior explanation when not playable/filmable;
- simply restating dialogue content in action lines;
- emotion-label repetition when behavior can carry the beat.

Python/runtime remains orchestration/validation/hashing only. Python literary prose generation = 0.

## 6. Frozen prospective sample
Use 12 fresh prospective scenes not used as scored triads in P07-I4F and not used in I4E/I4C Stage-A fixed 12 where feasible. Sample must cover at least eight functional strata and at least three sequences.

Before any Treatment prose:
- freeze scene IDs;
- freeze scene-function strata;
- freeze exact Control bytes;
- freeze semantic invariants and speaker sets;
- freeze whether each scene uses current I4D mode or NONE; I4G does not re-optimize mode selection.

Human anchors are not inspected before Stage A passes.

## 7. Control and Treatment
Control = exact current surface realization for each frozen scene under existing I4D/I4C-R2 evidence, with no new PerformanceDirectionContract.

Treatment = same semantic invariants, same speaker authorization, same selected I4D mode/NONE status, plus `PerformanceDirectionContractR1` and a fresh re-realization.

No plot, sequence ownership, thread state, scene objective/obstacle/info-change/relationship-change/turn/exit-state change is allowed.

## 8. Pre-output gates
Before Treatment prose is generated:
- 12/12 PerformanceDirectionContract validation PASS;
- semantic invariant binding 12/12 PASS;
- speaker/play/voice completeness PASS;
- selected performance-direction field mutation changes provider literary-payload hash;
- irrelevant metadata mutation leaves literary payload invariant;
- no Human Anchor inspected;
- new Treatment prose count = 0.

Any failure => HOLD before generation.

## 9. Mechanical/post-output gates
For all 12 Treatment scenes:
- unauthorized principal speaker = 0;
- critical semantic/continuity violation = 0;
- source/future leakage = 0;
- internal/meta terminology leakage = 0;
- long exact dialogue/narrative duplication = 0;
- no clear malformed Korean morphology/word-composition sentinel in accepted output;
- non-playable psychological narration rate must not exceed Control;
- explanatory dialogue density must be lower than Control in aggregate;
- playable/filmable direction coverage must be higher than Control in aggregate.

Mechanical metrics are diagnostic; they do not substitute for Blind craft preference.

## 10. Stage A internal blind gate
Create 12 pairwise anonymous Control-vs-Treatment packets. Seal mapping separately. Write all judgments before mapping reveal.

Primary pairwise criteria:
- dialogue naturalness / non-expository character action;
- playable/filmable direction;
- subtext externalization;
- actor-performance specificity;
- voice differentiation;
- scene objective/obstacle/turn clarity without verbal explanation;
- pacing and line economy;
- semantic/continuity fidelity.

Primary Stage A gate:
- Treatment wins >= 8/12;
- Treatment losses <= 3/12;
- Treatment win+tie >= 10/12;
- no critical semantic/continuity violation.

Failure => HOLD, no Human Stage B, no State Commit, no active-engine promotion.

## 11. Stage B fresh-human developmental gate
Only after Treatment seal and Stage A PASS may fresh DB59 human broadcast-script anchors be selected.

Human dialogue craft and candidate dialogue craft are compared directly. Candidate direction is not penalized simply for being more detailed than the human source; instead candidate direction is judged independently for playable/filmable utility, non-redundancy and dramatic usefulness.

Required Stage B gate on 12 matched scene-function pairs:
- Candidate wins >= 3/12;
- Candidate wins + ties >= 6/12;
- no critical violation.

This remains an internal single-judge development signal, not human-writer equivalence or external consensus.

## 12. Promotion rule
If and only if Stage A and Stage B PASS:
- adopt the interface/validation/wiring for `PerformanceDirectionContractR1` as an active-engine candidate;
- Treatment scene texts remain research evidence only, never hardcoded policy;
- run full nonhistorical regression and exact packaged-C2 fresh-materialization regression before active promotion;
- only then create a new active 5 Parts / 9 Packages authority.

If HOLD/FAIL:
- no State Commit;
- no active C2 change;
- no active-engine promotion;
- synchronize all I4G evidence into the cumulative 5 Parts / 9 Packages research authority before any I4H work.

## 13. Interruption-safe mandatory checkpoint rule
Because the current session may terminate at any point:
- immediately after this preregistration commit, Current Session Recovery Pointer / Developer Hub / START_HERE must identify I4G as `PREREGISTERED_ACTIVE__NO_OUTPUTS`;
- after every irreversible phase (sample seal, pre-output gate, treatment seal, Stage A judgment seal, Stage A result, Stage B judgment seal/result, final verdict), write a recoverable local/GitHub checkpoint or evidence file with hashes;
- if the session stops, the next session must resume from the latest sealed checkpoint rather than regenerate prior outputs;
- after I4G ends, PASS or HOLD, cumulative 5/9 research synchronization is mandatory before starting I4H.

## 14. Claim boundary
I4G is DEVELOPMENT / PREFORMAL. It cannot increment the formal scored count, unblock R140, establish real OpenAI Live evidence, external human consensus, or Production promotion by itself.
