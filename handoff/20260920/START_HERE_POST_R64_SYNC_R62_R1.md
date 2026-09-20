# START HERE — POST-R64 SYNC-R62 PHYSICAL ALIGNMENT R1

Date: 2026-09-20
Status: `CANONICAL_HANDOFF__R64_FAIL_PHYSICALLY_ALIGNED__R65_NEXT_NOT_STARTED`

## Namespace note
**SYNC-R62 is a physical package-sequence identifier and is distinct from experiment R62.**

## Current authority
- Physical authority: **SYNC-R62**
- Parent physical authority: **SYNC-R61 Delivery R2**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Failed research evidence: **R62 F01 + R63 F01 + R64 F01**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- R64: **CLOSED FAIL — pre-blind selector-safety**
- R65: **NOT STARTED**

## R64 result
Canonical:
`research/interventions/20260920/R64_F01_TYPED_SEMANTIC_ROLE_RESULT_R1.md`

Result commit:
`d5e0fa4cc2cf9589a92a5952b95211a14bb34556`

Diagnosis:
`FIELD_TYPED_LEXICAL_EVIDENCE_IS_STILL_NOT_SENSE_DISAMBIGUATED_SEMANTICS`

Fresh failure:
`표면 마감` (surface finishing) was falsely interpreted as deadline/time pressure and licensed PRESSURE_ESCALATION.

External blind:
NOT RUN, because the preregistered selector-safety gate failed.

## SYNC-R62 transport hashes
- CONTROL: `747a63b8c7e72f7abcaca10ccf1992ea6e91d6d08f6f2921e7ae42d4a7fd651e`
- A: `e89d07a0dec8bf89494d8c024d46b879dd137983057abd1d6edd00442a4e45b7`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2: `35d2d47754ab5e8fc71b2220b49317e58e8fd3b899f66205f66e0b7c75793167`
- C1: `8943991ee6ee3edb5f81c39069d4fcbfd061f75ed66eda0283bc4098ec742f9e`
- C2-A: `ec47f1c88bb7c5af774a990e3ba14aa5fc72629ddace82bab9631f729fcbc7c1`
- C2-B: `a55f4479ad12b2de3da5faeeee579d51441864a1ea68253c96ee5c66aa380ded`
- D1: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

C2 logical:
- bytes: `376195959`
- SHA256: `b7992b63dd9509637a8e544d2217d87506d6402b889e26879ebc1201d10778d4`

Trust root SHA256:
`c9acf57e92663f03c3231b45601dcef622e6bc8ff9cd18876874eaa1bff18b68`

## Active runtime
Exact SYNC-R58 remains active:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

R64 failed source is evidence only:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

## Audit
- 9/9 transport SHA PASS
- ZIP CRC PASS
- duplicate/encrypted/unsafe entries = 0
- C2 reassembly PASS
- active runtime exact SYNC-R58 PASS
- R64 source/evidence preserved but non-active
- secret-pattern audit PASS
- B1/B2/D1/D2 byte-identical to SYNC-R61 R2
- OOM 0 / OOM kill 0

## Next
`R65 = F01 Sense-Disambiguated Semantic Predicate Gate`

R65 is NOT STARTED.
