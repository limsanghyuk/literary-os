# P07-I4K-1 Event Candidate Generation Effect — Closure R1

Date: 2026-09-10
Classification: DEVELOPMENT / PREFORMAL / MASKED SAME-AGENT

Experiment: `P07-I4K-R1-EVENT-CANDIDATE-GENERATION-EFFECT`

Final decision: `PASS_TO_I4K2`.

Frozen parent:
- Physical authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R3__I4J_R1_CONTROL_SCALE_FLOOR_HOLD`
- Material SHA256: `7564dae4e61a15b5bfd57a7bb60745a4d3155c91711dc30ff105f799a95b312a`
- Active Engine: `P07-I4H Recovery R3`
- DB Authority: DB59 frozen

Generation:
- Control: 32 candidates, SHA256 `6046201372b3a9efd370a2d4765af5d2673d3f62ee54b3bee44ca6b65ce7b971`
- Treatment: 32 candidates, SHA256 `7001f5329497beca9bbbd8e78182f85565139f386c75dbee71aeee4f0e77a4ae`
- Treatment origin quota: 8 INTERNAL / 8 RELATIONSHIP / 8 SOCIAL_INSTITUTIONAL / 8 ENVIRONMENTAL_CHANCE
- Integrity issues before masking: 0

Masking and scoring:
- Secret map committed before scores, map SHA256 `eaae4eff0c233a70370259ef98cbb8bc1a1f930293641c000effac6dcc93627e`
- Masked 64-candidate packet SHA256 `e436acb1e6f66bb964ac612beda2b3e03e2a30e3a6010dfac3277dc845f81e39`
- Blind scores SHA256 `d97af420ec0b3346ad7b8e696433ab6a60c1824ab6a8e8d26ded4e4fa1ba1d48`
- Score seal occurred before unblind.

Results:
- Control all-7 mean: `7.799107142857142`
- Treatment all-7 mean: `8.53125`
- Treatment-Control all-7 delta: `+0.7321428571428577`
- Core-4 mean delta: `+0.90625`
- Ensemble + Future mean delta: `+0.6875`
- Coincidence/Convenience Safety delta: `+0.125`
- Treatment hard-gate-valid: `32/32`
- Every treatment origin group: `8/8` candidates with seven-axis mean >= 6.5
- H1 PASS / H2 PASS / H3 PASS / H4 PASS
- Hard gate violations: all 0

Post-experiment runtime regression:
- Historical preserved test: one expected historical FAIL under `tests/history_p07_pre09`
- Current nonhistorical suite: `258/258 PASS`

Evidence boundary:
- same-agent masked Development/Preformal only;
- masking is not independently provable;
- no OpenAI Live claim;
- no Active Engine, Production, DB, Formal count or R140 change;
- this single run qualifies only for I4K-2 Search Ablation, not engine promotion.

Closure ZIP SHA256: `638af2195e422ecb18352e360d12e1108fee91ee9f43bba1242da122443d01a4`.
