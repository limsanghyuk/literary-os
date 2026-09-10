# P07-I4K-2R State-Attached External Mechanism Replication — Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-2R-STATE-ATTACHED-EXTERNAL-MECHANISM-REPLICATION`
Classification: DEVELOPMENT / PREFORMAL / MASKED SAME-AGENT
Final verdict: `FAIL__H3_ENSEMBLE_FUTURE_MARGIN_BELOW_PREREG_THRESHOLD__NO_I4K3_ENTRY`

## Prospective integrity
- Parent physical authority: Research Sync R5 `b8c4d28370e6166851cd996bf89a37892268524824b00c511a3338f85031c87b`.
- Preregistration was sealed before candidate generation; prereg SHA256 `155e61aa0b836e31d58779180e8e4ac60f58bad8f1aa632346503e111c253b7b`.
- Arms: Internal-only 16 / External-unattached 16 / External-state-attached 16.
- Candidate bytes were restored after session compaction only because all three exact prior sealed SHA256 values matched 3/3; no candidate text was altered.
- Prescore integrity PASS; representation-parity max relative text gap 0.14626067 <= 0.15; State Attachment Contract 16/16 PASS; hard-gate violations 0.
- Secret mask SHA256 `6f195ff218ce9f63a33f5189376d971612d825506f96e359cff55a40ed9e1300` was sealed before scoring.
- 48 blind rows / 336 values were scored on neutral IDs only. Masked score SHA256 `d050f5b6d673f69051af29ae0f722777837d15c49cc41923e9a7c030672f9708`; score seal recorded map unopened for analysis.

## Unblinded means
- Internal-only: causal fit 8.59375; institutional+specificity 8.140625; ensemble+future 8.500000; all-7 8.428571.
- External-unattached: causal fit 7.59375; institutional+specificity 8.453125; ensemble+future 8.250000; all-7 8.294643.
- External-state-attached: causal fit 9.125000; institutional+specificity 8.734375; ensemble+future 8.609375; all-7 8.745536.

## Preregistered hypotheses
- H1 PASS: Attached causal-fit minus Unattached `+1.53125`; minus Internal `+0.53125`.
- H2 PASS: Attached institutional+specificity minus Unattached `+0.28125`; minus Internal `+0.59375`.
- H3 FAIL: Attached all-7 margin over best comparator `+0.316964` passes the `+0.20` condition, but ensemble+future margin is only `+0.109375`, below the frozen `+0.15` threshold.
- H4 PASS: hard gates/parity/attachment/quota requirements pass; Attached causal-fit >=6.5 is 16/16.

## Interpretation / claim boundary
State attachment repaired the specific causal-fit defect found in I4K-2 while preserving external-mechanism institutional/non-generic value. However the broader propagation requirement did not fully pass: the attached arm did not add enough incremental ensemble activation plus future sustainability beyond the best comparator.

The threshold is not changed after output. I4K-2 and I4K-2R both remain FAIL under their own preregistrations. Do **not** enter I4K-3. The next correct research boundary is diagnosis of second-order ensemble/future propagation, followed by a separately preregistered fresh propagation-focused replication if justified.

Post-I4K2R nonhistorical regression: `258/258 PASS`.
No Active Engine, Production, DB, Formal count, R140, or OpenAI Live promotion.