# CHANGELOG — V715

**버전**: V715  
**날짜**: 2026-05-28  
**단계**: SP-D.3 Plugin Registry (G87)

---

## 요약

Plugin SDK 구현. 플러그인 개발자용 퍼블릭 API (BasePlugin + PluginContext)와
테스트 헬퍼(PluginTestHarness)를 제공한다.

---

## 신규 모듈

| 모듈 | 설명 |
|------|------|
| `literary_system/plugins/plugin_sdk.py` | BasePlugin ABC + PluginContext + PluginSDKError + MissingManifestError |
| `literary_system/plugins/plugin_test_harness.py` | PluginTestHarness — 격리 테스트 헬퍼 |

---

## 신규 ADR

- **ADR-176**: Plugin SDK 설계 결정

---

## 테스트

| 파일 | TC 수 | 결과 |
|------|-------|------|
| `tests/unit/test_v715_plugin_sdk.py` | 33 | ✅ 33/33 PASS |

누적 테스트 수: **9,865** (V714 9,832 + 33)

V711~V715 플러그인 전체: **165/165 PASS**

---

## 변경 파일

```
literary_system/plugins/plugin_sdk.py           [신규]
literary_system/plugins/plugin_test_harness.py  [신규]
literary_system/plugins/__init__.py             [업데이트]
tests/unit/test_v715_plugin_sdk.py              [신규]
docs/adr/ADR-176.md                             [신규]
docs/changelog/CHANGELOG_V715.md               [신규]
```
