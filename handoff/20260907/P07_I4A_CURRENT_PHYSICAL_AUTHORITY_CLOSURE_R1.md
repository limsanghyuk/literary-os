# P07-I4A Current Physical Authority Closure R1

Date: 2026-09-07
Classification: DEVELOPMENT / PREFORMAL / PHYSICAL CLOSURE

## 1. Current authority
`CURRENT_PHYSICAL_AUTHORITY__P07_I4A_PROVIDER_SHADOW_PASS_SURFACE_REPAIR_HOLD_R1`

Parent authority:
`CURRENT_PHYSICAL_AUTHORITY__P07_I3_BROADCAST_BIDIRECTIONAL_LOOP_R1`

Formal scored count: 137 (unchanged)
R140 attempts/outputs/scores: 0/0/0 (unchanged, HARD BLOCK)
Live Provider evidence eligibility: FALSE

## 2. Split scientific result
### Provider operating track
`PASS__SHADOW_LIVE_PROVIDER_RESILIENCE_AND_FAIL_CLOSE`

Accepted engineering changes:
- canonical Live semantic provider construction uses `build_live_semantic_provider()`;
- factory wraps `OpenAIStructuredSemanticProvider` in bounded fail-closed `ResilientSemanticProvider`;
- default max attempts = 2;
- transient 429/500/503, incomplete, timeout/network and JSON decode/provider JSON failures may retry;
- HTTP 400 and non-transient failures do not retry;
- semantic requests include `X-Client-Request-Id`;
- per-attempt retry trace preserved;
- permanent 429 -> two attempts then ERROR/BLOCK;
- HTTP 400 -> one attempt only then BLOCK;
- returned-model mismatch -> trusted provider claim BLOCK;
- missing response-id -> fail closed / claim BLOCK;
- hierarchical planning failure -> State Commit path is not invoked.

Factory/resilience/fail-close tests: PASS.
Exact final materialized packaged C2 nonhistorical regression: **205/205 PASS, pytest exit code 0**.

### Literary surface track
`HOLD__SURFACE_REPAIR_NOT_HUMAN_COMPETITIVE_ENOUGH`

Internal calibrated blind baseline:
- Human 12 wins
- P07-I3 Candidate 0 wins
- Tie 0

Six-scene Literary Compression/Voice repair blind result:
- Human 5 wins
- Candidate Repaired 1 win
- Tie 0

Preregistered gates:
- Candidate wins >=1: PASS
- Candidate wins + ties >=3/6: FAIL (1/6)

Therefore:
`SURFACE_REPAIR_INSUFFICIENT__HOLD_FULL_EPISODE_RERENDER`

The six-scene intervention is preserved as research evidence only and is **not promoted** into the active engine policy. The P07-I3 50-scene / 35,442-character screenplay remains the current broadcast development surface reference.

