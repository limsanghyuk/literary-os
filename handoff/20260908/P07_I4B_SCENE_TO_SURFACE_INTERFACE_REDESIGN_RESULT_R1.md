# P07-I4B Scene Plan -> Surface Realization Interface Redesign — Result R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Parent authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4A_PROVIDER_SHADOW_PASS_SURFACE_REPAIR_HOLD_R1`
Parent Package Set SHA256: `e0bb95184f6ca841e491ef287507d88c07385982af72db9a8df4c61cbdb3563d`
Parent C2 SHA256: `496d396096630bf36e3c273becc954a8710989df0896586a90ac4cae5ef6c9c7`
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Preregistration commit: `c58313c9dbf4993d4ad98693afed1873d2a320b5`
Formal scored count: 137 (unchanged)
R140 attempts/outputs/scores: 0/0/0 (unchanged)

## 1. Result
`PASS__LITERARY_SURFACE_CONTRACT_CAUSAL_ADOPTION__STAGE_A_PASS__STAGE_B_HUMAN_COMPETITIVE_DEVELOPMENT_SIGNAL`

The intervention is not a prompt-only wording repair. A structured `LiterarySurfaceContractR1` was inserted between `SCENE_PLAN` and `SURFACE_REALIZATION` and wired into the semantic render bridge, episode packet wiring, and renderer/provider payload.

The eight treatment scene texts are evidence only. They are not hardcoded into the active engine policy. The promoted artifact is the interface contract + validation + bridge/wiring that caused the improvement.

## 2. Frozen sample
Exactly eight scenes were used: `S11, S14, S19, S21, S28, S33, S37, S50`.

Problem under test:
`INTERNAL_NARRATIVE_CONTROL_LOGIC_TO_SURFACE_EXPOSITION_LEAK`.

## 3. Causal adoption
- Contract validation: PASS.
- Contract physically reaches renderer/provider payload: PASS.
- Selected mutation of a consumed literary field changes literary provider-input hash: PASS.
- Irrelevant non-consumed metadata mutation leaves literary payload hash invariant: PASS.
- Semantic-invariant mismatch fails closed: PASS.
- Python literary prose generation: 0.

Working code SHA256:
- `literary_surface_contract.py` `79fa25b8aed55cf64eeecc2591c59ab1be199bddc9f6a2209a3ede57857a1ce5`
- `semantic_render_bridge.py` `c1627498a1128b7f57938593bc9f01c68de0412ee431a9b9b39a3eb0a8350551`
- `provider_backed_renderer.py` `bfa14133043bbcd386e6378c8cb3e471e4660537f708362283482009eeb0999b`
- `semantic_episode_render_wiring.py` `adf14f513110eb94a3fc621def9a1806cc16d9db388011ef4f058f12537a75c0`
- I4B interface test `d5fd91f892d3e80ce5ae744e17b1a6d25ece06931c5314edaae7d75b40bf7eb2`

## 4. Mechanical surface gates
Across the eight exact P07-I3 controls vs eight sealed treatments:
- control total chars: 8,073
- treatment total chars: 5,063
- procedural/control vocabulary density: 20.93398 -> 8.49299 per 1,000 chars (**59.43% reduction**, PASS)
- mean non-empty line length: 56.611 -> 23.586 (**58.34% reduction**, PASS)
- unauthorized direct speakers: 0
- critical semantic/continuity violations: 0
- decision: PASS

Evidence SHA256:
- contracts `6aa4115bc109b8bb06e18e2d1ffe624b6243bffb3670060795abffa387ccd10b`
- treatment scenes `6ee466b5949903d088c47575c338e604991e41f289de4e91424604df6170d231`
- mechanical metrics `955e3f035cad7a9c5d152cbedb592b7cc7130309bf31eb2abb2c119cb57973c9`

One pre-blind S33 draft attempted to add the shop owner as a direct speaker. This was detected by the frozen allowed-speaker mechanical gate before any blind packet was built. The draft was not scored. S33 was corrected to preserve the original speaker set; thresholds were not changed.

## 5. Stage A — Treatment vs exact P07-I3 control
Blind judgments were written before mapping reveal.

