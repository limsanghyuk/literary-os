# P07 I4I R2 Fresh Whole-Episode Replication Closure / Physical Research Sync R2

Date: 2026-09-10
Classification: DEVELOPMENT / PREFORMAL / VIRTUAL PROVIDER-ANALOG / CLOSED

## 1. FINAL SCIENTIFIC VERDICT

Experiment: `P07-I4I-R2-WHOLE-EPISODE-FRESH-REPLICATION`

Final verdict:
`CLOSED__PRIMARY_GATE_FAIL__FRESH_REPLICATION_POSITIVE_NONHARMFUL_SIGNAL__NO_PROMOTION`

The preregistered whole-episode primary threshold remains unchanged at Treatment-Control >= +0.30.
Observed fresh R2 whole-episode delta: `+0.16666666666666607`.
Therefore R2 is a PRIMARY FAIL. No threshold was relaxed, rounded, pooled with R1, or retroactively redefined.

I4I R1 remains independently closed as:
`CLOSED__PRIMARY_GATE_FAIL__POSITIVE_SCENE_LEVEL_SIGNAL__NO_PROMOTION`
with whole-episode delta `+0.2833333333333332`.
R1 and R2 are not pooled into a PASS claim.

## 2. FRESH R2 TASK

Synthetic source-free series: `남문박물관 사람들`
Episode: `빈 액자에 남은 이름`

Scale:
- sequences: 10;
- scenes: 50;
- Control Unicode chars: 35,738;
- Treatment Unicode chars: 37,939.

Control SHA256:
`d7596872d95375bc613372e07d3b5abafedd85bbba8a32f4fd34ad6fbd22d497`.

Treatment SHA256:
`33bc6c1150bc9333ceea8ab9adb1b840894a8d904300b3e1fd8664287eb9decc`.

Frozen plan hashes:
- Series/Episode `8057b6f8fc1c2681dd7259b29b5b9dbdd9dbdb99f49b9d628f71f5589d3a0c09`;
- Sequence Plan `b0a2296d580ce4b5184a6d405c74c992dc87e90a66908deaad3626b93242f319`;
- Scene Plan `459747d3653cb30200201f144e0c8fa31396976e2dc66106eb876045413057e4`;
- Complete Freeze Manifest `b3d08b6f81a80b60da372ed53a2ee9366c4a1e122927554cb9952f352569721d`.

## 3. EXECUTION BOUNDARY

The frozen R2 Scene Plan did not contain every semantic anchor required for a full current `SemanticSceneToRendererBridge` replay. This was discovered after Control sealing but before Selector/Treatment.

A non-result-changing execution adapter amendment was sealed before Selector outputs:
`handoff/20260910/P07_I4I_R2_EXECUTION_ADAPTER_AMENDMENT_R1_20260910.json`
Commit: `0b7e70fc404e9652707116d9cb220e583328c5f9`.

No missing semantic anchor was invented after Control seal. No full semantic-bridge execution claim is made for R2. The unchanged I4H Recovery R3 six-dimensional Selector and unchanged ABSTAIN/LOW/STANDARD revision constraints were used directly on the sealed Control scenes. Thresholds and claim boundaries were not relaxed.

## 4. SELECTOR / TREATMENT

Selector freeze:
- ABSTAIN: 29;
- LOW: 12;
- STANDARD: 9.

Selector ledger SHA256:
`5fccb3e0965dc291d9d68462e159e169988c1de219b6a45f668e5b01b5996475`.
Hub selector receipt commit:
`5869a45cea9fbe1c60a5ded8d676a8299882f0a8`.

Reliability/integrity:
- ABSTAIN byte identity: 29/29;
- intervention dialogue retention: 100%;
- unauthorized speaker: 0;
- participant/sequence/scene structural failure: 0;
- new foreign-script intrusion: 0;
- critical failures: 0;
- harmful intervention rate: 0%.

## 5. MASKED SAME-AGENT EVALUATION

This is not independent human evidence and not OpenAI Live evidence.
Evidence class:
`MASKED_SAME_AGENT__DEVELOPMENT_PREFORMAL__POLICY_BLINDNESS_NOT_INDEPENDENTLY_PROVABLE`.

