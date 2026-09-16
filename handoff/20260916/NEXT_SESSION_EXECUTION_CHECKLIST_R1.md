# NEXT SESSION EXECUTION CHECKLIST R1

Date: 2026-09-16

## A. Recovery

- [ ] Read `START_HERE_SYNC_R53_POSTSESSION_RESEARCH_HANDOFF_R1.md` first.
- [ ] Confirm physical baseline is SYNC-R53, not R52.
- [ ] Verify container/runtime minimal I/O before touching large packages.
- [ ] Mount/verify all nine developer-held R53 packages.

## B. Rebuild

- [ ] Reconstruct R53 in required read order.
- [ ] Reapply post-R53 Candidate research gates UL-11/UL-12/UL-13 plus earlier UL-1..UL-10 lineage.
- [ ] Preserve ENG:R47 Production unchanged.
- [ ] Preserve DB59 authority unchanged unless a separately authorized DB promotion occurs.
- [ ] Use a new SYNC successor number; do not rewrite R54/R55/R56 history.

## C. Physical custody gate

- [ ] Build PASS.
- [ ] CRC/binary integrity PASS.
- [ ] Per-package SHA PASS.
- [ ] C2 reconstruction PASS.
- [ ] C1/C2 Candidate Overlay identity PASS.
- [ ] B1/D1/D2 unchanged checks PASS.
- [ ] Narrative Engine Master canonical reconstruction PASS.
- [ ] DB59 canonical reconstruction PASS.
- [ ] Conversation attachment existence 9/9 PASS.
- [ ] User-visible download 9/9 PASS.
- [ ] Hub Physical Package Manifest complete.
- [ ] Durable archive locator verified for all nine payloads.

## D. Research continuation

- [ ] UL-13 Stage-1 external Surface-only blind evaluation.
- [ ] Seal Stage-1 responses.
- [ ] UL-13 Stage-2 plan reveal and fidelity evaluation.
- [ ] Keep mapping secret until protocol permits reveal.
- [ ] Do not claim external PASS before responses are collected.

## E. Live Provider qualification

- [ ] Use fresh isolated OpenAI Responses API contexts.
- [ ] Do not paste API keys into ChatGPT.
- [ ] No `conversation` reuse.
- [ ] No `previous_response_id` reuse.
- [ ] Stable candidate chain_id.
- [ ] Unique execution_nonce per provider call.
- [ ] Real response id/request id/model/usage receipts.
- [ ] Sibling candidates isolated.
- [ ] FULL/RECENT5 arms isolated.
- [ ] Target unopened until selector freeze.
- [ ] Counterfactual divergence for public-work memorization control.

## F. Promotion boundary

Do not promote the Candidate to Production until live provider, external blind, end-to-end surface, state-carry/regression and complete physical custody requirements are all satisfied.

Until explicit promotion:
`PRODUCTION_ENGINE = ENG:R47`.
