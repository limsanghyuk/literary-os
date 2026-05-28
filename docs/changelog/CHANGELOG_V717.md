# CHANGELOG V717

**버전**: v12.3.1  
**날짜**: 2026-05-28  
**주제**: ZeroTrustTokenService — HMAC-SHA256 토큰 서비스 (ADR-178)

## 신규

- `literary_system/security/__init__.py` — security 패키지 초기화
- `literary_system/security/zero_trust_token.py` — ZeroTrustTokenService + TokenClaims + 예외 2종
- `tests/unit/test_v717_zero_trust_token.py` — 33 TC PASS
- `docs/adr/ADR-178.md`

## 변경

- `pyproject.toml` version → 12.3.1

## 테스트 현황

- V717 신규: 33 TC PASS
- 누적: 9,931 TC (V716 기준 9,898 + 33)
