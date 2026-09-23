# R76 방송대본 외부평가 개발자 지침서 R1

Date: 2026-09-23
Status: RESEARCHED_AND_REISSUED_FOR_DEVELOPER

## 1. 현재 평가 대상

현재 R76-VP-B1에서 실제 완성된 1회차 방송대본 Surface가 존재한다.

- Work: SYNTH_R76_BREAKWATER_THEATER / 「방파제 극장」
- Final surface: 35,333 Korean characters
- Structure: 9 Sequences / 52 Scenes
- Dialogue-bearing scenes: 52/52
- Surface SHA256: 7b35fa2418f07382b52d5e93403e3da555539e1c96747cca98e3227e5c4c3ee4
- Mechanical validation: PASS
- Internal virtual evaluation: PASS, but NOT independent external evidence
- Output-only reverse reconstruction: completed
- Text Canonical State Ledger: sealed
- External independent judgment outputs: 0 at this guide revision

Therefore the next gate is external evaluation of the already-sealed finished screenplay. Do not regenerate, edit, or improve the screenplay after an external judge has seen it.

## 2. Historical external-evaluation methods that were re-investigated

### 2.1 SYNC-R58 Architecture-Only Blind

Purpose:
Evaluate upper-layer architecture independently of screenplay-surface prose.

Design:
- 3 independent fresh-context judges.
- 6 blind A/B pairs per judge.
- 18 total judge-pair outcomes.
- Candidate position balanced 3A/3B for each judge.
- Mapping hidden from judges and from the mapped-result stage until all judgments were sealed.
- Packet leak audit before dispatch.

Frozen axes:
1. EPISODE_MULTI_STRAND_ARCHITECTURE
2. SEQUENCE_FUNCTIONAL_DIVERSITY
3. ENSEMBLE_RELATIONSHIP_WEAVING
4. INFORMATION_ASYMMETRY_USE
5. SOCIAL_ECOLOGY_INTEGRATION
6. SCENE_TRANSACTION_SPECIFICITY_NECESSITY
7. CAUSAL_STATE_CONTINUITY
8. ESCALATION_TURNING_ARCHITECTURE

Critical violations:
- visible future-source leakage
- due-now obligation omitted
- deferred obligation falsely closed
- arm-identifying implementation labels

Frozen gate:
- Candidate wins >=12/18
- Candidate wins + ties >=15/18
- no Candidate critical-violation majority

Important lesson:
Raw scene/sequence counts were explicitly NOT treated as quality scores.
Axis means were descriptive. The preregistered win/tie/loss gate determined qualification.

### 2.2 R62 / R66 F01 External Blind

Purpose:
Evaluate whether the Treatment changed scene-contract quality safely.

Design:
- 3 independent fresh-context judges J01/J02/J03.
- 12 A/B pairs per judge.
- A/B Treatment position balanced 6/6 for each judge.
- Judges see only their own sealed packet.
- No judge may see lineage, source code, coordinator mapping, other judge results, or desired outcome.
- Repository/prior-chat search prohibited.
- All judgments sealed before mapping reveal.

R66 frozen axes:
1. TRANSACTION_SPECIFICITY
2. CAUSAL_COHERENCE
3. RESISTANCE_CHOICE_COST_DEVELOPMENT
4. NON_MECHANICAL_PROGRESSION
5. SCENE_STEP_NECESSITY
6. OBLIGATION_FIDELITY
7. SEMANTIC_APPLICABILITY
8. UNSUPPORTED_NOVELTY_PREMATURE_RESOLUTION_RISK

Per-pair aggregation:
- >=2 Treatment votes => Treatment WIN
- >=2 Control votes => Treatment LOSS
- otherwise TIE
- Treatment critical violation confirmed only if >=2/3 judges flag the mapped Treatment arm

Overall gate:
- Treatment wins >=7/12
- Treatment wins + ties >=10/12
- Treatment losses <=2/12
- confirmed critical Treatment violations = 0

Important lesson:
R62 mechanically improved diversity but failed quality because 9W/0T/3L violated the frozen gate.
R66 later passed 12W/0T/0L, 36/36 Treatment votes, confirmed critical violations 0.
This establishes that mechanical metrology cannot substitute for blind literary judgment.

### 2.3 R70 Provider Surface Evaluation

Purpose:
Evaluate Provider-generated scene prose.

