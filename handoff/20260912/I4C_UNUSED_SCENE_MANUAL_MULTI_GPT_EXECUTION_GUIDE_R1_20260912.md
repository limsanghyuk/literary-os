# I4C UNUSED-SCENE MIXED-CRAFT REPLICATION — MANUAL MULTI-GPT EXECUTION GUIDE R1

Date: 2026-09-12
Parent physical authority: SYNC-R32
Experiment: I4C unused-scene mixed-craft independent annotation replication
Current state: PACKETS_SEALED__RESPONSES_0__REPLICATION_MAPPING_CLOSED

## Historical method basis
This guide deliberately inherits the execution method used by the prior I4K-5 independent external GPT gate:
- each judge runs in a separate fresh GPT conversation outside the Literary OS Project and outside the coordinator conversation;
- judge receives only its own anonymized packet and common contract, never the mapping, GitHub/Hub material, prior scores, or another judge response;
- no cross-judge discussion before all required responses are sealed;
- record model/config and independence attestation;
- seal each returned response before any unblind.

This is independent external GPT evaluation. If all three are the same GPT model family, the claim boundary is same-family independent external GPT replication, not cross-family or human consensus.

## Files to release
Use the already sealed dispatch bundle:
`I4C_UNUSED_SCENE_MIXED_CRAFT_J01_J03_DISPATCH_BUNDLE_R1.zip`
Bundle SHA256: `ccbe1b37d3f7bc045985e654855c701e5e3cd99cca98dca8b81810c0c9ccf59d`

The operator must extract it locally and release only the file clearly marked for the target slot:
- J01 receives only J01 packet
- J02 receives only J02 packet
- J03 receives only J03 packet

Expected packet SHA256 values from the sealed manifest:
- J01: `5b9f56f1ff034bc6b2b760646bcac4ef5432bd1e89c7a354f0ae8d9cffd823c7`
- J02: `e007411a395f70676391673082e98e0e922ff487361aaf5ade59cbc419d7b465`
- J03: `6d9ebc75dccb7999c96946d5fec84e9ccc8c0f6120fcfccb203ba235a0e87a1d`

Never release the replication mapping. Mapping SHA256 is only a custody seal:
`46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`

## Operator procedure
1. Open three completely separate NEW GPT conversations. Do not use this Literary OS Project conversation and do not continue an old conversation.
2. Prefer the same capable model/config for comparability (historical I4K-5 used GPT-5.6 Sol / High), but record the exact visible model/config each time.
3. Name the conversations locally J01, J02, J03 for operator convenience only.
4. In J01 attach only the J01 packet, then paste the J01 launch instruction below.
5. In J02 attach only the J02 packet, then paste the J02 launch instruction below.
6. In J03 attach only the J03 packet, then paste the J03 launch instruction below.
7. Do not show any session another judge's answer, this guide's mapping SHA interpretation, historical Stage-B winners, scene positions, GitHub, R4A materials, or coordinator analysis.
8. Each evaluator must return one JSON object/file only under the frozen response contract. Concise evidence notes are required; hidden chain-of-thought is neither requested nor accepted.
9. Return the three JSON files to the coordinator conversation as attachments. Preserve them unchanged; do not manually merge or edit scores.
10. The coordinator validates J01/J02/J03 separately with `I4C_UNUSED_SCENE_MIXED_CRAFT_RESPONSE_VALIDATOR_R1.py`.
11. Only after all three are valid, run `I4C_UNUSED_SCENE_MIXED_CRAFT_3OF3_GATE_R1.py`.
12. Only `PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED` permits regeneration/opening of the replication mapping once.

## Frozen scoring meaning
For each opaque scene AP01-AP12 and each of the eight axes:
- 0 = no material deficit
- 1 = minor/local deficit
- 2 = material scene-level deficit

Axes, exact keys:
1. `DIALOGUE_SUBTEXT`
2. `CHARACTER_VOICE`
3. `RELATIONSHIP_STATUS_PRESSURE`
4. `PHYSICALIZATION_ACTION`
5. `PACING_ESCALATION_TIME_PRESSURE`
6. `ENSEMBLE_WORLD_SPECIFICITY`
7. `INFORMATION_REVEAL_IRREVERSIBILITY`
8. `LINE_ECONOMY_RHYTHM`

The evaluator judges only the text in the attached packet. It must not guess whether a scene is early/middle/late and must not compare against hidden historical winners.

## Required response JSON schema
```json
{
  "evaluator_id": "J01",
  "provider_or_human": "ChatGPT",
  "model_config_or_human_metadata": "EXACT MODEL / THINKING CONFIG AS SHOWN",
  "independence_attestation": true,
  "scenes": [
    {
      "opaque_id": "AP01",
      "scores": {
        "DIALOGUE_SUBTEXT": 0,
        "CHARACTER_VOICE": 0,
        "RELATIONSHIP_STATUS_PRESSURE": 0,
        "PHYSICALIZATION_ACTION": 0,
        "PACING_ESCALATION_TIME_PRESSURE": 0,
        "ENSEMBLE_WORLD_SPECIFICITY": 0,
        "INFORMATION_REVEAL_IRREVERSIBILITY": 0,
        "LINE_ECONOMY_RHYTHM": 0
      },
      "evidence_note": "Concise observable textual/behavioral evidence only."
    }
  ]
}
```
The `scenes` array must contain AP01-AP12 exactly once each. All eight axes must appear exactly for every scene, and every score must be the integer 0, 1, or 2.

## Launch instruction template
Replace only `[JUDGE_ID]` with J01, J02, or J03. Do not add project history or desired outcome.

> You are an independent blind evaluator in a pre-registered screenplay craft replication. Read only the attached evaluator packet. Do not search the web, GitHub, or prior conversations for this project. Do not ask for or infer hidden scene position, mapping, historical winner labels, treatment/control identity, or another evaluator's result.
>
> Evaluate all opaque scenes AP01-AP12 independently using the eight axes and 0/1/2 severity definitions contained in the packet. For every scene, provide all eight integer scores and one concise evidence note grounded only in observable dialogue, action, blocking, object use, rhythm, reveal, relationship pressure, or world specificity in that scene. Do not provide chain-of-thought; only concise evidence notes.
>
> Your evaluator_id is `[JUDGE_ID]`. Set `provider_or_human` to `ChatGPT`. Set `model_config_or_human_metadata` to the exact model/config visible in this conversation. Set `independence_attestation` to true only if this is a fresh independent conversation, you have not seen the hidden mapping, you have not seen another evaluator response, and you have no prior exposure to these exact opaque scenes in this evaluation context.
>
> Return exactly one valid JSON object matching the response schema in the packet. Include AP01 through AP12 exactly once. Do not add markdown commentary before or after the JSON. If file creation is available, also save the identical JSON as `[JUDGE_ID]_I4C_UNUSED_SCENE_MIXED_CRAFT_RESPONSE_R1.json`.

## Validity / replacement rule
A valid unfavorable response MUST NOT be replaced. A response may be redone only if it is protocol-invalid or malformed before mapping open. Do not inspect aggregate positional outcomes when deciding whether a malformed response is replaced.

## Claim boundary
Packet construction, three valid evaluations, or even a positive replication do not by themselves authorize a renderer patch, Active Engine promotion, Production promotion, Formal R140, or R4A unblind. This is knowledge-only replication of a mixed-craft positional hypothesis.
