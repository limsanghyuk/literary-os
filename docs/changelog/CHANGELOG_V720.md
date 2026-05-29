# CHANGELOG V720

**Version**: 12.3.4
**Date**: 2026-05-28
**Phase**: SP-D.3 Zero-Trust Security — Tamper-Proof Audit Log

## Summary

V720 implements `ZeroTrustAuditLog`, an HMAC-SHA256 chained append-only audit log that records every ZeroTrust decision with tamper-evidence via chain hash verification.

## New Files

| File | Description |
|------|-------------|
| `literary_system/security/zero_trust_audit_log.py` | ZeroTrustAuditLog, AuditRecord |
| `tests/unit/test_v720_zero_trust_audit_log.py` | 33 unit tests |
| `docs/adr/ADR-181.md` | Design rationale |

## Modified Files

| File | Change |
|------|--------|
| `literary_system/security/__init__.py` | Added ZeroTrustAuditLog, AuditRecord exports |
| `pyproject.toml` | version 12.3.3 → 12.3.4 |

## Test Results

- V720 unit: **33/33 PASS**

## Gate Progress

G88 Zero-Trust Security: V717 ✅ V718 ✅ V719 ✅ V720 ✅ | V721 (Gate) next
