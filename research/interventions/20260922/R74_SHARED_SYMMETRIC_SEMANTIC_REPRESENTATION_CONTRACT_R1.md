# R74 Shared Symmetric Semantic Representation Contract R1

Date: 2026-09-22

Status:
`FROZEN_BEFORE_BRIDGE_EXECUTION`

## Principle
One semantic meter, two arms.
Control and Treatment must be projected to one canonical schema before any F04/F06 scoring.

## Canonical record
Each canonical scene record must expose:
- canonical_scene_id
- canonical_sequence_id
- source_obligation_ids
- transaction_stage
- transaction_kind_role
- causal_role_profile
- state_delta_role_profile
- resolution_role
- deferred/open pressure set
- factual information/relationship/social delta roles
- dependency/precondition profile
- assigned source atom/obligation provenance

No arm identity field is available to the scoring functions.

## F04 scoring
Apply the exact R68 rule to canonical records:
- non-RESOLVE only;
- material-agnostic signature;
- >=3 equal normalized signatures => one repetition violation group;
- two occurrences allowed;
- RESOLVE excluded.

## F06 scoring
Apply the exact R69 counterfactual rule to canonical records:
- removal-loss test;
- immediate previous/next merge test;
- same sequence;
- same obligation-set compatibility;
- distinct transaction stages are not losslessly merged;
- protected contributions exactly N1-N5 from R69.

## Fail-closed requirements
If any required semantic role cannot be reconstructed from the arm output + frozen source bindings:
- mark scene/case `BRIDGE_UNRESOLVED`;
- do not assign zero F04/F06 violations;
- case is invalid for efficacy scoring.

## Symmetry tests
- identity parity;
- arm-swap invariance;
- serialization invariance;
- frozen R68 F04 regression;
- frozen R69 F06 regression.

## Prohibited shortcuts
- no use of existing Control validation issue strings as the Control score while computing Treatment from a different representation;
- no assumption that absent Treatment metadata means no violation;
- no arm-specific thresholds;
- no manual interpretation of scene quality;
- no story-material text in the normalized F04 signature.
