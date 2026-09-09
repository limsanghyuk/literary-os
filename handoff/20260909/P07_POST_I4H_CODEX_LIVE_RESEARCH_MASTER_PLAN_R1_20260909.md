# P07 Post-I4H / Post-Codex Live Research Master Plan R1

Date: 2026-09-09
Classification: DEVELOPMENT / PREFORMAL / PREOUTPUT

## Current authority lock
- Physical Authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R3`
- Package-set SHA256: `9327630e8fc8c9b88a8233055b939e08ab5d3726a777b44122bb6682a8c436f8`
- Combined C2 SHA256: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Production: `ENG:R47`
- Formal scored count: `137`
- Latest formal authority: `R138`
- R140: `0/0/0`
- I4I: `0/0/0/0`, unexecuted

## Track A — Semantic Contract Live Alignment
Active preoutput experiment:
`P07_LIVE_SEMANTIC_CONTRACT_ALIGNMENT_QUALIFICATION_R1`

Preregistration:
`handoff/20260909/P07_LIVE_SEMANTIC_CONTRACT_ALIGNMENT_QUALIFICATION_PREREG_R1_20260909.json`

Codex Live evidence is preserved as immutable HOLD evidence: real OpenAI generation 5/5 HTTP 200, but EPISODE→SEQUENCE semantic fulfillment stopped because the validator required same-group evidence while the judge instructions omitted that constraint. The prior response must not be edited into a PASS.

Critical structural finding: archived Semantic Contract Candidate R2/R3 sources exist inside C2, but they are not active in the current I4H Recovery R3 materialization. Therefore the next repair is a new isolated delta layered after the current R3 parent.

Required order:
1. Runtime/package preflight and parent lock.
2. Reproduce current-parent full nonhistorical regression before treatment.
3. Build isolated semantic alignment candidate only within preregistered scope.
4. Run deterministic/adversarial tests including exact Codex failure replay.
5. Run candidate full nonhistorical regression.
6. Seal deterministic fresh Live CASE-02 selection before first provider output.
7. Run one fresh Live attempt with no semantic cherry-pick retry.
8. Classify PASS / VALID_SEMANTIC_HOLD / JUDGE_INVALID_HOLD / INFRA_HOLD.
9. If any 5-Part/9-Package content changes, physically rebuild/audit/deliver every changed transport package before declaring new physical authority.

## Track B — DB64 Candidate Qualification
Queued and deliberately separated from Track A. DB59 remains the frozen control during Track A.

After Track A closes, DB64 reinforcement must be checked for:
- exact package authority, CRC/hash/parse/pairing and parent protected-byte invariance;
- C1-C5 implementation quality;
- C3 state semantics beyond simple before→after when trigger/exit/carry/next constraint matter;
- C5 Epistemic Status separate from owner grounding;
- A1 packet completeness: planning_question, target_consumer, execution_stage, selected_views, selected_record_ids, selection_reason, provenance;
- G1 authority/cutoff/version completeness;
- G2 responsible-ancestor repair receipt completeness;
- A2 actual engine selected-mutation effect plus irrelevant-unselected invariance;
- DB59-vs-DB64 paired causal/quality effect.

`A_SEMANTIC` does not by itself imply `CONSUMER_READY_A`.

## Track C — Hierarchy/Broadcast Continuation
Only after Track A is stable and the appropriate DB authority is selected:
- Sequence→Scene Live semantic gates;
- broadcast-scale floor diagnostics where applicable;
- I4H surface Live qualification;
- then I4I whole-episode execution.

I4I remains unexecuted until these prerequisites are closed or a pre-output amendment explicitly changes the order.

## Physical delivery rule
If research or experiment results cause actual changes to any of the 5 logical Parts / 9 transport packages, every changed transport package must be physically rebuilt, audited and delivered to the developer in the same closed research cycle. Byte-identical unchanged packages need not be regenerated solely for naming symmetry. Hub-only evidence is not a substitute for required changed physical package delivery.
