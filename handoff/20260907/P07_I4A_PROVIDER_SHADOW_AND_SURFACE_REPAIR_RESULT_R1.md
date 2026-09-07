# P07-I4A Provider Shadow + Internal Blind Surface Repair Result R1

Date: 2026-09-07
Classification: DEVELOPMENT PRETEST / PREFORMAL / NO FORMAL COUNT DELTA
Parent physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I3_BROADCAST_BIDIRECTIONAL_LOOP_R1`
Formal scored count: 137 (unchanged)
R140 attempts/outputs/scores: 0/0/0 (unchanged)
Live Provider evidence: FALSE

## 1. Frozen inputs and preregistration
- Provider emulation/internal blind preregistration: `handoff/20260907/P07_I4A_PROVIDER_EMULATION_AND_INTERNAL_BLIND_CRAFT_BENCHMARK_PREREG_R1.md`
- Surface repair preregistration: `handoff/20260907/P07_I4A_SURFACE_LITERARY_COMPRESSION_VOICE_REPAIR_PROBE_PREREG_R1.md`
- Surface repair preregistration commit: `b64c6cbca95aa6b267db5c9a45231ce89855da95`
- Current parent screenplay: P07-I3 50 scenes / 35,442 Unicode characters.

No preregistered threshold was changed after seeing results.

## 2. Baseline blind craft result
Calibrated internal blind judge first passed a human-vs-obvious-template calibration:
- human anchor choice: 10/10
- left/right reversal consistency: 1.00

P07-I3 baseline vs human broadcast-script anchors:
- Human: 12 wins
- P07-I3 Candidate: 0 wins
- Ties: 0

Observed surface bottleneck:
`INTERNAL_NARRATIVE_CONTROL_LOGIC_TO_SURFACE_EXPOSITION_LEAK`

Quantitative signal over the 12 matched excerpts:
- mean excerpt length: Human ~733 chars vs Candidate ~1,108 chars
- procedural/verification lexical density: Human ~0.21 / 1,000 chars vs Candidate ~18.32 / 1,000 chars
- mean non-empty line length: Human ~35.6 chars vs Candidate ~64.7 chars

Interpretation: narrative control/evidence discipline was leaking into dialogue and action description instead of being compressed into character-specific dramatic behavior.

## 3. Six-scene surface repair probe
Frozen repair scenes:
`S11 / S14 / S21 / S33 / S37 / S50`

Upper architecture, episode function, ensemble ownership, sequence order, information shift, relationship movement, and exit-state contracts were held fixed. Repair was surface-only under the preregistered principle:
`functional_truth != surface_visible_content`.

Repair blind gate before mapping disclosure:
- required Candidate wins >= 1
- required Candidate wins + ties >= 3 of 6

Blind judgments were sealed before mapping disclosure.
Judgment file SHA256:
`d5bd42ca79d8553be2a559be7b918270ca46bb3bdaf35270a347fcbc8fcdacce`

Mapping file SHA256:
`e2a74ffb736b990fcd886dcbc8e5c67d50c11d7cb5833033f1395a4bc60999b5`

After mapping disclosure:
- Human: 5 wins
- Candidate Repaired: 1 win
- Ties: 0

Candidate won only the investigative-reveal pair. It did not generalize across workplace, family-power, procedural, and exit-pressure scenes.

### Surface verdict
`SURFACE_REPAIR_INSUFFICIENT__HOLD_FULL_EPISODE_RERENDER`

Reason:
- Candidate win gate (>=1): PASS
- Candidate win+tie gate (>=3/6): FAIL (1/6)

Therefore the preregistered rule forbids expanding this repair into a full 50-scene rerender. The six-scene repair remains research evidence, not promoted surface policy.

## 4. Provider Shadow Live findings
The current semantic provider already records request/response hashes, requested/returned model, response id, x-request-id, usage, and trusted-transport evidence. Shadow testing found that retry behavior existed in `api_twin` but was not automatically adopted by the actual Live semantic-provider construction path.

Accepted operating repair:
- `ResilientSemanticProvider`
- bounded fail-closed retry, default max attempts = 2
- retryable transient classes include 429/500/503, timeout/network, incomplete response, JSON decode/provider JSON failures
- HTTP 400 and other non-transient failures do not retry
- per-attempt trace including distinct client trace ids and receipt fields
- canonical factory `build_live_semantic_provider()` wraps `OpenAIStructuredSemanticProvider` in resilience by default
- current external live validation runner uses the factory
- semantic requests carry `X-Client-Request-Id`

### Required Shadow Live scenarios
Using the canonical factory against a local Responses-like HTTP server:
1. permanent HTTP 429 -> 2 attempts -> ERROR -> provider claim BLOCK: PASS
2. HTTP 400 -> 1 attempt only -> ERROR -> provider claim BLOCK: PASS
3. returned model mismatch -> transport may return OK but trusted provider claim BLOCK: PASS
4. missing response-id -> fail closed / provider claim BLOCK: PASS
5. hierarchical planning failure -> State Commit path is not invoked: PASS

Factory-based Shadow result SHA256:
`c29872a462bd49d5bae88a3b05c801edb855057e6785837bf73cb11aef5c7319`

Provider resilience/fail-close/factory tests:
- 12/12 PASS
- extended fail-close tests included permanent 429, HTTP 400, model mismatch, missing response id, and state-commit prohibition.

## 5. Regression
Working overlay exact nonhistorical regression after provider changes:
- 205/205 PASS
- pytest exit code 0
- regression log SHA256 `ca55c3ed09481de20bc51c4c45e2a843f8ba4d5a1b743df884cf7cf51ad019db`

Six-scene repaired surface file SHA256:
`2e2e46ba868e4bd01283d89c2f125031c9ed8c23576e686409cf29544344d4c1`

## 6. Scientific interpretation
P07-I4A produces a split verdict.

### Provider operating track
`PASS__SHADOW_LIVE_PROVIDER_RESILIENCE_AND_FAIL_CLOSE`

The provider-emulation layer is materially closer to real OpenAI API operation and is suitable for later Live receipt validation. This does not constitute a real OpenAI Live call.

### Literary surface track
`HOLD__SURFACE_REPAIR_NOT_HUMAN_COMPETITIVE_ENOUGH`

The repaired six-scene sample shows a local improvement signal (1 human-comparative win) but fails the preregistered generalization gate. Full-episode rerender is prohibited.

## 7. Promotion decision
- Provider resilience/factory repair: ELIGIBLE FOR ENGINEERING ADOPTION after physical packaging/regression reseal.
- Six-scene literary repair policy: NOT ELIGIBLE FOR PROMOTION.
- P07-I3 50-scene screenplay remains the current broadcast development surface reference until a new preregistered surface intervention passes a blind gate.

## 8. Claim boundary
This result does NOT establish:
- OpenAI Live provider parity;
- external human craft equivalence;
- a successful full-episode surface repair;
- RFV3, CP1 Live, official R-F/R-G, Production promotion, or Formal R140.

The next surface-development unit must change the intervention itself rather than relaxing the blind threshold. The most likely target is the `Scene Plan -> Surface Realization` interface: voice-state conditioning, dialogue-information budget, relationship-specific behavior, and scene-level literary compression.
