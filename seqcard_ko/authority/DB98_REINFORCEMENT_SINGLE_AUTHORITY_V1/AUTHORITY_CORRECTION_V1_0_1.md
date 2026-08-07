# DB98 Reinforcement Authority Correction V1.0.1

Correction ID: `DB98_REINFORCEMENT_AUTHORITY_CORRECTION_V1_0_1`  
Date: 2026-08-07  
Status: `ACTIVE_NONDESTRUCTIVE_CORRECTION`  
Parent authority: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1` / method version `1.0.0`

## 0. Purpose

This correction resolves authority drift discovered during the first source-grounded CT-07R application. It does not replace or silently rewrite the sealed master document. It states the current interpretation that new sessions must apply together with the master.

## 1. Active exact schema

The master authority was sealed when the exact schema path was:

`schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1.json`

Source-grounded application then demonstrated that `info_shift.mode` required three non-overlapping meanings that V1 could not represent without distortion:

- `RECALL`
- `MISINTERPRET`
- `INFER`

Therefore the active exact schema for all new authoring is:

`schemas/DB98_REINFORCEMENT_EXACT_SCHEMA_REGISTRY_V1_0_1.json`

The original V1 registry remains historical. When the master text and root pointer differ only on this schema path/version, **root pointer + this correction + schema changelog govern**. This is a schema correction, not a change to the CT-07 rollout threshold or Stage01–04 authority.

## 2. CT-07R measurement correction

The global rollout gate remains blocked. CT-07R was preregistered and source-grounded thick packets were sealed, but pre-score audit found that the v1.0 TN presentation could confound semantic mismatch with visible donor metadata.

The controlling experiment documents are now:

1. `docs/tracks/confirmatory/CT-07R_2026-08-07_db98_reinforcement_replication_prereg.md`
2. `docs/tracks/confirmatory/CT-07R_2026-08-07_prereg_amendment_v1_1.md`
3. `docs/tracks/confirmatory/CT07R_RENDER_PAYLOAD_CONTRACT_V1.json`
4. `docs/tracks/confirmatory/ct07r_packets/CT07R_PACKET_AUDIT_AND_CORRECTION_LEDGER_20260807.json`

The v1.1 amendment changes only renderer/control presentation before any score was observed. Frozen works, anchors, semantic donor mapping, metrics and thresholds are unchanged.

## 3. Required next action

The next semantic-gate action is no longer generic packet preparation. It is:

`CT07R_INDEPENDENT_KEY_SEAL_THEN_SANITIZED_BLIND_RENDER_AND_SCORE`

Sequence:

```text
independent target-function key author (blind to thick packets)
→ key SHA seal
→ derive sanitized T/TN renderer payloads under contract V1
→ independent blind renderer
→ independent blind judge(s)
→ unblind and compute preregistered metrics
→ developer accepts PASS/FAIL
```

No 98-work bulk Thick Sequence authoring may begin before a valid PASS + developer acceptance.

## 4. Completion and state truth

The following are NOT rollout authorization:

- CT-07 primary pilot PASS;
- CT-07R packet authoring complete;
- schema validation PASS;
- hygiene/reassembly progress on an individual work.

Until independent CT-07R measurement is validly completed, global state remains:

`FULL_THICK_ROLLOUT_BLOCKED_PENDING_CT07_REPLICATION`.

## 5. Core protection

This correction does not modify:

- Stage01–04 core schemas or meaning;
- canonical 9-key SceneCard;
- human thin authored_seq boundaries;
- legacy EXT6/PHASE02 completion status;
- retained Source Hold for `최강칠우`;
- no-auto-promotion policy.

## 6. New-session precedence addition

For DB98 reinforcement, read:

`root pointer → master authority → this correction → active exact schema → schema changelog → execution/validation → current gate status → work index → bootstrap`.

If a future correction supersedes this document, the root pointer must say so explicitly.
