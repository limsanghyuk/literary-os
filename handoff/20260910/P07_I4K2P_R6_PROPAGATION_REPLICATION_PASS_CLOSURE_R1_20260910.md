# P07-I4K-2P R6 Five-Attempt Target-Aware Propagation Replication — PASS Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-2P-R6-FIVE-ATTEMPT-TARGET-AWARE-PROPAGATION-REPLICATION`
Preregistration commit: `23a5aeccefe5594dfed181bce42c30bc2062c2bf`
Prescore mask seal commit: `de8907def29855e0c7717a3e770ed2dc8f7195af`
Blind score seal commit: `cb5ca8d1e8409a23e7f4d33b4fb788652538408b`
Final verdict: `PASS_TO_I4K3_PREREG`

## Prospective integrity
- Parent: Research Sync R11 / material `b7a6df5d175c0d8bd6e60243044934c8250d99e486fe124e655d880cd19995f6`.
- Completely fresh world `느린강 저녁문화교실 연합`; no R1–R5 candidate reuse.
- Only operational change from R5: provisional max attempts 3 → 5. Field budgets, target-aware parity, State Attachment, Propagation Contract, hard gates, and H1–H4 were unchanged.
- Preregistration sealed at output 0.
- 12 BASELINE + 12 PROPAGATION final candidates admitted; max attempts actually used = 3.
- State Attachment 24/24; Treatment Propagation Contract 12/12; hard-gate violations 0.
- Arm mean total representation gap 2.212% <= 5%; non-target field means identical across arms.
- 24×7 = 168 masked same-agent blind values were sealed before unblind.

## Results
- BASELINE: all-7 `8.595238`; ensemble+future `8.041667`; causal fit `8.958333`; institutional+specificity `8.604167`.
- PROPAGATION: all-7 `9.071429`; ensemble+future `9.250000`; causal fit `9.041667`; institutional+specificity `8.666667`.
- H1 PASS: ensemble+future delta `+1.208333` >= `+0.20`.
- H2 PASS: all-7 delta `+0.476190` >= `+0.10`.
- H3 PASS: causal-fit delta `+0.083333` >= `-0.10`; institutional+specificity delta `+0.062500` >= `-0.10`.
- H4 PASS: integrity/contracts/parity/hard gates all PASS.

Post-I4K2P-R6 full nonhistorical regression was reconstructed from the authority-declared materialization order and exact 258-node collection; three disjoint 86-test batches all passed: `258/258 PASS`.

## Claim boundary
This is Development/Preformal masked same-agent evidence; blindness is not independently provable. It authorizes **I4K-3 preregistration only after Research Sync R12 physical closure**. No Active Engine, Production, DB59, Formal count, R140, or genuine OpenAI Live promotion.