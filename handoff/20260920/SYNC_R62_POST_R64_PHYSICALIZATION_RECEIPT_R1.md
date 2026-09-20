# SYNC-R62 Post-R64 Physicalization Receipt R1

Date: 2026-09-20
Status: `PASS__9_OF_9__R64_FAIL_PHYSICALLY_ALIGNED__R65_NOT_STARTED`

## Authority
- Physical authority: SYNC-R62
- Parent: SYNC-R61 Delivery R2
- Active qualified Candidate: exact SYNC-R58 / ADAPTIVE_UL16
- R64: CLOSED FAIL before blind
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64 research-only

## Trust
Trust root:
`c9acf57e92663f03c3231b45601dcef622e6bc8ff9cd18876874eaa1bff18b68`

C2 logical:
`b7992b63dd9509637a8e544d2217d87506d6402b889e26879ebc1201d10778d4`

Active runtime:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

R64 source evidence:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

R64 evidence ZIP:
`60f25fed4a0a05b68efa70268660388717f52b50ce3a5cbc8bbd8973fafc8649`

## Audit
- 9/9 transport SHA PASS
- modified ZIP CRC PASS
- duplicates/encrypted/unsafe paths = 0
- C2 reassembly PASS
- active runtime unchanged exact SYNC-R58
- R64 failed source preserved, non-active
- B1/B2/D1/D2 byte-identical to parent
- B2 remains 268,286,597 bytes, 148,859 bytes under 256 MiB
- OOM 0 / OOM kill 0

## R64 scientific boundary
R64 failed the preregistered selector-safety gate because `표면 마감` was interpreted as deadline/time pressure and licensed PRESSURE_ESCALATION.

Diagnosis:
`FIELD_TYPED_LEXICAL_EVIDENCE_IS_STILL_NOT_SENSE_DISAMBIGUATED_SEMANTICS`

External blind was not run.

Next:
`R65 = F01 Sense-Disambiguated Semantic Predicate Gate`
Status: NOT STARTED.
