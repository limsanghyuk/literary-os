# CHANGELOG V711 — SP-D.3 Plugin System 기반 (ADR-172)

**날짜**: 2026-05-28
**버전**: 12.2.1 (V711 개발 이터레이션)
**SP**: SP-D.3 Plugin Registry + Zero-Trust + Chaos

## 신규 모듈

| 모듈 | 위치 | 설명 |
|------|------|------|
| `PluginManifest` | `literary_system/plugins/plugin_manifest.py` | 불변 플러그인 메타데이터 선언 (frozen dataclass) |
| `PluginPermission` | 동상 | 6종 권한 Enum |
| `PluginStatus` | 동상 | 4종 수명 주기 상태 Enum |
| `PluginValidationError` | 동상 | 검증 실패 예외 |
| `PluginLoader` | `literary_system/plugins/plugin_loader.py` | 화이트리스트 기반 로더 |
| `PluginLoadResult` | 동상 | 로드 결과 데이터클래스 |

## 테스트

- `tests/unit/test_v711_plugin_manifest.py`: 33 TC PASS
- 누적 TC: 9,733+ (기준선 9,700 + 33)

## 다음 V712

- `PluginRegistry`: 등록/조회/검색 핵심 레지스트리
- `PluginDiscovery`: 디렉토리 기반 자동 탐색
- ADR-173
