# P07-I4D Surface Realization Modes / Craft Operators — Preregistration R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Parent physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4B_LITERARY_SURFACE_CONTRACT_R1`
Parent Package Set SHA256: `3103c0448649a9d89294abc3e5ba3fde2bf9ac415ea5e8d69d530562e4fdcb2b`
Parent reconstructed C2 SHA256: `fd5e3d78b3e127a6c2a252d5a825b8355e88438a18cc386239e6ce006e91ebaa`
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Formal scored count before probe: 137
R140 attempts/outputs/scores before probe: 0/0/0
Real OpenAI Live evidence eligibility: FALSE unless a trusted live receipt exists.

## 1. Problem statement
P07-I4B successfully adopted `LiterarySurfaceContractR1` and produced an eight-scene internal human-competitive development signal. P07-I4C R2 then generalized the interface across a whole 50-scene episode and strongly beat the old P07-I3 surface in Stage A (12/12), but failed the preregistered fresh-human Stage B gate at Human 9 / Candidate 3 / Tie 0.

The remaining losses were not uniformly distributed. Candidate wins occurred in family/relationship, ensemble/community, and procedural/social scenes. Candidate losses clustered in high-pressure occupational/action/reveal/exit modes. Therefore P07-I4D may NOT weaken Stage B thresholds and may NOT rewrite `LiterarySurfaceContractR1` globally. It tests whether scene-function-specific `SurfaceRealizationMode` / `CraftOperator` payloads can improve the nine frozen loss strata while preserving the successful general interface.

## 2. Hypothesis
Keeping `LiterarySurfaceContractR1` unchanged, adding a structured scene-function-specific `SurfaceRealizationModeR1` consumed by the renderer will improve high-pressure occupational/action/reveal/exit realization because the renderer receives mode-specific dramatic execution constraints rather than applying one generic surface strategy to every scene.

## 3. Frozen target loss scenes and modes
Exactly the nine P07-I4C R2 Stage-B loss scenes are treatment targets:

1. S03 `INVESTIGATIVE_INTERPERSONAL` -> mode `ELICITATION_PRESSURE`
2. S19 `QUIET_EMOTIONAL_RELATIONSHIP` -> mode `EMOTIONAL_WITHHOLDING`
3. S21 `WORKPLACE_PROCEDURAL` -> mode `OCCUPATIONAL_EXECUTION`
4. S28 `TIME_PRESSURE` -> mode `DEADLINE_KINETICS`
5. S33 `INVESTIGATIVE_REVEAL` -> mode `REVEAL_REVERSAL`
6. S37 `POWER_CONFLICT` -> mode `STATUS_DOMINANCE`
7. S41 `URGENT_PROCEDURAL` -> mode `URGENT_COMMAND_ACTION`
8. S45 `ENSEMBLE_TEAM_WORK` -> mode `TEAM_EXECUTION`
9. S50 `EXIT_PRESSURE` -> mode `EXIT_ESCALATION`

Protected successful controls from I4C R2:
- S07 `FAMILY_RELATIONSHIP_CONFLICT`
- S11 `ENSEMBLE_COMMUNITY_WORK`
- S14 `PROCEDURAL_SOCIAL`

Protected controls must receive no new targeted mode and must remain byte-identical in this probe.

## 4. Frozen control / treatment
CONTROL for each target scene: exact sealed P07-I4C R2 candidate scene text from final treatment SHA256 `5a4943106d9013777620299beb1ded5e233bf825d7a3fbdf7b2fce59c1206639`.

TREATMENT: same frozen scene semantics and same `LiterarySurfaceContractR1`, with one additional `SurfaceRealizationModeR1` payload chosen solely from the frozen scene-function label above.

No human-anchor text may be inspected during treatment generation. Fresh human anchors may be selected only after all nine treatment scenes are sealed and the treatment-vs-control blind gate passes.

## 5. SurfaceRealizationModeR1 contract
Every targeted mode payload contains only craft-execution instructions, never new story facts.

Common required fields:
- `mode_id`
- `dramatic_clock`
- `action_chain`
- `information_release_pattern`
- `status_or_relationship_motion`
- `turn_mechanism`
- `exit_pressure_mechanism`
- `compression_rule`
- `anti_exposition_rule`
- `prohibited_generic_rhythm`

Mode-specific requirements:

### ELICITATION_PRESSURE
- question / evasion / partial concession ladder;
- each exchange must change leverage, not merely repeat information;
- one observable tell or physical choice may carry withheld information;
- no multi-line explanation of investigative rationale.

### EMOTIONAL_WITHHOLDING
- explicit emotion statement minimized;
- asymmetry between what one character knows/wants and what can be said;
- concrete relational object/action carries pressure;
- emotional turn must occur through choice, omission, or changed posture rather than summary.

### OCCUPATIONAL_EXECUTION
- domain action sequence must be legible through work being done;
- occupational vocabulary appears only where an action depends on it;
- world/role fatigue and competence shown through task rhythm, not briefing dialogue.