## 3. Current canonical 5 Parts / 9 Packages
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`

1. CONTROL `LITERARY_OS_CURRENT_CONTROL_P07_I4A_PROVIDER_SHADOW_SURFACE_HOLD_R1.zip`
   SHA256 `3b44518b65dbd2aa5898973fbe05d4f9630b638a766813439eed0fa5284db3fe`
2. A `LITERARY_OS_CURRENT_PART_A_P07_I4A_PROVIDER_SHADOW_SURFACE_HOLD_R1.zip`
   SHA256 `e03b0d47c984bec1d2a915f3178091619cfb63c3f3340a5a797fbfdfb4130189`
3. B1 `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1.zip`
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. B2 `LITERARY_OS_CURRENT_PART_B2_P07_I4A_PROVIDER_SHADOW_SURFACE_HOLD_R1.zip`
   SHA256 `f599aca3f7008ff05a63e405f91147bca5e60e6e398cf413ea317d99487385cc`
5. C1 `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1.zip`
   SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. C2-A `LITERARY_OS_CURRENT_C2_BINARY_A_P07_I4A_PROVIDER_SHADOW_SURFACE_HOLD_R1.bin`
   SHA256 `df67f68786e9c4197b9c6524557e00da37cffa29cef52824a5b203ed415dbfc9`
7. C2-B `LITERARY_OS_CURRENT_C2_BINARY_B_P07_I4A_PROVIDER_SHADOW_SURFACE_HOLD_R1.bin`
   SHA256 `f9daabb01f25fa325add80d5a261a006ea76fd15e73ae4b0212e67f51d3bbe2d`
8. D1 `LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1.zip`
   SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. D2 `LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1.zip`
   SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Changed from P07-I3: CONTROL / A / B2 / C2-A / C2-B.
Whole-file byte-identical to P07-I3: B1 / C1 / D1 / D2.

## 4. C2 and Trust Roots
Current reconstructed C2:
- bytes `319431814`
- SHA256 `496d396096630bf36e3c273becc954a8710989df0896586a90ac4cae5ef6c9c7`
- C2-A || C2-B rejoin: PASS

Package Set SHA256:
`e0bb95184f6ca841e491ef287507d88c07385982af72db9a8df4c61cbdb3563d`

Manifest SHA256:
`b01483cf2fd3cbe17f92a3dc08d39d98457ecd85e6a6751020916eaf2274c358`

Trust Root file SHA256:
`6ad698bcf76482d21b93f976aeb68b25a21a1966398a44e1196853722c5b6fcf`

Trust Root material SHA256:
`f4d639c0f67dac90d904cd34f6f8b31fc0579d0c4d13910285a444a656e116c9`

## 5. Physical audit — PASS
- changed CONTROL/A/B2/C2 preserve all parent entries with 0 missing, 0 CRC/size/compression mismatch, 0 nested-ZIP byte mismatch;
- unchanged B1/C1/D1/D2 whole-file byte-identical;
- CRC PASS / duplicate path 0 / unsafe path 0;
- nested ZIP counts unchanged from parent where relevant: CONTROL 54 / A 60 / B2 46 / C2 155;
- I4A delta secret hits 0;
- C2-A||C2-B reconstruction PASS;
- Research Master SHA256 `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0` PASS;
- Narrative Engine Master SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649` PASS;
- DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9` PASS;
- exact final materialized packaged C2 nonhistorical regression: 205/205 PASS, exit code 0.

## 6. Preregistration / result lineage
Provider emulation/internal blind preregistration commit:
`f4b2cc2b1be99a7f7cf96b9250f2063e2a3a864e`

Surface repair preregistration commit:
`b64c6cbca95aa6b267db5c9a45231ce89855da95`

P07-I4A result commit:
`80d8027e918254ec774bcc2e9b0b6bb8d1abf8bf`

## 7. Claim boundary
This authority physically adopts the Provider Shadow Live resilience/fail-close engineering improvement. It does **not** promote the failed six-scene surface-repair intervention.

It does not establish:
- a real OpenAI Live call or trusted OpenAI Live receipt;
- human broadcast-writer craft equivalence;
- successful full-episode surface repair;
- RFV3 causal effect;
- CP1 Live, official R-F/R-G, Production promotion, or Formal R140.

## 8. Next order
Use these exact nine packages as the sole starting authority.

The next surface unit must redesign the `Scene Plan -> Surface Realization` intervention rather than relax the failed blind threshold. Priority targets: character-specific voice state, dialogue-information budgets, relationship-specific behavior, subtext/physicalization, and stronger scene-level literary compression.

A real OpenAI Live validation should use the newly adopted resilient provider factory when the developer executes it in the secure credential environment.

## CURRENT STATUS TOKEN
`CURRENT_PHYSICAL_AUTHORITY_P07_I4A_R1__5_PARTS_9_PACKAGES_SEALED__PROVIDER_SHADOW_PASS__SURFACE_REPAIR_HOLD__205_OF_205__NONLIVE__P07_ACTIVE_PREFORMAL__R140_HARD_BLOCK`
