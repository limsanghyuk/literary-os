# CHANGELOG V712

**날짜**: 2026-05-28  
**버전 태그**: v12.2.0-V712 (베이스 12.2.0 유지)  
**SP**: SP-D.3 Plugin Registry  
**Gate**: G87 진행 중

---

## 변경 사항

### 신규 모듈

| 모듈 | 클래스/심볼 | 설명 |
|------|-------------|------|
| `literary_system/plugins/plugin_registry.py` | `PluginRegistry`, `RegistryEntry` | 중앙 플러그인 레지스트리 |

### 수정 모듈

| 모듈 | 변경 내용 |
|------|-----------|
| `literary_system/plugins/__init__.py` | `PluginRegistry`, `RegistryEntry` 익스포트 추가 |

### 신규 테스트

| 파일 | TC 수 | 결과 |
|------|-------|------|
| `tests/unit/test_v712_plugin_registry.py` | 33 | ✅ 33 PASS |

**테스트 클래스 구성:**
- `TestRegistryBasic` (TC01~08): 기본 등록/조회/해제
- `TestRegistryDuplicate` (TC09~14): 중복 등록 처리 (overwrite 옵션)
- `TestRegistryQuery` (TC15~22): 태그·권한·로드 상태 필터 조회
- `TestRegistryHooks` (TC23~28): on_register / on_unregister 훅 동작
- `TestRegistryIntegration` (TC29~33): auto_load + PluginLoader 통합

### 신규 문서

- `docs/adr/ADR-173.md`: PluginRegistry 설계 결정

---

## 누적 TC 현황

| 구간 | TC |
|------|----|
| V711 누적 | 9,733 |
| V712 신규 | +33 |
| **V712 누적** | **9,766** |

---

## 다음 버전 예고

**V713**: Plugin Whitelist + RestrictedPython 샌드박스 (D-M-03, ADR-174)
- `PluginSandbox`: RestrictedPython 기반 코드 실행 격리
- `PluginWhitelist`: 허용 모듈 목록 관리
- 예상 TC: +33
