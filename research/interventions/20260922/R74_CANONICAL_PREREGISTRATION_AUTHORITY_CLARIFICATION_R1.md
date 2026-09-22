# R74 Canonical Preregistration Authority Clarification R1

Date: 2026-09-22

## Problem
Two R74 preregistration artifacts coexist:

1. Earlier JSON variant
   - path: `R74_F05_SYMMETRIC_SEMANTIC_TRANSACTION_MEASUREMENT_BRIDGE_PREREGISTRATION_R1.json`
   - commit: `8f12a285884dc471e8f22773214470282acafc80`
   - created: 2026-09-22 13:27:47Z
   - sample concept: 17 R73 Stage-A Control-only / Treatment-naive cases

2. Later sealed canonical preregistration
   - path: `R74_F05_SYMMETRIC_SEMANTIC_TRANSACTION_MEASUREMENT_BRIDGE_PREREG_R1.md`
   - commit: `ec58f4b71e511f0e55c2cfbe1e1d0d751258c5ac`
   - created: 2026-09-22 13:32:57Z
   - SHA256: `8ae36a1a2c56b147bb76181b6b9f9a16e979977c3ec6d34fd74c0be7e61cf0dd`
   - explicitly sealed by `R74_PREREGISTRATION_SEAL_RECEIPT_R1.md` at 13:33:03Z
   - primary rule: exactly 24 fully fresh cases, >=12 works, max 2/work
   - the 17 R73 Control-only cases are bridge/metrology reserve only and cannot support the fully-fresh efficacy claim.

## Authority decision
The later SHA-sealed Markdown preregistration is the **canonical R74 scientific preregistration**.

Reason:
- it was created before any R74 Stage-M or primary scientific output;
- it was explicitly SHA-sealed;
- the subsequent shared representation contract and Stage-M execution cite that SHA.

The earlier JSON variant is retained as historical design history only and is **superseded for sample selection and efficacy gates**.

## Consequence
R74 primary efficacy may not use the 17 R73 Control-only cases as the primary sample.

Required primary:
- 24 fully fresh DB64 R127 episodes;
- exclude all R71 primary works;
- exclude all R72 R2/R3/R4/R5 primary cases;
- exclude all 41 R73 Stage-A HIGH cases;
- exclude all 24 R73 Stage-B cases;
- exclude SOURCE HOLD works;
- >=12 works;
- <=2 episodes/work;
- ledger sealed before any Treatment output.

This clarification changes no threshold and introduces no post-output sample selection because R74 primary outputs remain 0.