Secret map SHA256:
`063fdebfac967630b5e96d4e63c381557b14d197552ad25db927c9c3428969e1`.
Blind score SHA256:
`71539c66ac2ff5a0f84cc191605ac9a607f86ebd7287a3284521c0044a34125e`.

Scores were sealed before unblinding.
Unblind result: A = Control, B = Treatment.

Whole-episode means:
- Control: 8.333333333333334;
- Treatment: 8.5;
- delta: +0.16666666666666607;
- axis nonloss: 12/12;
- maximum axis regression: 0.0.

Secondary scene-level diagnostics:
- LOW n=12, mean craft delta +0.300833..., nonloss 100%;
- STANDARD n=9, mean craft delta +0.526666..., nonloss 100%;
- harmful intervention rate 0%.

Mechanism groups:
- improvement-target axes mean +0.50;
- protection axes mean +0.0167, all nonloss;
- mixed-context axes mean +0.1333.

Secondary positives cannot compensate for the failed preregistered primary whole-episode gate.

## 6. POST-EXPERIMENT ENGINE SAFETY

Active engine parent after R2:
`P07-I4H Recovery R3`.

Post-R2 full nonhistorical regression:
`258/258 PASS`.

No runtime code, DB59, Production, Formal count, or R140 state was changed by R2.

## 7. DATABASE / OTHER RESEARCH BOUNDARIES

DB authority remains frozen DB59:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

DB64 / 9-Contract candidate remains HOLD and is not used as current DB authority.

`P07_SEMANTIC_CONTRACT_ALIGNMENT_VIRTUAL_R1` remains a virtual qualified shadow candidate requiring genuine OpenAI Live confirmation. It is not added to the active materialization order.

## 8. PHYSICAL RESEARCH SYNC R2

Research/evidence changes only. Runtime C2 and DB packages remain byte-identical.

Changed and newly delivered:
- CONTROL SHA256 `395badc00eb61b0997805fa41e9d82a55d951ba4bcffdf826f9bf5657975ebd3`;
- Part A SHA256 `47e7d622d1b7b4ea91f23ea52115cb4561ec24698a12a9f69a94939c9a32afca`;
- Part B2 SHA256 `71dc41bc47adca97fddd59ee3e95a6965256bf3aaf4d0de10e3e28dd1f1aae85`.

Reuse byte-identically from I4H Recovery R3:
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`;
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`;
- C2-A `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`;
- C2-B `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`;
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`;
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`.

Full logical nine-file material SHA256:
`6e630bf4039953bd7b9969735c87fe7f273e760aa0811ee6c0322c2ea74b3b84`.

Combined C2 remains byte-identical:
`58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.

Physical audit: PASS.
- changed ZIP CRC PASS;
- parent entry metadata mismatch 0;
- duplicate path 0;
- unsafe path 0;
- symlink 0;
- encrypted 0.

## 9. CROSS-SESSION RECOVERY CONTRACT

Recovery index local durable artifacts:
- `P07_EXPERIMENT_RECOVERY_INDEX_R1_20260910.json`;
- `P07_EXPERIMENT_RECOVERY_INDEX_R1_20260910.md`.

Completed experiments must be recoverable through this minimum chain:
Preregistration -> Frozen Inputs -> Control/Seal -> Selector/Profile Freeze -> Treatment/Integrity -> Provider/Runtime Receipts if claimed -> Blind Map Hash -> Blind Scores -> Unblind Map -> Final Result -> Post Regression -> Package Impact -> Changed Physical Packages.

Transient scratch scripts, temporary split files and `/tmp` working material are not authority and may be absent by design. Completed-result authority must not depend on those transient files.

## 10. FIXED GOVERNANCE STATE

- Active Development Engine: `P07-I4H Recovery R3`;
- Production: `ENG:R47`;
- DB Authority: DB59 frozen;
- Formal scored count: `137`;
- latest formal authority: `R138`;
- Formal R140: `0/0/0`;
- actual OpenAI Live confirmation for Semantic Alignment candidate: pending;
- I4I R1: Primary FAIL +0.2833;
- I4I R2: Primary FAIL +0.1667.

No Production or active-engine promotion is implied.
