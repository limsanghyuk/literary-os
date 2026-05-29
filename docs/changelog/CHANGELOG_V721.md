# CHANGELOG V721

**날짜**: 2026-05-29  
**버전**: v12.3.5  
**단계**: SP-D.3 Zero-Trust Security 통합

## 요약

PluginAuthAdapter 구현으로 security 패키지 ADR-128 고립 해소. plugins/ → security/ 단방향 연결 확립.

## 신규

| 파일 | 설명 |
|------|------|
| `literary_system/plugins/plugin_auth.py` | PluginAuthAdapter + PluginAuthResult + 예외 4종 + PERMISSION_ROLE_MAP |
| `tests/unit/test_v721_plugin_auth.py` | 33 TC PASS |
| `docs/adr/ADR-182.md` | 설계 결정 |

## 수정

| 파일 | 변경 내용 |
|------|-----------|
| `literary_system/plugins/__init__.py` | PluginAuthAdapter 등 8종 export 추가 |

## 주요 변경

- `security/` 패키지 고립 해소 (ADR-128 WARN → 0건)
- `PluginPermission → Zero-Trust role` 매핑 테이블 제정