Strong practices:
- Actual provider requests frozen before calls.
- Request bytes, response bytes, model, usage, attempt receipts, local guards preserved.
- 3 independent judge contexts.
- Judge A/B positions independently balanced.
- Scene order shuffled.
- Judge sees shared scene facts/contract but not provider context payload, future plan, Treatment identity, other judges.
- Judge must not accept machine fields/self-description as literary realization.
- Evidence quotations checked against source output.
- Majority rule for winner.

Six literary axes used in the auxiliary blind:
- Character Voice
- Relationship / Status Pressure
- Ensemble / World Specificity
- Subtext Physicalization
- Causal / Semantic Fidelity
- New-Fact Safety

Important R70 lesson:
Provider validity and literary-quality validity are separate.
R70 R2 achieved valid 24/24 arms and 12/12 pairs, but the original coordinator mapping bytes were lost.
Therefore the formal literary verdict remained HOLD.
Never reconstruct or infer a lost secret mapping from writing style.

### 2.4 R133 / R136-R138 lessons

R133 demonstrated the central methodological failure mode:
Strong same-session/internal scores did not transfer to independent blind evaluation.
Therefore external blind evidence is mandatory before a screenplay-quality claim.

R136 used original independent judges across Legacy / R135 / Improved screenplay renderer.
All three judges directionally preferred C > B > A, but the experiment still failed one frozen gate because Spoken Korean Colloquiality did not reach its preregistered improvement threshold.

R137 and R138 likewise show:
A candidate can improve many axes yet remain formally FAIL if one or more frozen gates fail.

Important lesson:
Do not convert a mostly-good scorecard into PASS after seeing the result.
A valid unfavorable result is immutable.

## 3. What R76 external evaluation must answer

R76 is not merely a component A/B intervention.
It is one already-sealed complete broadcast-scale screenplay.

Therefore external evaluation has three different questions and they must not be conflated.

### Question A — Absolute screenplay quality
Is this finished 35,333-character episode itself sufficiently strong as a Korean broadcast screenplay?

### Question B — Structural recoverability
Can an evaluator who sees only the finished screenplay recover the episode premise, major threads, sequence functions, relationship changes, information shifts, resolved material, and deferred/open material?

### Question C — Causal improvement effect
Is R76 better than a particular Control/Baseline?

The current R76 external packet can answer A and B.
It CANNOT by itself establish C because there is no same-input, same-scale hidden Control screenplay in the current R76-VP-B1 gate.

Any future causal improvement claim requires a separately preregistered paired experiment.

## 4. R76 evaluation design — frozen current method

Do not alter these rules after the first external judge output.

Judges:
- J01
- J02
- J03
- separate fresh contexts
- each receives only its own sealed packet
- no judge sees internal result, hidden plan, State Ledger, source code, project history, GitHub, or other judge output

### 4.1 Whole-Episode Architecture / Dramaturgy

The judge reads the complete 35,333-character screenplay.

Score 1–10:
1. EPISODE_PREMISE_COHERENCE
2. CAUSAL_SEQUENCE_PROGRESSION
3. THREAD_AND_SUBPLOT_INTEGRATION
4. CHARACTER_RELATIONSHIP_TRAJECTORY
5. INFORMATION_TOPOLOGY_DRAMATIZATION
6. SCENE_NECESSITY_AND_DISTINCT_FUNCTION
7. ESCALATION_PACING
8. CLOSURE_DEFERRED_BALANCE

What these axes mean:

EPISODE_PREMISE_COHERENCE:
Does the episode have one intelligible central dramatic problem rather than a collection of unrelated incidents?

CAUSAL_SEQUENCE_PROGRESSION:
Does each major movement change the conditions for the next one? Penalize sequence changes that are only chronological or topical.

THREAD_AND_SUBPLOT_INTEGRATION:
Do safety, money/labor, documentary evidence, community, relationships, and long-horizon threads interact rather than run as independent summaries?

CHARACTER_RELATIONSHIP_TRAJECTORY:
Do relationships actually change in behavior, access, trust, withholding, responsibility, or cooperation?

INFORMATION_TOPOLOGY_DRAMATIZATION:
Does who-knows-what change through scenes, discoveries, concealment, disclosure, and action instead of explanatory recap?

