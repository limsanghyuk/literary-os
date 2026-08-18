# SequencePlan Pure-GPT → Literary-OS Ablation — 2026-08-19

Status: `PARTIAL_SUPPORT_PRIMARY_PREREG_GATE_FAIL`.

Fresh targets: 난폭한로맨스 EP09 / 닥터챔프 EP09 / 드림 EP09. Fifteen outputs were frozen before holdout opening.

Arms and medians:
- A0 plain-recap base GPT: 65
- A1 richer N-1 prose state, no LOS grammar: 76
- B LOS structured state + THICK + explicit Sequence grammar: 80
- C B + autonomous EpisodeSynopsisPlanLite: 82
- D C + five-work cross-work retrieval: 82

Median deltas: A1-A0 +11; B-A1 +4; C-B +2; D-C 0; D-A0 +17.

Preregistered conditions: 3/4 passed. The hierarchy threshold required C>=B+3 but observed +2, so the primary gate is FAIL, not PASS.

Interpretation:
1. A strong base model can reach low-70s on some episodes from a plain recap alone (닥터챔프 73), so a 71-level generic result is plausible in favorable states.
2. The biggest signal is state quality: richer N-1 state adds +11 median.
3. LOS structured representation + Sequence grammar adds +4 beyond rich prose state, though this contrast also adds THICK/structured representation and is not grammar-only.
4. EpisodePlan-first hierarchy is positive but weaker than the previous +5 internal signal; current replication is +2.
5. Current retrieval adds 0 median in this run.
6. Key failure: 드림 EP09. LOS overcommitted to dangerous-match continuation while canonical design escalated at a different level: monopoly licensing cancels the tournament and forces survival alliance. More correct state can harden the wrong plan when episode-axis selection is wrong.

Next priority: Episode Axis Selector + Escalation-Level Predictor + active-thread suppression/defer policy, followed by a larger fresh A0→A1→B→C→D replication with independent blind scorers.

Drama-data authority report: `limsanghyuk/v1700-literary-os/R21_PURE_GPT_TO_LITERARY_OS_ABLATION_RESULT_20260819.md`.