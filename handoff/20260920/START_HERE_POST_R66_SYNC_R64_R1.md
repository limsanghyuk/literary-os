# START HERE — POST-R66 SYNC-R64 QUALIFIED-CANDIDATE PHYSICALIZATION R1

Date: 2026-09-20
Status: `CANONICAL_HANDOFF__R66_CLOSED_PASS__QUALIFIED_CANDIDATE_PHYSICALLY_ADOPTED__PRODUCTION_UNCHANGED`

## Namespace note
**SYNC-R64 is a physical package-sequence identifier and is distinct from experiment R64.**

## Current authority
- Physical authority: **SYNC-R64**
- Parent logical physical authority: **SYNC-R63**
- Active qualified Candidate: **R66 F01 Boundary-Safe Predicate Parser / ADAPTIVE_UL16 lineage**
- Qualified parent/fallback: **exact SYNC-R58 / ADAPTIVE_UL16**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- R66: **CLOSED PASS — external blind 12W / 0T / 0L**
- Next research: **NOT STARTED**

## R66 final qualification
Canonical result:
`research/interventions/20260920/R66_F01_BOUNDARY_SAFE_FINAL_RESULT_R1.md`

Result commit:
`8fa0b2bc36c978b7746abdf9144b7e3d919b60e5`

External blind:
- Treatment wins: 12/12
- ties: 0/12
- losses: 0/12
- mapped Treatment votes: 36/36
- confirmed Treatment critical violations under frozen 2-of-3 rule: 0

Claim boundary:
`F01_BOUNDARY_SAFE_PREDICATE_PARSER_GATE = QUALIFIED_AT_PLANNING/SCENE-CONTRACT_LEVEL`

This does NOT establish F04/F06/F07/F08 closure or Production promotion.

## Active qualified Candidate
R66 source SHA256:
`0558c910896556048bb6acf0e1d4097477c3c31a60d47f16c4bd83e3f6253f1d`

R66 integrated Candidate runtime SHA256:
`575fd5378c69d282c9b4c39d03e52d4cc436744fa67c792db8515fe91c384e75`

C1 `10_REQUIRED_PACKAGES/LITERARY_OS_RUNTIME_SOURCE_CURRENT.zip` now hashes exactly to that runtime.

## Qualified parent/fallback custody
Exact SYNC-R58 integrated runtime is also preserved separately in C1:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

SYNC-R58 overlay:
`d4215a8a5075054a054d5ca60e10e5992c4139588cccaeb0dabe14281f2fd633`

SYNC-R58 adaptive source:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

## SYNC-R64 exact package hashes
- CONTROL: `1ff66e7e62c8d8d1e6dc29e25d85447bdc95387e38de36f9d3474522453268f7`
- A: `d6cb32d0b12a164a4e7bf251d94d60e2b613da38784ab7163bcb12174ce52741`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 rebuilt recovery: `62c30bb4e28945deafc77fc18c888dc5e97527fe2f00a7536e250dce370fedba`
- C1: `1c33db2c2ba1116b72c34919c512433af234e6ea38a5e8d9c2c659e57cdea265`
- C2-A: `f9e2067d797ccfa2f1d22eae5757d7d7f53131a877bdf30f96091f3cb9c8dbe3`
- C2-B: `00e252d4912ed29df1d00f827b28341f68ae98a8327abf649e67f50cc4047863`
- D1: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

C2 logical:
- bytes: `414216598`
- SHA256: `0ddeaa58d43189f7805d014382f0b0b93e06a139673115d47ed980bfc4ff555b`
- entries: 3907
- CRC: PASS

Trust root SHA256:
`157d5ed7e6cebca9c2b8966b768447f9a4a9bd2f54498e339a19cb67fde88e92`

## B2 retention incident and resolution
During final SYNC-R64 audit, the local retained B2 copies for SYNC-R60 through SYNC-R63 were found truncated at different retained sizes. They do NOT match their historical sealed hash:
`35d2d47754ab5e8fc71b2220b49317e58e8fd3b899f66205f66e0b7c75793167`

The last locally byte-verified corrected B2 parent remains:
- SYNC-R59 corrected B2
- SHA256: `753db03b5c161d3c016ef95388f93e2dfe2c469d2e1eb6182429b3d16cd549e6`
- bytes: `268276811`

SYNC-R64 therefore does NOT claim byte-identical inheritance from the truncated local copies.
Instead, B2 was rebuilt from the verified SYNC-R59 corrected B2 payload plus an explicit current supersession/recovery notice.

New B2:
- bytes: `268278383`
- SHA256: `62c30bb4e28945deafc77fc18c888dc5e97527fe2f00a7536e250dce370fedba`
- ZIP CRC: PASS
- 256 MiB headroom: `157073` bytes

No guessed reconstruction of missing retained bytes was used.

## R66 evidence custody
External-blind final evidence ZIP:
`440e4105539e7daf53c5f48487b25090f0dbad92be4110f9e10b646139518b0c`

Raw uploaded judgments:
- J01: `33fbc3da74a79d2d32121e6bad8f9aa17d5f650e2ceb74c6703f5be42c369612`
- J02: `93962424ebe74008669f59c5e3f971e75cf5930d232df3e714ca1c68e3fa6b9b`
- J03: `84b64bb7bcbab0da3ee7d036c3a2f961f442f303e78ba04cc0f33964fb715587`

Aggregation JSON:
`d22ac68d634fd8ac187e9c4039a5e35cb51abbc741bb78f1fa5479472c62e055`

## Audit closure
- 9/9 transport SHA PASS
- all package ZIP CRC PASS
- duplicate entries 0
- encrypted entries 0
- unsafe paths 0
- C2 reassembly and CRC PASS
- R66 active runtime binding PASS
- exact SYNC-R58 qualified-parent runtime custody PASS
- R66 evidence custody PASS
- secret-pattern audit PASS, 0 live-looking findings
- DB59 transport parts unchanged
- OOM 0 / OOM-kill 0

## Next research
R61 causal map identified remaining supported/pending areas:
- F04 Semantic Repetition Validator Gap — SUPPORTED
- F06 Scene Necessity Declarative — SUPPORTED
- F07 State Carry runtime — CONTRACT_RESOLVED_RUNTIME_PENDING
- F08 Provider Context — CONTRIBUTOR
- F02/F05 — UNRESOLVED

No R67 target is started or preregistered by this handoff.
The next intervention target must be selected and preregistered separately.

Status token:
`SYNC_R64_PHYSICAL_AUTHORITY__R66_F01_QUALIFIED_CANDIDATE_ACTIVE__SYNC_R58_FALLBACK_PRESERVED__PRODUCTION_ENG_R47_UNCHANGED__NEXT_RESEARCH_NOT_STARTED`
