# P07-I4B Current Physical Authority Closure R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / PHYSICAL CLOSURE

## 1. Current authority
`CURRENT_PHYSICAL_AUTHORITY__P07_I4B_LITERARY_SURFACE_CONTRACT_R1`

Parent authority:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4A_PROVIDER_SHADOW_PASS_SURFACE_REPAIR_HOLD_R1`

Formal scored count: 137 (unchanged)
R140 attempts/outputs/scores: 0/0/0 (unchanged, HARD BLOCK)
Real OpenAI Live evidence eligibility: FALSE

## 2. Scientific result
P07-I4B redesigned the `SCENE_PLAN -> SURFACE_REALIZATION` interface using `LiterarySurfaceContractR1` rather than relaxing the failed I4A blind threshold.

Causal-adoption result:
- contract validation PASS for 8/8 frozen scenes;
- contract is physically present in renderer/provider literary payload;
- selected literary-field mutation changes provider-input literary payload hash;
- irrelevant metadata mutation leaves the consumed literary payload invariant;
- semantic-invariant mismatch fails closed;
- Python literary prose generation = 0.

Mechanical surface result:
- procedural/control vocabulary density: 20.93398 -> 8.49299 / 1,000 chars, drop 59.43%;
- mean non-empty line length: 56.611 -> 23.586 chars, drop 58.34%;
- unauthorized speakers = 0;
- critical semantic/continuity violations = 0.

Stage A blind result — Treatment vs exact P07-I3 control:
- Treatment 8 wins;
- Control 0 wins;
- Tie 0;
- preregistered gate PASS.

Stage B blind result — Treatment vs fresh DB59 human broadcast-script anchors:
- Human 4 wins;
- Candidate 2 wins;
- Tie 2;
- Candidate wins >=2 PASS;
- Candidate wins + ties >=4/8 PASS;
- verdict: `PASS__HUMAN_COMPETITIVE_DEVELOPMENT_SIGNAL`.

This is an internal single-judge development signal, not external human consensus.

## 3. Promoted engine policy
ADOPT:
- `LiterarySurfaceContractR1`;
- Scene Plan semantic-invariant binding;
- dialogue-information budget;
- character play state;
- relationship surface map;
- voice state;
- subtext/physicalization carrier contract;
- rhythm contract;
- surface firewall;
- bridge/renderer wiring that passes only consumed literary payload fields;
- fail-close on semantic-invariant mismatch.

NOT promoted:
- the exact eight treatment scene texts. They remain research evidence only and are not hardcoded policy.

NOT run in I4B:
- full 50-scene interface-driven whole-episode rerender. This is reserved for separately preregistered P07-I4C.

## 4. Exact packaged regression
Exact final packaged C2 fresh-materialization nonhistorical regression:
- 209/209 PASS;
- pytest exit code 0;
- regression log SHA256 `de4c0a120a4863ff20bbe8dfa062d28f5b0cdbfb99c0b75f83950809bf4bf68e`.

## 5. Current canonical 5 Parts / 9 Packages
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`

1. CONTROL `LITERARY_OS_CURRENT_CONTROL_P07_I4B_SURFACE_INTERFACE_R1.zip`
   SHA256 `358207e26e4a7ae60c04cfa6c4037f9219038eeeb2bbb4f81506919f4a8b2fa4`
2. A `LITERARY_OS_CURRENT_PART_A_P07_I4B_SURFACE_INTERFACE_R1.zip`
   SHA256 `43cc2adff0343cc2257bc9d25b963e5f048561b93d6668e557608db5eefdcf6e`
3. B1 `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1.zip`
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. B2 `LITERARY_OS_CURRENT_PART_B2_P07_I4B_SURFACE_INTERFACE_R1.zip`
   SHA256 `ed84d88619a1e29d3aa9e36e4e030675f21c89ba44280be91164282401cdb490`