SCENE_NECESSITY_AND_DISTINCT_FUNCTION:
Would removal of scenes cause meaningful causal/state loss? Penalize repeated investigation, repeated argument, or repeated paperwork that performs the same dramatic transaction.

ESCALATION_PACING:
Does pressure transform rather than merely accumulate? Examine time pressure, reversals, choice cost, temporary solutions, and new constraints.

CLOSURE_DEFERRED_BALANCE:
Does the episode close what happened now while honestly keeping unresolved long-horizon obligations open?

### 4.2 Pre-Frozen Surface-Craft Sample

The scene sample was frozen from the sealed surface hash before external scoring.

Scenes:
- SC07
- SC15
- SC30
- SC32
- SC39
- SC41

Each scene is scored 1–10 on:
1. DIALOGUE_SUBTEXT
2. CHARACTER_VOICE
3. RELATIONSHIP_STATUS_PRESSURE
4. PHYSICALIZATION_ACTION
5. PACING_ESCALATION_TIME_PRESSURE
6. ENSEMBLE_WORLD_SPECIFICITY
7. INFORMATION_DRAMATIZATION
8. KOREAN_SPOKEN_NATURALNESS

Interpretation:

DIALOGUE_SUBTEXT:
Characters should not merely explain their emotion, intention, relationship, or plot state. Dialogue should pressure, evade, negotiate, test, withhold, redirect, or choose.

CHARACTER_VOICE:
Different characters should have distinguishable sentence length, vocabulary, directness, institutional role, avoidance pattern, and conflict strategy.

RELATIONSHIP_STATUS_PRESSURE:
Power, trust, intimacy, exclusion, obligation, or authority should be active in how the exchange unfolds.

PHYSICALIZATION_ACTION:
Important changes should have screen-visible carriers: expression/gaze, hands, props, blocking, approach/withdrawal, pause/silence, failed action, withholding, spatial change.

PACING_ESCALATION_TIME_PRESSURE:
The scene should change pressure or choice; dialogue should not circle the same point without added cost.

ENSEMBLE_WORLD_SPECIFICITY:
Institution, work procedure, place, group relations, objects, and social ecology should feel specific rather than generic.

INFORMATION_DRAMATIZATION:
Information should be discovered, withheld, verified, contradicted, physically produced, or acted on—not simply narrated to the audience.

KOREAN_SPOKEN_NATURALNESS:
Lines should sound speakable in Korean television drama, not like translated prose, research notes, summaries, or policy documents.

### 4.3 Output-Only Reverse Reconstruction

The evaluator must use only the finished screenplay.

Reconstruct:
- Episode premise
- Major threads
- Functional sequence progression
- Character / relationship trajectories
- Major information shifts
- Resolved due-now material
- Deferred/open material

For each reconstructed item mark:
- EVIDENCED: directly supported by visible text/action/dialogue
- INFERRED: plausible but not directly evidenced

Purpose:
Detect the R59 failure mode where architecture claims a state that cannot be recovered from the actual screenplay.

## 5. Critical violations

A judge may flag only clearly evidenced violations.

1. INTERNAL_SCHEMA_OR_RESEARCH_META_LEAK
Internal IDs, state_delta, transaction_stage, evaluation terminology, research metadata, or implementation labels visibly leak into screenplay prose.

2. IMPORTANT_STATE_CHANGE_WITHOUT_SCREEN_VISIBLE_CARRIER
A major relationship/information/causal state supposedly changes, but the screenplay does not actually show or dramatize it.

3. EXPOSITORY_EMOTION_STATE_DIALOGUE_AS_DOMINANT_CRAFT
Characters repeatedly state emotional/relationship/plot conditions directly where dramatic action or subtext should carry them.

4. SEVERE_CHARACTER_VOICE_COLLAPSE
Multiple principal characters become functionally interchangeable in diction and conflict behavior.

5. MAJOR_CAUSAL_OR_CONTINUITY_BREAK
Later scenes depend on an event/state/information change that the screenplay did not establish.

Critical confirmation rule:
A critical violation is confirmed only when >=2/3 independent judges identify the same substantive violation.
Do not combine unrelated criticisms merely because their labels are similar.

## 6. Current frozen R76 pass rule

Because R76 is an absolute single-screenplay qualification rather than an A/B treatment-effect experiment:

Per-judge PASS:
- whole-episode mean >=7.0
- scene-sample mean >=7.0
- CHARACTER_VOICE mean >=6.5
- KOREAN_SPOKEN_NATURALNESS mean >=6.5
- no critical violation

Aggregate PASS:
- at least 2/3 judges PASS
- pooled median whole-episode axis score >=7.0
- pooled median scene-axis score >=7.0
- no critical violation independently confirmed by >=2 judges

This threshold is already frozen for R76 and should not be changed in response to observed judge outputs.

Important claim boundary:
This qualifies absolute virtual-provider broadcast screenplay quality only.
It does not prove an improvement effect against ENG:R47 or another renderer.
It does not establish actual OpenAI API equivalence.
It does not promote Production or activate Operational Level-3 by itself.

## 7. Required judge execution procedure

1. Verify packet SHA before dispatch.
2. Start J01 in a fresh conversation/context.
3. Give only:
   - judge instruction
   - whole-episode screenplay-only packet
   - pre-frozen scene packet
   - JUDGE_ID
4. Explicitly prohibit:
   - project/GitHub search
   - prior chat access
   - hidden-plan requests
   - other judge outputs
   - guessing model/candidate identity
5. Require JSON-only output.
6. Preserve the first complete valid output. Do not ask a judge to improve an unfavorable score.
7. Hash and seal the raw judgment.
8. Repeat separately for J02 and J03.
9. Validate schema before reading aggregate result:
   - correct judge_id
   - all 8 whole-episode axes
   - all 6 scenes x 8 surface axes
   - reconstruction section
   - critical-violation list
   - strengths / weaknesses / notes
10. Seal 3/3 judgments before aggregation.
11. Run the frozen aggregation exactly once.
12. Preserve unfavorable valid result unchanged.

## 8. What must NOT be sent to judges

Do not send:
- R76 internal virtual evaluation scores
- R76 hidden Episode/Sequence/Scene contracts
- obligation IDs or transaction roles
- Text Canonical State Ledger
- expected reconstruction answer
- DB64 source evidence
- R74/R75/R76 research history
- “Candidate passed internal test” statements
- Production/Candidate identity
- desired result or threshold explanation beyond the scoring rubric
- another judge's comments

Coordinator-only material must remain physically separate from judge packets.

## 9. Result reporting

Developer final report must contain four separate sections.

A. Mechanical validity
35,333 chars / 9 sequences / 52 scenes / leak and duplicate checks.

B. External literary quality
Judge-by-judge scores, medians, PASS/FAIL, critical findings.

C. Output-only recoverability
Which planned-looking structures are actually reconstructable from the screenplay, and which are only inferred.

D. Claim boundary
State exactly what the result does and does not establish.

Never merge A-D into one overall subjective score.

## 10. If R76 fails external blind

Do not return to broad component research.

Procedure:
1. Identify the failed dimension from convergent judge evidence.
2. Locate the Responsible Ancestor:
   - Episode architecture
   - Sequence architecture
   - Scene architecture
   - Scene contract
   - Renderer/surface realization
   - Voice/naturalness
3. Make one bounded repair.
4. Freeze a new fresh full-scale episode.
5. Generate >=35,000 chars again.
6. Repeat external blind.

Do not rewrite the already-judged R76 script and re-score it as though it were the same experiment.

## 11. If R76 passes

1. Seal R76 external result.
2. Preserve the finished screenplay and all raw judge outputs.
3. Perform evidence-backed Text Canonical State Commit only from screenplay evidence.
4. Begin R77 EP01 -> EP02 -> EP03 broadcast-scale State Carry.
5. Each episode must again reach real screenplay Surface; do not validate carry on plans alone.
6. Operational Level-3 and Production promotion remain separate later gates.

## 12. Historical lessons condensed

- R58: architecture can pass independently while surface remains unqualified.
- R62: mechanical improvement can coexist with external quality FAIL.
- R66: hidden mapping + 3 independent judges + frozen majority gate can close a component claim cleanly.
- R70: provider validity does not equal literary-quality validity; lost coordinator mapping can invalidate formal adjudication even when generations are valid.
- R133: internal high scores can collapse under external blind.
- R136-R138: “almost all gates pass” is still FAIL if a preregistered gate fails.
- R59/R60: planner intention is not canonical state unless the finished text evidences it.

These lessons define the R76 external-evaluation discipline.
