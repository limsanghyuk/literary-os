# SYNC-R73 Recovery Precedence Guard R1

Date: 2026-09-25
Status: `ACTIVE__AUTHORITY_SHADOWING_GUARD`

## Purpose
Prevent recursive recovery logic from treating historical nested `CURRENT_*` documents as the current physical authority.

## Mandatory precedence
1. External `SYNC_R73_5PART_9PACKAGE_MANIFEST_R1.json`
2. External `SYNC_R73_TRUST_ROOT_R1.json`
3. External `00_READ_FIRST_SYNC_R73_20260925.md`
4. Top-level package `SYNC_R73_CURRENT_RECOVERY_20260925/01_CURRENT_AUTHORITY_R1.json`
5. Hub `CURRENT_HANDOFF_POINTER` / `CURRENT_SESSION_RECOVERY_POINTER`
6. Nested historical overlays and their embedded `CURRENT_*` documents

## Shadowing case
B2 contains `POST_SYNC_R72_FULL_RECOVERY_OVERLAY_R3.zip` (SHA256 `e215795bdcafacb20ed4ee91f009cbd24c87dc8ebb07c6664e86056d7c1bc72f`). Its embedded `CURRENT_*` documents correctly describe the pre-promotion SYNC-R72 snapshot and are provenance-only. The overlay itself declares `physical_authority_change=false`.

## Hard rule
A nested historical/recovery archive can never supersede the enclosing sealed authority merely because it contains files named `CURRENT_*`. If nested and top-level authority declarations disagree, the top-level SYNC-R73 Manifest/Trust Root/READ FIRST wins.

Historical evidence must not be rewritten or deleted to resolve this ambiguity.

## Current authority
- Physical: SYNC-R73
- Active Runtime: exact R69
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64-R131 research-only
- Operational Level-3: SUSPENDED__REQUALIFICATION_REQUIRED
- Formal latest scored: R138
- Formal R140: NOT_STARTED
- R77-H1: Generator Dispatch Ready / C-T not started / Human target unopened / primary outputs 0

No package mutation or physical reseal is required by this guard.
