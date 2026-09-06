# Literary OS — R11 RFV Codex/API Handoff

## Current scientific state
- P06 COMPLETED / PHYSICALLY CLOSED.
- P07 ACTIVE PREFORMAL / NOT COMPLETE.
- Formal scored count 137; latest formal R138.
- R140 formal 0 attempts / 0 outputs / 0 scores.
- ENG:R47 Production immutable.
- DB59 frozen SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- R-F actual OpenAI live outputs / Provider Receipts = 0 / 0.

## R11 package set
Read order: CONTROL R39 -> A R38 -> B1 R10 unchanged -> B2 R39 -> C1 R10 unchanged -> C2 R38 -> D1 R10 unchanged -> D2 R10 unchanged.

Executable candidate is C2 `CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY/`.

R11 integrity: fresh C2 regression 181/181 PASS; outer ZIP 8/8 PASS; duplicate/unsafe paths 0; nested ZIP 320/320 CRC PASS; Research Master reassembly `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0`; Narrative Engine Master reassembly `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`; DB59 reassembly `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## R-FV repairs propagated into R11
- Provider 2xx malformed/missing-id/refusal -> structured non-pass instead of uncaught exception.
- bounded retry for retryable timeout/429/5xx; failed attempts never become trusted Provider Evidence.
- returned model and request/response hashes bound to trusted transcript; mismatch blocks.
- strengthened hash fixture correction.
- packaging-only self-containment fix: six already-frozen R-E fixtures made package-local; no runtime policy/threshold change.

Preserved R-FV evidence: provider failure proxy 20/20 PASS after preregistered repair; focused adoption 60/60; behavioral adoption 35/35; R1-R134 direct/successor coverage 100/100; preseal 5/5.

## Critical supersession
The old R10 CP1 Checkpoint and Ready Packet were frozen before R-FV runtime repair. They are historical only and MUST NOT be used for live OpenAI execution.

Codex must mint a NEW R11 CP1 checkpoint after fresh verification and credential resolution.

## Codex credential gate
Before any API-backed run, Codex must inspect for a usable `OPENAI_API_KEY` without printing it, then ask whether to reuse an existing usable key or create a new one. If none exists, ask whether to create one securely. Never expose plaintext. If creating in Codex, use the secure OpenAI Platform Codex key flow and a developer-confirmed ignored local env file.

## Mandatory execution order
1. Verify all 8 package hashes against the R11 delivery manifest.
2. Fresh-extract C2 R38 current overlay and require 181/181 PASS.
3. Verify DB59 frozen SHA and R-F CP0 R0A/R0C constraints; source cutoff EP01-EP05, actual EP06 forbidden.
4. Resolve secure credential gate.
5. Mint NEW R11 CP1 checkpoint/ready packet.
6. Run CASE-01 Reference-vs-Engine paired live smoke under identical OpenAI Responses API / model / settings. Frozen intent: model `gpt-5.6-sol`, reasoning `low`, `store=false`. If unavailable, HOLD; never silently substitute.
7. Seal actual Provider Receipts for both arms. Provider/transport faults are non-pass infrastructure/provider states, not literary Craft FAIL.
8. CP1 failure blocks CP2/CP3; preserve all failures and amend before repair.
9. Only after R-F closes: R-G Freeze -> fresh deterministic sample -> revised R140 preregistration -> new G0 -> Formal R140.

No Formal R140 before these gates. Local/API Twin evidence cannot be promoted to live Provider evidence. Python must author zero literary prose.