### DEADLINE_KINETICS
- explicit or implicit countdown must alter choices;
- scene beats shorten as deadline approaches;
- interruption/collision must consume time or force prioritization;
- no static explanation while the clock is active.

### REVEAL_REVERSAL
- release information in staged packets rather than one explanatory block;
- each packet changes belief, alliance, or tactical position;
- final reveal must force an immediate relational or action consequence.

### STATUS_DOMINANCE
- power is expressed through who can interrupt, refuse, delay, name, move, or make others wait;
- avoid explaining hierarchy that can be enacted;
- reversal or consolidation of status must be observable in dialogue control or spatial behavior.

### URGENT_COMMAND_ACTION
- commands must map to immediate physical/task responses;
- ethical or relational conflict runs concurrently with procedure;
- no post-command explanation unless the action itself fails.

### TEAM_EXECUTION
- divide labor across at least two independently causal team members when permitted by frozen semantics;
- chain tasks so one member's output constrains another member's action;
- avoid protagonist-only orchestration or roll-call dialogue.

### EXIT_ESCALATION
- after the apparent scene objective is reached, introduce or expose one authorized pressure that raises the next-episode cost;
- no explanatory echo after the turn;
- final beat should be action/image/decision/arrival/revelation rather than thematic summary where possible.

## 6. Generation boundary
The nine mode contracts and treatment prose may be authored by the in-session foundation LLM for development-only evidence, labeled `IN_SESSION_LLM_SURROGATE__NONLIVE`.
Python/runtime may only validate, route, hash, measure, audit, and commit research receipts. Python literary prose generation = 0.

## 7. Causal adoption gates
G1. `SurfaceRealizationModeR1` validates for all 9 targeted scenes.
G2. Targeted mode payload is physically included in renderer/provider literary input for all 9 targeted scenes.
G3. Selected mutation of a consumed mode field changes provider-input literary hash.
G4. Irrelevant non-consumed metadata mutation leaves provider-input literary hash invariant.
G5. Protected S07/S11/S14 receive no targeted mode and their probe text remains byte-identical.
G6. Frozen `LiterarySurfaceContractR1.semantic_invariants`, scene order, ownership, principal cast, information movement, relationship movement, thread commitments, and exit-state truth remain unchanged.
G7. No future/source leakage and no unsupported principal fact.

## 8. Mechanical / semantic gates
Across the 9 targeted treatments:
- no unauthorized principal speaker;
- no critical semantic/continuity violation;
- procedural/control vocabulary density does not increase by >20% versus target-scene control aggregate;
- mean non-empty line length does not increase by >20% versus control aggregate;
- exact long-dialogue duplicate ratio <=0.05;
- exact long-narrative duplicate ratio <=0.05;
- no forbidden engine/meta terminology;
- protected three successful controls byte-identical.

## 9. Stage A — targeted repair vs exact I4C-R2 control
After all nine treatment scenes are sealed, create nine anonymous randomized pairs: treatment vs exact frozen I4C-R2 scene control.
Mapping remains sealed until judgments are written.

PASS requires BOTH:
- Treatment wins >=7/9;
- Treatment wins + ties >=8/9;
- zero critical semantic/continuity violation.

If Stage A fails: `HOLD__CRAFT_OPERATORS_INSUFFICIENT__NO_HUMAN_STAGE__NO_WHOLE_EPISODE_RETRY`.

## 10. Stage B — fresh-human targeted benchmark
Only after treatment sealing and Stage A PASS, select nine fresh DB59 human broadcast-script anchors matched to the same nine functional strata. Do not knowingly reuse exact I4C-R2 or I4B human passages where feasible.
Mask titles/names/source identifiers and randomize left/right after Candidate sealing.

Human-competitive targeted development signal requires BOTH:
- Candidate wins >=3/9;
- Candidate wins + ties >=5/9;
- zero critical semantic/continuity violation.

These thresholds are not weaker than I4C R2: required Candidate win fraction increases from 25% to 33.3%; required non-loss fraction increases from 50% to 55.6%.

If failed: `HOLD__CRAFT_OPERATORS_NOT_HUMAN_COMPETITIVE__NO_WHOLE_EPISODE_RETRY`.

## 11. Promotion rule
No 50-scene rerender and no active-engine promotion unless causal, mechanical, Stage A, and Stage B gates all PASS.

If all pass, only the mode contract/bridge/renderer wiring may be promoted. Exact treatment prose remains research evidence and must not be hardcoded. A separately preregistered whole-episode rerender must then test generalization.

If failed, P07-I4B remains Current Physical Authority. I4C R1/R2 prose and I4D treatment prose remain non-authoritative research evidence.

## 12. Regression / physical rule
Any promoted code must pass focused tests and exact final packaged-C2 fresh-materialization nonhistorical regression with pytest exit code 0 before any 5 Parts / 9 Packages reseal.

## 13. Non-claims
A P07-I4D development PASS would not establish real OpenAI Live parity, external human consensus, human-writer equivalence, whole-episode human competitiveness, Production promotion, RFV3, CP1 Live, official R-F/R-G, or Formal R140.
