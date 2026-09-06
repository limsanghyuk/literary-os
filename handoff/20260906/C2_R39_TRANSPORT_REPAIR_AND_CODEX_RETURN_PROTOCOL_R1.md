# Literary OS — C2 R39 Transport Repair + Codex Return Protocol Index

Date: 2026-09-06

## Transport incident conclusion
The R11 C2 R38 ZIP had passed local CRC/nested-ZIP/Fresh Runtime verification, but the large single-file delivery object was not reliably downloadable. A later historical C2 copy was also observed truncated without a valid ZIP central directory. The repaired 311MB C2 outer ZIP itself passes CRC, so this is classified as a **large-artifact durable upload/transport failure**, not a candidate-engine semantic failure.

## Current delivery replacement
Use **C2 R39 Transport Repair** for delivery instead of the unavailable C2 R38 delivery object.

- filename: `LITERARY_OS_MANDATORY_CONTINUATION_PART-C2_ENGINE_MASTER_VOL2_CANDIDATE_R39_P07_RFV_R11_CODEX_TRANSPORT_REPAIR_20260906_SEALED.zip`
- bytes: `311653716`
- SHA256: `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`
- members: `3610`
- outer CRC: PASS
- duplicate paths: 0
- unsafe paths: 0
- nested ZIPs: 155/155 PASS
- executable runtime: `CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY/`
- runtime overlay files: 520
- fresh nonhistorical regression: 181/181 PASS
- scientific/runtime semantic change: NONE; packaging/transport repair only.

Because the 311MB single artifact may fail durable delivery, it is distributed as seven 48MiB-or-smaller binary parts with per-part SHA256 and a reassembly manifest/script. The streamed concatenation of part001..part007 reproduces the exact C2 R39 SHA above.

## Updated delivery manifest
`LITERARY_OS_R11_CODEX_HANDOFF_DELIVERY_MANIFEST_R2_C2_TRANSPORT_REPAIR_20260906.json`
SHA256: `4ddbaac1426b2c5f8073fb9811bca6f50171fef200847bb913c04c3df9dcf9f9`

## Updated Trust Root
`LITERARY_OS_R11_CODEX_HANDOFF_TRUST_ROOT_R2_C2_TRANSPORT_REPAIR_20260906_SEALED.zip`
SHA256: `40c44960b8e8f5a5295197ce3ec8d89f1e517f31be4f044daf83cd5bf97dc525`

## Formal experiment execution/evaluation/return protocol
Codex must also ingest:
`LITERARY_OS_R11_CODEX_FORMAL_EXPERIMENT_EXECUTION_EVALUATION_AND_RETURN_PROTOCOL_R1_20260906.md`
SHA256: `f7ab5f485c912189b83e3d271e6286987c8b0705efc5d19dfc69335db6d51fc0`

It defines: R-F purpose/method/order, R-G entry, Formal R140 purpose/hypothesis, Control/Treatment, source cutoff, broadcast-scale contract, blind 3-Judge protocol, 100-point rubric, G0-G9 gates, failure preservation, mandatory outputs, and the exact Codex -> ChatGPT return sequence.

## Scientific state unchanged
- Formal scored count: 137
- latest formal scored: R138
- R140: 0 attempts / 0 outputs / 0 scores
- R-F actual OpenAI live outputs / Provider Receipts: 0 / 0
- ENG:R47 immutable
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## Mandatory next action
Codex: download all C2 R39 split parts -> reassemble -> verify C2 SHA/CRC -> verify R11 runtime regression -> secure credential gate -> mint NEW R11 CP1 checkpoint -> R-F live paired smoke -> remaining R-F gates -> R-G freeze -> fresh deterministic sample -> revised R140 preregistration -> new G0 -> Formal R140 -> return all sealed outputs/receipts/judge results/manifests to ChatGPT for independent re-audit.
