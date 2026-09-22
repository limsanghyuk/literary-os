# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-22

## CURRENT AUTHORITY
- Physical Authority: **SYNC-R72**
- Research Overlay: **POST-SYNC-R72 / R74 STAGE-M PASS / PRIMARY FREEZE HARNESS PASS / R72 EXCLUSION CUSTODY HOLD**
- Active Qualified Candidate: **R69/R68/R67/R66 lineage**
- Active Runtime: exact R69 — SHA256 `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- Production Engine: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 R127 research-only**
- Operational Level-3: **SUSPENDED / REQUALIFICATION REQUIRED**
- Formal R140: **NOT STARTED**

## RESEARCH STATUS
- R70: Provider validity PASS / formal literary quality HOLD.
- R71: F02 CLOSED PASS.
- R72 Research: F05 CLOSED FAIL.
- R73: diagnostic PASS; Stage-B efficacy invalidated by metric non-comparability; F05 NOT QUALIFIED.
- R74: Stage M PASS; primary efficacy NOT STARTED; Control outputs 0; Treatment outputs 0.

## R74 QUALIFIED COMPONENTS
### Symmetric Measurement Bridge
- canonical preregistration SHA256:
  `8ae36a1a2c56b147bb76181b6b9f9a16e979977c3ec6d34fd74c0be7e61cf0dd`
- shared contract SHA256:
  `f8bd7b9ad211d603861d47cd41986c3fc9242fc981b41c33f8e3c1bb5e988be1`
- qualified bridge: R3
- bridge SHA256:
  `a68f463177310d3857dd773811ba05400248e65436d686a81087184df1d4a6a7`
- Stage M: M1-M7 all PASS
- R68 F04 regression: 16/16 PASS
- R69 F06 regression: 16/16 PASS
- independent clean reexecution: PASS

### Primary Freeze Harness
- source:
  `research/interventions/20260922/r74_primary_materialize_freeze_r1.py`
- qualification:
  `research/interventions/20260922/R74_PRIMARY_FREEZE_HARNESS_QUALIFICATION_R1.md`
- GitHub Actions self-test: PASS
- deterministic 24-case selection: PASS
- >=12 works / max2-work constraints: PASS
- missing R72 revision custody -> fail-closed: PASS
- literary prose generation bytes: 0

## CURRENT HOLD
`HOLD__R72_R2_R3_R4_R5_CASE_ID_CUSTODY_INCOMPLETE__NO_PRIMARY_FREEZE`

Canonical audit:
`research/interventions/20260922/R74_PRIMARY_EXCLUSION_CUSTODY_AUDIT_R1.md`

Known:
- R2 selected 24 cases and had Treatment outputs; exact IDs missing.
- R3 selected fresh 24 cases; Control precheck 22/24; Treatment outputs 0; exact IDs missing.
- R4 selected fresh 24 cases; Control precheck 20/24; Treatment outputs 0; exact IDs missing.
- R5 completed fresh 24-case primary; ledger SHA256 `d4398a3568f55258fb664f782f5542431795ab471f944a5df168c5501478a364`; exact IDs missing from current custody.
- R73 41-case exclusion manifest is recovered and sealed.

Current local container/Python/Jupyter runtimes remain unavailable due TransportTimeoutError. GitHub Actions bypasses this only for repository-resident data. DB64 split custody remains present in conversation storage but is not repository-resident.

## NEXT
Recover exact R72 R2/R3/R4/R5 case IDs from physical C2 / historical local evidence when content access is restored -> build complete R72 exclusion manifest -> run qualified R74 primary freeze harness -> seal fully fresh 24-case ledger and selected DB64 bundle -> exact R69 Control vs unchanged F05 Treatment -> score symmetrically through R74 R3 -> apply P1-P11.

Do not weaken freshness or infer missing R72 case IDs.
Physical Authority remains SYNC-R72 until a successor 5-Part / 9-Package reseal is actually completed.
