# R64 / SYNC-R62 Final Closure & Incident Seal R1

Date: 2026-09-20
Status: `FINAL_CLOSURE__R64_FAIL__SYNC_R62_PHYSICALIZED__R65_NEXT_NOT_STARTED`

## Final authority
- Physical authority: **SYNC-R62** (physical namespace; distinct from experiment R62)
- Parent: **SYNC-R61 Delivery R2**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Failed research evidence: **R62 + R63 + R64**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- R64: **CLOSED FAIL before external blind**
- R65: **NOT STARTED**

## Incident root cause and repair
The repeated operational error was not package corruption.

### Incident A — duplicate preregistration create
A GitHub create-file call returned HTTP 422 `sha wasn't supplied`.

Root cause:
the R64 preregistration path had already been created by an earlier backend/tool transaction whose completion was not fully reflected in the conversational state.

Repair:
- fetch the exact path before retrying;
- detect existing immutable preregistration;
- never overwrite/recreate it;
- adopt the existing Hub file as canonical.

### Incident B — hidden local progress
The local runtime already contained:
- frozen/near-frozen R64 implementation work;
- known-failure regression receipts;
- R58B regression;
- R63-fresh regression.

Root cause:
tool/session visibility lag after interrupted operations.

Repair:
- inspect Hub and local filesystem before repeating work;
- hash existing artifacts;
- continue only from the last verifiable checkpoint.

### Incident C — Control QA import failure
Loading the exact R58 single source file outside package context failed on relative import `.trace`.

Root cause:
test harness import topology, not Control corruption.

Repair:
load exact R58 from its full package-context runtime. Control source SHA remained exact:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

## R64 scientific closure
Frozen Treatment source:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

Fresh mechanical:
- Control 12/12 PASS
- Treatment 12/12 PASS
- Treatment ACCEPT 30 / ABSTAIN 18

Pre-blind safety failure:
`표면 마감` = surface finishing was falsely interpreted as deadline/time-pressure evidence.

Diagnosis:
`FIELD_TYPED_LEXICAL_EVIDENCE_IS_STILL_NOT_SENSE_DISAMBIGUATED_SEMANTICS`

External blind:
NOT RUN.

## Physical closure
Trust root:
`c9acf57e92663f03c3231b45601dcef622e6bc8ff9cd18876874eaa1bff18b68`

C2 logical:
`b7992b63dd9509637a8e544d2217d87506d6402b889e26879ebc1201d10778d4`

Active runtime:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

Audit:
- 9/9 transport hashes PASS
- ZIP CRC PASS
- duplicates/encrypted/unsafe paths = 0
- C2 reassembly PASS
- secret-pattern audit PASS
- OOM 0 / OOM-kill 0
- B2 inherited byte-identical and remains below 256 MiB attachment boundary

## Hub transaction
- R64 result commit: d5e0fa4cc2cf9589a92a5952b95211a14bb34556
- SYNC-R62 START HERE: c01c1bad04bf531e6db9fd66da2f38aebe195787
- SYNC-R62 receipt: e9742749815e2a05ae6630e348c2e4f52e25a049
- CURRENT_DEVELOPER_HUB_AUTHORITY: 9a9c0bcee6cb495ff9f0b5e60141af13562a7331
- CURRENT_NEXT_RESEARCH_POINTER: 74037334167d1d081a8696975c138e6a578a1cc4
- CURRENT_HANDOFF_POINTER: c13c36f748c576d18c8e6012285e12addc795189
- CURRENT_SESSION_RECOVERY_POINTER: e9f456c0dd0a14595d330684f01f93428bd9ad50

## Next
`R65 = F01 Sense-Disambiguated Semantic Predicate Gate`

No R65 preregistration, implementation or output is part of this seal.

Status token:
`R64_FINAL_CLOSURE__STATE_VISIBILITY_INCIDENT_REPAIRED__SYNC_R62_9_OF_9__ACTIVE_SYNC_R58__R65_NEXT_NOT_STARTED`
