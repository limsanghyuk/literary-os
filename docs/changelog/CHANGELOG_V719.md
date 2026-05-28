# CHANGELOG V719

**Version**: 12.3.3
**Date**: 2026-05-28
**Phase**: SP-D.3 Zero-Trust Security — Request Interceptor

## Summary

V719 implements `ZeroTrustMiddleware`, the request-interceptor layer that combines `ZeroTrustTokenService` (V717) and `TenantAuthority` (V718) into a single fail-closed entry point for all authenticated service calls.

## New Files

| File | Description |
|------|-------------|
| `literary_system/security/zero_trust_middleware.py` | ZeroTrustMiddleware, ZTRequest, ZTResponse, ZeroTrustAuditEntry |
| `tests/unit/test_v719_zero_trust_middleware.py` | 33 unit tests |
| `docs/adr/ADR-180.md` | Design rationale |

## Modified Files

| File | Change |
|------|--------|
| `literary_system/security/__init__.py` | Added ZeroTrustMiddleware, ZTRequest, ZTResponse, ZeroTrustAuditEntry exports |
| `pyproject.toml` | version 12.3.2 → 12.3.3 |
| `tools/run_preflight.py` | Fixed timeout, added --skip-gate, --fast; Survival Matrix updated |

## Test Results

- V719 unit: **33/33 PASS**
- Cumulative: see regression run

## Gate Progress

- G88 Zero-Trust Security: V717 ✅ V718 ✅ V719 ✅ | V720 (AuditLog) → V721 (Gate) pending

## ADR

- ADR-180: ZeroTrustMiddleware Request Interceptor Design
