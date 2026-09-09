# P07 Semantic Contract Alignment Provider-Analog Candidate R1 — Result

Date: 2026-09-09

## Classification
`PASS_PROVIDER_ANALOG_ENGINEERING__LIVE_GATE_PENDING__NO_ACTIVE_ENGINE_PROMOTION`

Parent active physical authority remains:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R3`.

## Scientific / engineering result
- Parent nonhistorical baseline: 258/258 PASS.
- New semantic-alignment tests: 23/23 PASS.
- Candidate full nonhistorical regression: 281/281 PASS.
- I4H protected runtime files: 8/8 byte-identical.
- DB59 frozen SHA256 unchanged: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- RFV2 frozen index SHA256 unchanged: `e13b55f940ad3395e6db2a63829cc70e4754acd7438104ee2aba1ee07b0905cb`.

Provider-Analog matrix:
1. compliant all-positive packet: PASS; SCENE_PLAN reached; 9/9 semantic contract edges ACCEPT; receipt chain PASS;
2. preserved valid negative packet: HOLD / VALID_SEMANTIC_HOLD; raw 13 positive / 2 negative; unfulfilled_count=2; REPAIR_CHILD;
3. cross-group invalid packet: HOLD / SEMANTIC_JUDGE_INVALID_HOLD; JUDGE_INVALID; no fabricated literary unfulfilled_count;
4. archived Codex packet remains JUDGE_INVALID with raw 13 positive / 2 negative and is not rewritten as PASS.

## Root causes and fixes
- Primary engine defect: Judge prompt/payload omitted the same-group-only/per-obligation allowed-evidence rule while validator enforced it. Fixed by explicit allowed_evidence_ids + obligation_group alignment and strict validator enforcement.
- Reporting defect: invalid judge packets could be confused with literary nonfulfillment. Fixed by separating raw judge counts from validated semantic counts.
- Summary bookkeeping defect: an early result projection could report SCENE_PLAN=false despite execution. Final evidence uses server-observed stage calls plus engine contract verdicts.
- Harness termination defect: local Provider-Analog server thread was not shut down in one harness revision. Restored shutdown/server_close/join with termination assertion.
- Combined-command timeout: regression + multiple DB59-backed analog modes exceeded a short shell budget. Final runs were separated; no engine result changed.
- First physical C2 candidate build omitted two frozen Codex fixture JSON files. That build was discarded. Rebuild includes both fixtures; packaged second-pass is 23/23 + 281/281 PASS.

## Physical packaging
This cycle changes only CONTROL, A, B2, C2-A, C2-B. B1, C1, D1, D2 remain byte-identical parent references.

Composite candidate package-set SHA256:
`597d31f7513ce5eeaff22e607784d23a874155c2b60944657e83add03e30f2ae`

Combined candidate C2:
- bytes: 318655027
- entries: 3804
- SHA256: `dc82b881a43c1624af023438fccb4ceda6b0776e489bf27a23467ec11016e7f5`
- CRC PASS / duplicate 0 / unsafe 0.

## Claim boundary
This is not actual OpenAI Live qualification. Provider-Analog runs are explicitly `provider_backed=false`. Candidate code is physically packaged for reproducible continuation but is not appended to the active materialization order. Actual OpenAI Live confirmation remains pending.

Production ENG:R47, Formal 137, latest Formal R138, R140 0/0/0, I4I 0/0/0/0 remain unchanged.
