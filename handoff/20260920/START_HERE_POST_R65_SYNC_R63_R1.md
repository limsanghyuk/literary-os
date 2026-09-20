# START HERE — POST-R65 SYNC-R63 PHYSICAL ALIGNMENT R1

Date: 2026-09-20
Status: `CANONICAL_HANDOFF__R65_FAIL_PHYSICALLY_ALIGNED__R66_NEXT_NOT_STARTED`

## Namespace note
**SYNC-R63 is a physical package-sequence identifier and is distinct from experiment R63.**

## Current authority
- Physical authority: **SYNC-R63**
- Parent physical authority: **SYNC-R62**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Failed research evidence: **R62 F01 + R63 F01 + R64 F01 + R65 F01**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- R65: **CLOSED FAIL — pre-blind selector-safety**
- R66: **NOT STARTED**

## R65 result
Canonical:
`research/interventions/20260920/R65_F01_SENSE_DISAMBIGUATED_RESULT_R1.md`

Result commit:
`b1bdd77a6fd9ffc4da9bc5cdb00f38b2c8f27713`

Diagnosis:
`TARGETED_SENSE_DISAMBIGUATION_IS_NOT_BOUNDARY_SAFE_SEMANTIC_PARSING`

Fresh failure:
the deadline cue `시한` was falsely found inside `표시한다`, licensing PRESSURE_ESCALATION for R65C06-E1.

External blind:
NOT RUN because the preregistered selector-safety gate failed.

## SYNC-R63 transport hashes
- CONTROL: `54a98d1d5cb41c0bd9eafed5c04134bc38060975a755a894361cb8df8736431a`
- A: `0cd590b9024a3ad63bd8a78a32f24b0e8a503df591bcabec796abeb5356e508f`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2: `35d2d47754ab5e8fc71b2220b49317e58e8fd3b899f66205f66e0b7c75793167`
- C1: `e27f7c85de726922bd2211bdbca88cad094919c8c3e702223029ce78e04a3a7b`
- C2-A: `6d49b64e6ca0c1ddefb22811a709efe6e147fd0aff4fbf99e093a57afdcc09e0`
- C2-B: `f1b80d8ad31c5af703520ed2d3df16746ac22ddf3d5300610f3ac19ac61ae641`
- D1: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

C2 logical:
- bytes: `376351229`
- SHA256: `979634720b06e931bb9bc8332a068500e754619762c97f3e1695c0f06f9738f3`

Trust root SHA256:
`94697514918cff9091132fb6adafeb75dadf195c4be5e6e2c51861d561ba3916`

## Active runtime
Exact SYNC-R58 remains active:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

R65 failed source is evidence only:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

## Audit
- 9/9 transport SHA PASS
- all ZIP CRC PASS
- duplicate/encrypted/unsafe entries = 0
- C2 reassembly PASS
- active runtime exact SYNC-R58 PASS
- R65 source/evidence preserved but non-active
- secret-pattern audit PASS
- B1/B2/D1/D2 byte-identical to SYNC-R62
- B2 margin below 256 MiB boundary: 148,859 bytes
- OOM 0 / OOM kill 0

## Next
`R66 = F01 Boundary-Safe Predicate Parser Gate`

R66 is NOT STARTED.

A fresh session must verify the SYNC-R63 trust root and transport hashes before R66.
