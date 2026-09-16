# UL-15 — Adaptive Multi-Obligation Showrunner Contract R1

Date: 2026-09-16
Status: **PREREGISTERED DESIGN / REFERENCE IMPLEMENTATION AVAILABLE / MAIN-PATH ADOPTION PENDING**
Depends on: UL-14 defect closure
Physical authority: SYNC-R53 unchanged
Production: ENG:R47 unchanged

## 1. Purpose

Replace the old forward-planning pattern of a small fixed axis set plus single-owner sequence allocation with an adaptive dramatic-obligation system that can represent ensemble drama, changing relationships, causal events, information asymmetry, social ecology, plants/payoffs and long-horizon debts without forcing fixed sequence/scene counts.

This is a forward-generation contract. Legacy `EpisodeSynopsisPlan.v0.3-r1` is analytic/reverse-engineered only for the Candidate path.

## 2. Core object — Obligation Portfolio

Each active obligation is typed as one of:
- `EVENT`
- `CHARACTER`
- `RELATIONSHIP`
- `INFORMATION`
- `SOCIAL_GROUP`
- `WORLD_STATE`
- `PLANT_PAYOFF`
- `LONG_HORIZON_DEBT`
- `THEMATIC_FUNCTION`

Minimum obligation fields:
- `id`
- `type`
- `owners[]`
- `entry_state`
- `desired_delta`
- `urgency`
- optional `horizon/deadline`
- `dependencies[]`
- `conflict_targets[]`
- `defer_cost`
- `evidence_refs[]`
- `episode_function_refs[]`

No axis-count quota is allowed.

## 3. Episode decision layer

The Episode Planner must decide, rather than inherit a template:
1. episode dramatic function;
2. which obligations are active now;
3. which obligations are selected, deferred, transformed or dropped with reason;
4. whose state changes are essential this episode;
5. which obligations must collide, cooperate, reveal, constrain or pay off;
6. what residual pressure exits the episode;
7. where a responsible-ancestor replan is required when a lower-level plan cannot satisfy the portfolio.

`DEFER` is an episode-level disposition. It is never a sequence owner.

## 4. Ensemble / social ecology layer

Character ownership is many-to-many.

The planner must preserve:
- relationship states and power/debt/trust changes;
- group/family/organization membership where supported by evidence;
- information access differences;
- event ownership and consequences;
- subplot re-entry after absence;
- cross-owner collision and convergence.

When social-ecology evidence is absent, status is `UNKNOWN_OR_DERIVATION_REQUIRED`; the planner may not invent a fully observed group graph and label it sourced.

## 5. Episode Weave Graph

Nodes are selected obligations and/or generated sequence transactions.

Allowed edge families include:
- causal: triggers, enables, constrains, damages, reveals, transfers ownership, pays off, forces choice;
- functional: thematic contrast, mirror, counterpoint, obligation advance;
- relationship: alliance/rupture/debt/power/trust transfer;
- information: conceal/reveal/misbelief/publicization/access change.

Every edge requires provenance and a removal/counterfactual test where applicable. Decorative links do not count as weaving.

## 6. Sequence Transaction Plan

A Sequence is not an axis bucket. It is a variable-length dramatic transaction.

Required fields:
- `id`, `order`;
- `primary_owner`;
- `co_owners[]`;
- `obligation_ids[]` — one or more;
- `prerequisites[]`;
- concrete transaction/action;
- state deltas by obligation;
- required turn/reversal/decision/reveal where justified;
- exit pressure;
- `downstream_consumers[]`.

A sequence may consume several obligations simultaneously. It may also be a justified independent obligation sequence if removal would materially weaken episode function/debt progression.

No fixed sequence count is allowed. Corpus sequence-count distributions are anomaly diagnostics only.

## 7. Scene Transaction Plan

A forward Scene Plan must exist before surface rendering.

