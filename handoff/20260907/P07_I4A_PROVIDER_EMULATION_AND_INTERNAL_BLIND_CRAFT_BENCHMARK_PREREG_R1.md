# P07-I4A Provider Emulation + Internal Blind Craft Benchmark — Preregistration R1

Date: 2026-09-07
Classification: DEVELOPMENT PRETEST / PREFORMAL / NO FORMAL COUNT DELTA
Parent authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I3_BROADCAST_BIDIRECTIONAL_LOOP_R1`
Parent package-set SHA256: `9e005a8093a24a1d64b6a2584d8b841eb1662d92902cffac94f1fa00b5af4952`
Parent C2 SHA256: `6abf3934a2434968a13ac9a83f5b86e97222fc5f1c97019caec7c64a66299e08`
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Formal scored count: 137
R140 attempts/outputs/scores: 0/0/0

## 1. Purpose
Before official OpenAI Live execution, construct a provider-emulation harness that reproduces the operational semantics of the intended OpenAI Responses API path as closely as possible without claiming Live receipts. Separately, calibrate and execute an internal blind craft benchmark for P07-I3 against human broadcast-script anchors under a judge design that corrects the known CT-17 score-compression failure.

## 2. Provider-emulation target
The emulation path must preserve the creative hierarchy:
`SERIES_PLAN -> EPISODE_ALLOCATION -> EPISODE_PLAN -> NARRATIVE_KNOWLEDGE_BUS/NAP -> ENSEMBLE_ECOLOGY_PLAN -> CANDIDATE/CRITIC/SELECTOR -> SEQUENCE_PLAN -> SCENE_PLAN -> SURFACE_REALIZATION -> DIAGNOSTICS -> RESPONSIBLE_ANCESTOR_REPLAN -> RELOWERING -> STATE_COMMIT/CARRY`.

Creative stages are to be treated as Frontier-LLM stages; Python/runtime remains orchestration, state, retrieval, validation, hashing, retry, fail-close, and receipt/trace infrastructure only.

Emulated provider receipt fields:
- provider=`OPENAI_EMULATED_NONLIVE`
- intended API=`Responses API`
- intended model family=`gpt-5.6-sol`
- stage
- request_id (synthetic `sim_...`)
- request_sha256
- response_sha256
- parent_binding_sha256
- model_requested
- reasoning_effort
- store flag
- input token estimate / output token estimate
- latency_ms
- attempt_no / retry_reason
- status
- live_call=false
- provider_receipt_eligible=false

Operational fault injection must cover at least: timeout, transient 429-like retry, malformed structured output, context-budget overflow sentinel, duplicate response sentinel, and partial-stage failure. Failures may not be silently accepted.

## 3. OpenAI-like settings discipline
For the shadow environment, freeze one intended model/settings profile for all creative stages unless a separate preregistration changes it:
- model: `gpt-5.6-sol`
- API family: Responses
- store=false
- reasoning effort: one frozen level per run
- no hidden stage-specific model substitution
- bounded output budget per stage
- request/response hash preserved

These values simulate the intended Live contract; they do not constitute an OpenAI Provider Receipt.

## 4. Internal blind craft benchmark rationale
CT-17 showed the old 12-axis simple average was invalid for discrimination: HUMAN ranked third and scores compressed heavily into 7–9. Therefore P07-I4A must not reuse that scoring aggregation unchanged.

## 5. Blind benchmark packet design
Target: P07-I3 final repaired screenplay vs human broadcast-script anchors.

The full episode itself is not scored as one monolithic document. Create matched anonymous packets by scene type and approximate length:
- A: confrontation / conflict
- B: quiet emotional / relational
- C: ensemble operational / social-ecology
- D: information revelation / reversal
- E: transition / comic relief / pressure release
- F: late-episode convergence / exit-pressure

Prefer 2 matched pairs per type where material allows (target 12 pairs). Each pair must hide source identity, title, episode number, known character names where feasible, and generation/human labels. Human and candidate packets should be approximately length-matched.

## 6. Judge calibration before P07-I3 scoring
No P07-I3 blind score is valid until the judge passes calibration:
1. Strong human anchor vs deliberately degraded/template text: human must win >= 90% of pairwise decisions.
2. Two plausible professional-level samples: judge must permit TIE/near-tie and must not force large numerical gaps without evidence.
3. Repeated shuffled-label packet: preference consistency >= 0.80.
4. Score-distribution compression sentinel: if >75% of axis scores fall in 7–9 or no score below 5 appears across calibration+test when clear degraded anchors are present, metrology HOLD.

## 7. Craft axes
Use 10 craft axes, each 0–10 but do not decide by simple mean alone:
1. dialogue naturalness
2. character voice differentiation
3. subtext / implication
4. physicalization / playable action
5. scene objective-obstacle-turn clarity without exposition
6. emotional progression / reversibility
7. pacing / line economy
8. information control / exposition discipline
9. interpersonal specificity / non-generic behavior
10. scene ending pressure / carry-forward energy

Separate structural context axes (not compensatory with craft):
11. continuity/state fidelity
12. ensemble/social-ecology causality
13. thread/payoff/information continuity
14. episode/sequence functional fit

## 8. Non-compensatory floors
A candidate cannot be internally classified `HUMAN-COMPETITIVE` if any of the following median scores are below threshold:
- dialogue naturalness < 6.5
- character voice differentiation < 6.5
- continuity/state fidelity < 7.0
- unsupported invention critical violation > 0
- source/future leakage > 0

High structure scores may not compensate for failing naturalness/voice floors.

## 9. Primary comparison metric
Primary = forced pairwise preference by packet with options `LEFT / TIE / RIGHT`, plus confidence LOW/MEDIUM/HIGH and 1–3 concrete evidence points.

Report candidate win / tie / human win counts overall and by scene type. Numerical axis scores are secondary diagnostics.

Interpretation bands for internal development only:
- candidate win rate (ties split 0.5) >= 0.60 and all floors pass -> `INTERNAL_HUMAN_COMPETITIVE_SIGNAL`
- 0.45–0.60 -> `INTERNAL_NEAR_PARITY / IMPROVEMENT_REQUIRED`
- <0.45 -> `INTERNAL_CRAFT_GAP`

These are development signals, not external validation.

## 10. Known risk hypotheses to inspect
Based on prior CT evidence and P07-I3 architecture, inspect specifically for:
- voice homogenization across characters;
- polished but generic LLM phrasing;
- explanatory dialogue that states plan/subtext explicitly;
- repeated scene-entry or scene-exit rhythms;
- over-structured beats that reduce surprise;
- ensemble ownership improving structurally but supporting characters still sounding functionally interchangeable;
- action lines that describe emotion rather than dramatize it;
- excessive competence/clarity vs human-script messiness and local specificity;
- transition scenes that exist to satisfy architecture rather than create new dramatic value.

## 11. Internal-vs-external separation
Internal judge may guide engineering but cannot promote Production. External human/script-editor evaluation remains a separate later gate. Current assistant-as-judge is not independent even when label-blinded; report it as `INTERNAL_SINGLE_MODEL_BLIND_OR_SEMI_BLIND` unless a genuinely independent judge is used.

## 12. Current-input availability rule
Direct P07-I3 text scoring may proceed only from exact sealed screenplay bytes (expected final surface SHA256 `d4f60d3cfc3064ec326954e776272df9dacaf1cd8ac551f88395dac04bbccf63`) or a verified byte-identical copy. If those bytes are not available to the judge runtime, do not fabricate a blind score; report `BLIND_TEXT_INPUT_HOLD` while preserving this preregistration.

## 13. Pass/next-step rule
P07-I4A is complete only when:
- provider-emulation mechanics PASS;
- blind judge calibration PASS;
- exact P07-I3 screenplay bytes are scored against matched human anchors;
- improvement targets are identified from evidence;
- any accepted code/research change is physically propagated to 5 Parts / 9 Packages.

This is not CP1 Live, official R-F, R-G, Production promotion, or Formal R140.