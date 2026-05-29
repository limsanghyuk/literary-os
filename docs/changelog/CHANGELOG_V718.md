# CHANGELOG V718

**버전**: v12.3.2  
**날짜**: 2026-05-28  
**주제**: TenantAuthority — 테넌트 격리·권한 관리 (ADR-179)

## 신규

- `literary_system/security/tenant_authority.py`
- `tests/unit/test_v718_tenant_authority.py` — 33 TC PASS
- `docs/adr/ADR-179.md`

## 변경

- `literary_system/security/__init__.py` — TenantAuthority 등 6종 추가 export
- `pyproject.toml` version → 12.3.2

## 테스트 현황

- V718 신규: 33 TC PASS
- 누적: 9,964 TC
