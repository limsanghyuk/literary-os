# UL-16 Candidate Main-Path Integration Receipt R2

Date: 2026-09-16
Status: `MAIN_PATH_RESEARCH_INTEGRATION_PASS__CENSUS_PRIOR_CORRECTED__LEGACY_PATH_INVARIANT__PHYSICAL_AUTHORITY_UNCHANGED`
Supersedes for current research execution: `UL16_MAIN_PATH_INTEGRATION_RECEIPT_R1.md`

## 1. Why R2 exists

A consistency audit found a metadata/census discrepancy:
- R1/UL-14 text used `10,853` sequences;
- the stored A0 structural-representability result records `total_sequences = 11,213`;
- the 1,160 episode-plan sequence counts sum to 11,213;
- the reported mean `9.6663793103 * 1160` also resolves to 11,213.

Canonical correction:
`source_sequence_total = 11,213`.

This discrepancy did **not** indicate DB64 byte corruption and did not change the sequence/scene quantile priors used to allocate structure. It did affect the prior-profile metadata/hash, so the research runtime was rebuilt and re-regressed.

## 2. Corrected prior binding

DB64 R108 research-support SHA256:
`19f3c446a73408045d02d4d99e168251dca42da3bfa00abaff1d8f9159d7ea46`

Corrected census:
- works: 61
- episodes: 1,160
- sequence records: **11,213**
- scene cards: 73,639
- episode sequence P10/median/P90: 6 / 9 / 14
- episode scene P10/median/P90: 46 / 62 / 81.1
- sequence scene P10/median/P90: 3 / 7 / 10

Corrected UL-16 prior profile hash:
`f18c8d6224b23fbd00ad9d8883745945fcb1a0bfa375c829e4baef0fceb2d6ac`

## 3. Base runtime and mutation scope

Base runtime source ZIP SHA256:
`b3873e98d8f5df44aee22c388ac9b19bf61cbdafd5f9c09cda7f06952125da55`

Research mutation scope remains:
- `literary_os_runtime/canonical_authoring.py`
- `literary_os_runtime/adaptive_showrunner_ul16.py`

Legacy/Production algorithm remains routed separately as `LEGACY_R53`.
Research Candidate route remains `ADAPTIVE_UL16`.

## 4. R2 regression

After correcting the sequence total and recomputing the prior-profile hash, the complete UL-16 software/structural regression was rerun.

PASS:
- Legacy path;
- explicit adaptive path;
- broadcast structural depth;
- due/defer integrity;
- current-state derived obligation compiler;
- dynamic sequence count not fixed at 9;
- future-source leakage fail-closed;
- unknown mode fail-closed.

`all_boolean_pass = true`.

Python runtime compilation: **45/45 PASS**.

Legacy before/after regression remains exactly invariant:
- graph hash `f27df4468b4d2a8de1dfe50fdd6508a63dddd3d9dbb67d31eeb4428e39f9af6b`
- sequences 9
- scenes 20

## 5. R2 research package

Canonical current research package:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`

Size:
`18,681,762 bytes`

SHA256:
`7f71484cd2687262d18104b3a9a5cfe727d003d7ed4b616ce8d64702b2da2ca8`

ZIP CRC/integrity:
PASS.

R2 manifest SHA256:
`4cb83c8c1dba275c043fa7674d93405ab75f2936436063d34c8c118bce6f7abb`

R2 regression JSON SHA256:
`25a6f3041b93f843950c84a8982ed532837ce9a89e3ec06fe73ec2742a67e2f9`

Persistent Library canonical path:
`/Literary_OS/Physical_Archive/RESEARCH_UL16_20260916/LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`

A prematurely created different R2-sized artifact was preserved under:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_PREMATURE_UNVERIFIED_20260916.zip`

It is explicitly **not** current research authority.

## 6. Root-cause lesson

The census mismatch and duplicate-name incident reinforce R4:
- do not reuse a version name before its receipt is sealed;
- assign canonical status only after hash/CRC/regression closure;
- if an interrupted run has already emitted a same-name artifact, preserve it under an explicit `PREMATURE_UNVERIFIED` name and issue a new sealed receipt;
- never infer stable Library identifiers; use exact IDs returned by listing/tool results.

Mandatory execution protocol:
`handoff/20260916/RUNTIME_CONTAINER_HUB_ATOMIC_EXECUTION_PROTOCOL_R4.md`

## 7. Evidence boundary

R2 proves corrected software/structural Main-Path research integration only.

It does not prove:
- independent architecture quality;
- human-level planning;
- state carry/replan closure;
- live OpenAI Provider execution;
- full screenplay literary quality;
- Production promotion;
- a new physical SYNC authority.

## 8. Authority impact

None.

Unchanged:
- Physical baseline: SYNC-R53
- Production Engine: ENG:R47
- Candidate Base authority: P07-I4H Recovery R3
- Runtime DB: DB59 frozen
- DB64: research-support candidate only
- Formal total: 137; latest R138; R140 0/0/0

## STATUS TOKEN

`UL16_R2__CENSUS_CORRECTED_11213__PRIOR_HASH_F18C8D62__MAIN_PATH_RESEARCH_INTEGRATION_PASS__LEGACY_INVARIANT__PACKAGE_SHA_7F71484C__ARCHITECTURE_PROVIDER_PHYSICAL_PROMOTION_PENDING`