Result:
- Treatment wins: **8/8**
- Control wins: 0/8
- Ties: 0/8

Preregistered requirements:
- Treatment wins >=6/8: PASS
- Treatment losses <=2/8: PASS
- critical semantic/continuity violation = 0: PASS

Evidence:
- blind packet SHA256 `b8402cea19b718b2f8755b761f7e22e325d56961c5bb67fe0ec2f14d22433c8e`
- sealed mapping SHA256 `4b7efa2279d81ea399c7e19589deb3f2b866e9a8191adfc5b8d5e8a4076204b0`
- sealed judgments SHA256 `8884d92b3e3cf5d2d7cbf4479d3ad157528033a9a41802fff49743eeda196723`

## 6. Stage B — Treatment vs fresh human broadcast-script anchors
Human anchors were selected only after treatment sealing and Stage A PASS. Fresh masked passages were drawn from multiple DB59 works/functions and did not simply reuse the exact I4A six-pair set.

Blind judgments were written before mapping reveal.

Result:
- Human wins: **4/8**
- Candidate wins: **2/8**
- Ties: **2/8**

Preregistered human-competitive development signal required BOTH:
- Candidate wins >=2/8: **PASS**
- Candidate wins + ties >=4/8: **PASS (4/8)**

Candidate wins occurred in the time-pressure/multi-party scene and episode-exit-pressure scene; ties occurred in investigative evidence-ownership and internal power-conflict strata.

Evidence:
- masked human anchors SHA256 `3350f48e848134d180a0c2d22a44265f61e683de1e10f19f252d75e585e22a54`
- masked candidate SHA256 `a15483c5ee1571951fe231c6e6fe8c687b15bcd7c87db70a30c2218338b17154`
- blind packet SHA256 `d9b8812a0d70be9dd88896c6ff25c12ff09a1ebf5640068d3cc26208e8d6da62`
- sealed mapping SHA256 `3de4e267c9b9fac2327f4c5035bc5fda2ecf746b5c726af38b59c806115bc55b`
- sealed judgments SHA256 `888f3e1e0017acc7f0f489f5d4ced8ed6ae3bc5f7dc25b6544a8c96baf3b93cf`

This is the first internal human-competitive development signal after I4A's Human 12 / Candidate 0 baseline and the failed six-scene Human 5 / Candidate 1 repair. It is not external-human consensus.

## 7. Regression
The import-path interruption was not a semantic failure. `literary_os_runtime/__init__.py` existed; the initial pytest command omitted the materialized runtime root from Python import search path. Rerun with `PYTHONPATH=.` passed.

- I4B contract tests: 4/4 PASS
- renderer/bridge/backward-compat targeted regression: 32/32 PASS
- materialized runtime nonhistorical regression: **209/209 PASS, pytest exit code 0**
- working regression log SHA256 `4efea9283bfd9810d1a4923436124ea0c48f02b31ec1cec15f38b8dde1f3b42b`

## 8. Promotion decision
Promote:
- `LiterarySurfaceContractR1`
- contract validation/fail-close
- canonical consumed literary payload excluding non-consumed metadata
- semantic render bridge contract binding
- episode renderer packet propagation
- provider-backed renderer payload/instruction consumption

Do NOT promote:
- literal eight treatment scene texts as engine policy
- a claim that the whole 50-scene episode is repaired
- a claim of human-writer equivalence

The next whole-episode rerender must be a separately preregistered unit from the physically sealed I4B authority.

## 9. Claim boundary
P07-I4B establishes an internal, development-only causal interface improvement and a single-judge human-competitive signal on eight paired scenes. It does NOT establish real OpenAI Live evidence, external human consensus, whole-episode human equivalence, Production promotion, RFV3, CP1 Live, official R-F/R-G, or Formal R140.

## 10. Physical rule
Because the interface code is accepted, it must be propagated into the canonical 5 Parts / 9 Packages with thin-delta preservation of parent bytes, exact packaged-C2 fresh-extraction regression, CRC/duplicate/unsafe/nested/secret audits, cross-package reconstruction, Manifest and Trust Root before Current Authority promotion.