Required semantic decisions:
- scene necessity;
- sequence parent and obligation IDs;
- actors and concrete ownership;
- goal;
- opposition/constraint;
- physical action or failed action;
- information access/change if relevant;
- relationship transaction if relevant;
- props/place/time constraints when they matter;
- `pre_state`;
- `post_state`;
- downstream consumer;
- merge/split test;
- subtext/exposition constraint.

A scene may be split only when distinct dramatic transactions, location/time constraints or incompatible state changes justify the split. It should be merged when one transaction can carry the required deltas without loss.

No fixed scene count is allowed. A 45–50-scene / 9–10-sequence broadcast shape is a useful scale reference, not a generation target.

## 8. Surface boundary

Surface rendering is forbidden before Episode, Sequence and Scene transaction gates pass.

Renderer rules preserved from craft requirements:
- dialogue should not restate plot/state/psychology that can be carried by direction/action;
- emotional change is preferentially physicalized through expression, gesture, hands/props, movement, position, hesitation, failed action, silence and choice;
- direction may carry setting, action, emotional state and performance guidance in detail;
- >=35,000 Korean characters is a delivery-floor target for a full broadcast episode, not an architecture quota.

## 9. Reverse reconstruction and state carry

After surface generation:
1. reconstruct Scene transactions from surface;
2. reconstruct Sequence transactions from scenes;
3. reconstruct Episode obligations/function from sequences;
4. compare to frozen plans;
5. commit only observed/authorized state changes;
6. use Responsible-Ancestor Replan when divergence traces to an upper decision.

Do not repair upper-layer failures by surface paraphrase alone.

## 10. Quality diagnostics — not generation quotas

Measure at minimum:
- obligation disposition completeness;
- primary-owner dominance;
- co-owner participation;
- multi-obligation sequence share;
- cross-owner weaving;
- relationship-state movement;
- information-state movement;
- plant/payoff progress;
- downstream consumption;
- scene necessity/removal sensitivity;
- repeated/generic transaction rate;
- sequence-length variability;
- scene-count / sequence-count position relative to authored corpus distributions.

No single statistic is a pass by itself. In particular, obligation coverage alone is insufficient.

## 11. Reference implementation R1

A research reference implementation accompanies this contract:
- `research/upper_layer/ul15/adaptive_obligation_planner_r1.py`
- `research/upper_layer/ul15/AdaptiveMultiObligationShowrunnerPlan.v1.schema.json`
- `research/upper_layer/ul15/test_adaptive_obligation_planner_r1.py`

Local preflight: `5/5 PASS`.

Reference hashes:
- planner: `c52435269730e344c5cc45111d7403e9a999384ecfd8c4ac798a9af419cf1649`
- JSON schema: `033e5bf90413daab16d3dc71f64a5d1aeef473a0302a2178def3d2106fbf4e76`
- tests: `27d61ef133614d86c7f3568b2e79181d6a65e4b83a19081cca865475dba44827`

The reference implementation proves contract executability only. It does **not** prove human-level planning quality or P07 Main-Path adoption.

## 12. Hard fails

Candidate qualification fails if any of these occur:
- fixed axis/sequence/scene quota injected into forward planning;
- old schema ID reused after semantic mutation;
- `DEFERRED` used as a fake sequence owner;
- sequence without obligation/state delta;
- scene without pre/post state and necessity/downstream contract;
- screenplay surface produced before planning gates;
- DB state present only in receipt but not causally affecting the plan;
- provider conversation carry contaminates fresh qualification;
- a virtual/mock run is described as live Candidate execution.

## 13. Qualification boundary

UL-15 status is:
`CONTRACT_AND_REFERENCE_IMPLEMENTATION_PASS__P07_MAIN_PATH_NOT_YET_ADOPTED__PROVIDER_NOT_YET_QUALIFIED`.

The next required work is UL-16 causal-adoption + provider qualification. No Production promotion and no new physical authority follow from UL-15 alone.