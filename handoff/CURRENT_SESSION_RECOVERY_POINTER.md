# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-07

Always read this file first when resuming Literary OS work in a new ChatGPT session, then read `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`.

## CURRENT LATEST PHYSICAL AUTHORITY CHECKPOINT — READ FIRST
`handoff/20260907/P07_I4A_CURRENT_PHYSICAL_AUTHORITY_CLOSURE_R1.md`
Commit: `173fe629201fb7eda5ba9a5a498ab1b8a8b25eda`

Provider emulation/internal blind preregistration commit:
`f4b2cc2b1be99a7f7cf96b9250f2063e2a3a864e`

Surface repair preregistration commit:
`b64c6cbca95aa6b267db5c9a45231ce89855da95`

P07-I4A result commit:
`80d8027e918254ec774bcc2e9b0b6bb8d1abf8bf`

Previous physical authority checkpoint:
`handoff/20260907/P07_I3_CURRENT_PHYSICAL_AUTHORITY_CLOSURE_R1.md`
Commit: `1725b27ae2370d06ffe7b7edac52dba759b30b77`

## CURRENT SCIENTIFIC / PACKAGE STATE
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores — HARD BLOCK
- ENG:R47 Production: immutable
- P06: COMPLETED / PHYSICALLY CLOSED
- P07: ACTIVE PREFORMAL / NOT COMPLETE
- Current physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4A_PROVIDER_SHADOW_PASS_SURFACE_REPAIR_HOLD_R1`
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- DB64 remains separate Living DB and MUST NOT silently replace DB59
- RFV3 outputs: 0
- CP1 current-authority restoration: OPEN
- Real OpenAI Live evidence eligibility: FALSE for I4A shadow-provider work

## P07-I4A SPLIT RESULT
### Provider operating track
`PASS__SHADOW_LIVE_PROVIDER_RESILIENCE_AND_FAIL_CLOSE`
- canonical live semantic provider construction uses `build_live_semantic_provider()`;
- bounded fail-closed retry, default max attempts 2;
- transient 429/500/503, incomplete, timeout/network and provider JSON failures may retry;
- HTTP 400/non-transient failures do not retry;
- `X-Client-Request-Id` and per-attempt trace preserved;
- permanent 429 -> two attempts then ERROR/BLOCK;
- model mismatch -> trusted provider claim BLOCK;
- missing response-id -> fail close;
- planning failure -> no State Commit;
- exact final materialized packaged C2 nonhistorical regression 205/205 PASS, pytest exit code 0.

### Literary surface track
`HOLD__SURFACE_REPAIR_NOT_HUMAN_COMPETITIVE_ENOUGH`
- calibrated blind baseline: Human 12 / Candidate 0 / Tie 0;
- six-scene compression/voice repair: Human 5 / Candidate 1 / Tie 0;
- preregistered Candidate wins+ties >=3/6 gate FAILED at 1/6;
- therefore `SURFACE_REPAIR_INSUFFICIENT__HOLD_FULL_EPISODE_RERENDER`;
- failed six-scene surface intervention is research evidence only and is NOT active engine policy.

## CURRENT 5 PARTS / 9 PACKAGES
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`

SHA256:
- CONTROL `3b44518b65dbd2aa5898973fbe05d4f9630b638a766813439eed0fa5284db3fe`
- A `e03b0d47c984bec1d2a915f3178091619cfb63c3f3340a5a797fbfdfb4130189`
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 `f599aca3f7008ff05a63e405f91147bca5e60e6e398cf413ea317d99487385cc`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `df67f68786e9c4197b9c6524557e00da37cffa29cef52824a5b203ed415dbfc9`
- C2-B `f9daabb01f25fa325add80d5a261a006ea76fd15e73ae4b0212e67f51d3bbe2d`
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Changed from P07-I3: CONTROL / A / B2 / C2-A / C2-B.
Whole-file byte-identical to P07-I3: B1 / C1 / D1 / D2.

## TRUST ROOTS
- Package Set SHA256 `e0bb95184f6ca841e491ef287507d88c07385982af72db9a8df4c61cbdb3563d`
- Manifest SHA256 `b01483cf2fd3cbe17f92a3dc08d39d98457ecd85e6a6751020916eaf2274c358`
- Trust Root file SHA256 `6ad698bcf76482d21b93f976aeb68b25a21a1966398a44e1196853722c5b6fcf`
- Trust Root material SHA256 `f4d639c0f67dac90d904cd34f6f8b31fc0579d0c4d13910285a444a656e116c9`
- Current reconstructed C2 SHA256 `496d396096630bf36e3c273becc954a8710989df0896586a90ac4cae5ef6c9c7`

## CROSS-PACKAGE CONTRACTS — PASS
- Research Master SHA256 `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0`
- Narrative Engine Master SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`
- DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## NEXT MANDATORY ORDER
Use these exact nine P07-I4A packages as the sole starting authority.

Next surface unit: redesign the `Scene Plan -> Surface Realization` interface itself. Do not relax the failed blind threshold. Priority: character-specific voice state, dialogue-information budgets, relationship-specific behavior, subtext/physicalization, and stronger literary compression. Run a small causal/blind probe before any full 50-scene rerender.

## CURRENT STATUS TOKEN
`CURRENT_PHYSICAL_AUTHORITY_P07_I4A_R1__5_PARTS_9_PACKAGES_SEALED__PROVIDER_SHADOW_PASS__SURFACE_REPAIR_HOLD__205_OF_205__NONLIVE__P07_ACTIVE_PREFORMAL__R140_HARD_BLOCK`