5. C1 `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1.zip`
   SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. C2-A `LITERARY_OS_CURRENT_C2_BINARY_A_P07_I4B_SURFACE_INTERFACE_R1.bin`
   SHA256 `211988d224a5b258e2535a5b9768de54ad82b8606500b7f9c3dac5986913f0ca`
7. C2-B `LITERARY_OS_CURRENT_C2_BINARY_B_P07_I4B_SURFACE_INTERFACE_R1.bin`
   SHA256 `882b3d1da8c53672af94a3253616619c359623cc443bef3b1b1b00ae52e016ea`
8. D1 `LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1.zip`
   SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. D2 `LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1.zip`
   SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Changed from P07-I4A: CONTROL / A / B2 / C2-A / C2-B.
Whole-file byte-identical to P07-I4A: B1 / C1 / D1 / D2.

## 6. C2 and trust roots
Current reconstructed C2:
- bytes `319498857`;
- SHA256 `fd5e3d78b3e127a6c2a252d5a825b8355e88438a18cc386239e6ce006e91ebaa`;
- C2-A || C2-B rejoin PASS.

Package Set SHA256:
`3103c0448649a9d89294abc3e5ba3fde2bf9ac415ea5e8d69d530562e4fdcb2b`

Manifest SHA256:
`947bb6776126c3b493727be31ec4b07bd3efd3ee3e02f340aadd4d1f53e8ec69`

Trust Root file SHA256:
`1cb9890daff10e82825637f1412aaafbac1c108b6036ab9983c563e1f5ef02d3`

Trust Root material SHA256:
`e449f5f93c6cf74a2571bdde7bef83f1ac4c36197a533529566746966452be67`

## 7. Physical audit — PASS
- changed CONTROL/A/B2/C2 preserve every parent entry with 0 missing, 0 CRC/size/compression mismatch and 0 nested-ZIP byte mismatch;
- unchanged B1/C1/D1/D2 are whole-file byte-identical;
- CRC PASS / duplicate path 0 / unsafe path 0;
- nested ZIP counts: CONTROL 54 / A 60 / B2 46 / C2 155;
- I4B delta secret hits 0;
- C2-A||C2-B reconstruction PASS;
- Research Master SHA256 `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0` PASS;
- Narrative Engine Master SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649` PASS;
- DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9` PASS;
- post-sidecar copy audit: all nine package SHA values unchanged PASS.

## 8. Lineage
P07-I4B preregistration commit:
`c58313c9dbf4993d4ad98693afed1873d2a320b5`

P07-I4B result commit:
`9ed97571fad13fa2a106948c8bd6cebf239e9ff8`

## 9. Claim boundary
P07-I4B physically adopts the redesigned Scene Plan -> Surface Realization literary interface and establishes an internal human-competitive development signal on eight frozen scenes.

It does not establish:
- a real OpenAI Live call or trusted OpenAI Live receipt;
- external human consensus or human-writer equivalence;
- full 50-scene interface-driven rerender success;
- RFV3 causal effect;
- CP1 Live, official R-F/R-G, Production promotion, or Formal R140 qualification.

## 10. Next order
Use these exact nine packages as the sole starting authority.

Next unit: separately preregister P07-I4C 50-scene interface-driven whole-episode rerender under the adopted `LiterarySurfaceContractR1`. Preserve the P07-I4B Stage A/B thresholds and re-check broadcast scale, craft/continuity/ecology/thread diagnostics, responsible-ancestor routing, and State Commit/Carry before any Live-provider or downstream formal work.

## CURRENT STATUS TOKEN
`CURRENT_PHYSICAL_AUTHORITY_P07_I4B_R1__5_PARTS_9_PACKAGES_SEALED__LITERARY_SURFACE_CONTRACT_CAUSAL_ADOPTION_PASS__STAGE_A_8_OF_8__STAGE_B_HUMAN_4_CANDIDATE_2_TIE_2__209_OF_209__NONLIVE__P07_ACTIVE_PREFORMAL__R140_HARD_BLOCK`
